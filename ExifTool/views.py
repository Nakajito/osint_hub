import os
import tempfile
import subprocess
import logging
import json
from django.shortcuts import render, redirect
from django.conf import settings
from django.urls import reverse
from django.contrib import messages

# Configuración básica
ALLOWED_CONTENT_TYPES = [
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/tiff",
    "video/mp4",
    "application/pdf",
]
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

logger = logging.getLogger(__name__)


def clean_metadata_for_session(metadata):
    """
    Limpia el diccionario de metadatos para evitar que la sesión de Django
    explote por tamaño excesivo. Elimina valores muy largos.
    """
    clean_data = {}
    if not isinstance(metadata, dict):
        return {}

    for k, v in metadata.items():
        # Convertir a string para verificar longitud
        str_val = str(v)
        # Si el valor tiene más de 500 caracteres, lo truncamos o ignoramos
        if len(str_val) > 500:
            clean_data[k] = str_val[:100] + "... (truncado por tamaño)"
        else:
            clean_data[k] = v
    return clean_data


def upload_file(request):
    """Mostrar formulario de subida y procesar el archivo para extraer metadatos."""
    if request.method == "POST":
        uploaded = request.FILES.get("file")
        keep = request.POST.get("keep_file") == "on"

        if not uploaded:
            messages.error(request, "No se envió ningún archivo.")
            return redirect(reverse("exiftool:upload"))

        if uploaded.size > MAX_FILE_SIZE:
            messages.error(
                request,
                f"El archivo excede el tamaño máximo permitido ({MAX_FILE_SIZE/1024/1024} MB).",
            )
            return redirect(reverse("exiftool:upload"))

        if uploaded.content_type not in ALLOWED_CONTENT_TYPES:
            messages.warning(
                request,
                "Tipo de archivo no recomendado; se intentará procesar de todos modos.",
            )

        # Guardar temporalmente usando chunks para no saturar RAM
        try:
            tmp_dir = tempfile.mkdtemp(prefix="exif_")
            tmp_path = os.path.join(tmp_dir, uploaded.name)

            with open(tmp_path, "wb+") as f:
                for chunk in uploaded.chunks():
                    f.write(chunk)
        except Exception as e:
            logger.error(f"Error escribiendo archivo temporal: {e}")
            messages.error(request, "Error interno al procesar el archivo.")
            return redirect(reverse("exiftool:upload"))

        metadata = {}

        # --- ESTRATEGIA 1: Piexif (Solo para JPEGs pequeños/medianos) ---
        # Si el archivo es muy grande (>10MB), saltamos piexif para evitar cargar todo en RAM python
        use_piexif = (
            uploaded.content_type == "image/jpeg" and uploaded.size < 10 * 1024 * 1024
        )

        if use_piexif:
            try:
                import piexif

                exif_dict = piexif.load(tmp_path)
                for ifd_name, ifd in exif_dict.items():
                    if ifd is None:
                        continue
                    for tag, val in ifd.items():
                        tag_info = piexif.TAGS.get(ifd_name, {}).get(tag, {})
                        tag_name = tag_info.get("name", str(tag))

                        if isinstance(val, bytes):
                            try:
                                v = val.decode("utf-8", errors="ignore")
                            except Exception:
                                v = "<datos binarios>"  # No guardar bytes crudos
                        else:
                            v = val
                        metadata[tag_name] = v
            except Exception as piexif_error:
                logger.debug(f"Piexif falló o se omitió: {piexif_error}")
                metadata = {}  # Reiniciar para intentar con ExifTool

        # --- ESTRATEGIA 2: ExifTool (Subprocess) ---
        if not metadata:
            try:
                # Buscar ExifTool
                import shutil

                exiftool_path = shutil.which("exiftool") or "/usr/bin/exiftool"

                # Verificar si realmente existe antes de ejecutar
                if not os.path.exists(exiftool_path):
                    logger.error(f"ExifTool no encontrado en: {exiftool_path}")
                    # Puedes lanzar una excepción o dejar que siga para mostrar el error

                # Comprobar si existe (opcional, subprocess lanzará FileNotFoundError si no)
                # Ejecutar exiftool optimizado
                # -j: JSON output
                # -q: Quiet
                # -n: No print conversion (valores numéricos reales para coordenadas)
                # -b-: IMPORTANTE -> NO extraer datos binarios (evita OOM)
                # -u: Extract unknown tags

                cmd = [exiftool_path, "-json", "-q", "-n", "-b-", "-u", tmp_path]

                logger.debug(f"Ejecutando: {' '.join(cmd)}")

                proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

                if proc.returncode == 0 and proc.stdout:
                    # --- AÑADE ESTA LÍNEA PARA VER EL RESULTADO REAL EN EL LOG ---
                    logger.info(f"JSON CRUDO EXIFTOOL: {proc.stdout}")

                    parsed = json.loads(proc.stdout)
                    if isinstance(parsed, list) and parsed:
                        metadata = parsed[0]
                        logger.info(
                            f"ExifTool extrajo {len(metadata)} tags de {uploaded.name}"
                        )
                else:
                    logger.warning(f"ExifTool stderr: {proc.stderr}")

            except FileNotFoundError:
                logger.error("ExifTool no está instalado en el servidor.")
            except subprocess.TimeoutExpired:
                logger.error("ExifTool timeout.")
            except json.JSONDecodeError:
                logger.error("Error decodificando JSON de ExifTool.")
            except Exception as e:
                logger.error(f"Error general ExifTool: {e}")

        # --- Limpieza y Lógica de Coordenadas ---

        # Eliminar archivo si no se pide guardar
        if not keep:
            try:
                os.remove(tmp_path)
                os.rmdir(tmp_dir)
            except Exception:
                pass

        if not metadata:
            messages.warning(request, "No se pudieron extraer metadatos.")
            return redirect(reverse("exiftool:upload"))

        # Procesar coordenadas (Logica simplificada gracias a flag -n de exiftool)
        map_url_target = None
        map_url_drone = None
        target_coords = None
        drone_coords = None
        drone_alt = None

        # Helper interno para flotantes seguros
        def safe_float(val):
            try:
                return float(val)
            except (ValueError, TypeError):
                return None

        # Drone Coords
        lat = safe_float(metadata.get("GPSLatitude")) or safe_float(
            metadata.get("Exif_GPSLatitude")
        )
        lon = safe_float(metadata.get("GPSLongitude")) or safe_float(
            metadata.get("Exif_GPSLongitude")
        )

        # Como usamos flag -n en ExifTool, los números ya vienen decimales (ej: 19.4326)
        # o a veces positivos necesitando referencia. Revisamos Refs por si acaso.
        lat_ref = str(metadata.get("GPSLatitudeRef", "")).upper()
        lon_ref = str(metadata.get("GPSLongitudeRef", "")).upper()

        if lat is not None and lon is not None:
            if lat_ref.startswith("S") and lat > 0:
                lat = -lat
            if lon_ref.startswith("W") and lon > 0:
                lon = -lon

            drone_coords = (lat, lon)
            map_url_drone = f"https://www.openstreetmap.org/?mlat={lat}&mlon={lon}#map=18/{lat}/{lon}"

        # Altitude
        drone_alt = safe_float(
            metadata.get("GPSAltitude") or metadata.get("Exif_GPSAltitude")
        )

        # Target Coords (DJI LRF)
        tlat = safe_float(
            metadata.get("LRFTargetLat") or metadata.get("LRFTargetLatitude")
        )
        tlon = safe_float(
            metadata.get("LRFTargetLon") or metadata.get("LRFTargetLongitude")
        )

        if tlat is not None and tlon is not None:
            target_coords = (tlat, tlon)
            map_url_target = f"https://www.openstreetmap.org/?mlat={tlat}&mlon={tlon}#map=18/{tlat}/{tlon}"

        def round_coord(val):
            try:
                return round(float(val), 5)
            except (TypeError, ValueError):
                return val

        # Aplicar redondeo a las tuplas si existen
        if target_coords:
            target_coords = (
                round_coord(target_coords[0]),
                round_coord(target_coords[1]),
            )

        if drone_coords:
            drone_coords = (round_coord(drone_coords[0]), round_coord(drone_coords[1]))

        if drone_alt:
            drone_alt = round(float(drone_alt), 2)  # Altitud a 2 decimales

        # --- GUARDAR EN SESIÓN (SANITIZADO) ---
        # IMPORTANTE: Limpiamos los datos antes de meterlos a la sesión
        clean_meta = clean_metadata_for_session(metadata)

        request.session["exif_metadata"] = clean_meta
        request.session["exif_filename"] = uploaded.name
        request.session["exif_map_target_url"] = map_url_target
        request.session["exif_map_drone_url"] = map_url_drone
        request.session["exif_target_coords"] = target_coords
        request.session["exif_drone_coords"] = drone_coords
        request.session["exif_drone_alt"] = drone_alt

        return redirect(reverse("exiftool:metadata"))

    return render(request, "exiftool/upload.html")


def show_metadata(request):
    """Mostrar metadatos almacenados en la sesión."""
    metadata = request.session.get("exif_metadata")
    filename = request.session.get("exif_filename", "-")
    map_url = request.session.get("exif_map_url")
    map_target = request.session.get("exif_map_target_url")
    map_drone = request.session.get("exif_map_drone_url")
    target_coords = request.session.get("exif_target_coords")
    drone_coords = request.session.get("exif_drone_coords")
    drone_alt = request.session.get("exif_drone_alt")
    # Opcional: limpiar sesión tras mostrar
    # del request.session["exif_metadata"]
    return render(
        request,
        "exiftool/metadata.html",
        {
            "metadata": metadata,
            "filename": filename,
            "map_url": map_url,
            "map_target": map_target,
            "map_drone": map_drone,
            "target_coords": target_coords,
            "drone_coords": drone_coords,
            "drone_alt": drone_alt,
        },
    )
