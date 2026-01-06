import os
import tempfile
import subprocess
import logging
import json
import re
import shutil
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
MAX_FILE_SIZE = 50 * 1024 * 1024

logger = logging.getLogger(__name__)


def clean_metadata_for_session(metadata):
    """Limpiar metadatos para la sesión."""
    clean_data = {}
    if not isinstance(metadata, dict):
        return {}
    for k, v in metadata.items():
        str_val = str(v)
        if len(str_val) > 500:
            clean_data[k] = str_val[:100] + "... (truncado)"
        else:
            clean_data[k] = v
    return clean_data


def parse_dms(dms_str):
    """
    Convierte cadenas DMS (ej: "21 deg 8' 34.30" N") a decimal (float).
    Soporta formatos numéricos simples también.
    """
    if not dms_str:
        return None

    # Si ya es un número (int o float), devolverlo directo
    if isinstance(dms_str, (int, float)):
        return float(dms_str)

    dms_str = str(dms_str).strip()

    # Intento 1: Es un número en string ("21.123")
    try:
        return float(dms_str)
    except ValueError:
        pass

    # Intento 2: Parsear formato "21 deg 8' 34.30" N"
    # Regex busca: (numero) deg (numero)' (numero)" (Letra)
    match = re.search(
        r'(\d+)\s*deg\s*(\d+)\'\s*([\d\.]+)"\s*([NSEW])', dms_str, re.IGNORECASE
    )
    if match:
        deg = float(match.group(1))
        mn = float(match.group(2))
        sec = float(match.group(3))
        direction = match.group(4).upper()

        decimal = deg + (mn / 60.0) + (sec / 3600.0)

        if direction in ["S", "W"]:
            decimal = -decimal

        return decimal

    return None


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
    if request.method == "POST":
        uploaded = request.FILES.get("file")
        keep = request.POST.get("keep_file") == "on"

        if not uploaded:
            messages.error(request, "No se envió ningún archivo.")
            return redirect(reverse("exiftool:upload"))

        if uploaded.size > MAX_FILE_SIZE:
            messages.error(request, "Archivo demasiado grande.")
            return redirect(reverse("exiftool:upload"))

        # Guardar temporalmente
        try:
            tmp_dir = tempfile.mkdtemp(prefix="exif_")
            tmp_path = os.path.join(tmp_dir, uploaded.name)
            with open(tmp_path, "wb+") as f:
                for chunk in uploaded.chunks():
                    f.write(chunk)
        except Exception as e:
            logger.error(f"Error archivo temporal: {e}")
            return redirect(reverse("exiftool:upload"))

        metadata = {}

        # --- EJECUCIÓN DE EXIFTOOL ---
        try:
            # Buscamos la ruta real
            exiftool_path = shutil.which("exiftool") or "/usr/bin/exiftool"

            # COMANDO ESTÁNDAR (El que te funcionó)
            cmd = [exiftool_path, "-json", tmp_path]

            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if proc.returncode == 0 and proc.stdout:
                try:
                    parsed = json.loads(proc.stdout)
                    if parsed:
                        metadata = parsed[0]
                except json.JSONDecodeError:
                    pass
        except Exception as e:
            logger.error(f"Error ExifTool: {e}")

        # Limpieza física
        if not keep:
            try:
                os.remove(tmp_path)
                os.rmdir(tmp_dir)
            except Exception:
                pass

        if not metadata:
            messages.warning(request, "No se encontraron metadatos.")
            return redirect(reverse("exiftool:upload"))

        # --- LÓGICA DE MAPAS (CORREGIDA) ---
        target_coords = None
        drone_coords = None
        map_url_drone = None
        map_url_target = None

        # 1. Coordenadas del Dron/Cámara (GPSLatitude / GPSLongitude)
        lat_raw = metadata.get("GPSLatitude")
        lon_raw = metadata.get("GPSLongitude")

        # Usamos la nueva función parse_dms
        lat = parse_dms(lat_raw)
        lon = parse_dms(lon_raw)

        if lat is not None and lon is not None:
            # Redondear para estética
            lat = round(lat, 6)
            lon = round(lon, 6)
            drone_coords = (lat, lon)
            map_url_drone = f"https://www.openstreetmap.org/?mlat={lat}&mlon={lon}#map=16/{lat}/{lon}"

        # 2. Coordenadas del Objetivo (LRF Target - Drones DJI Enterprise)
        tlat_raw = metadata.get("LRFTargetLat") or metadata.get("LRFTargetLatitude")
        tlon_raw = metadata.get("LRFTargetLon") or metadata.get("LRFTargetLongitude")

        tlat = parse_dms(tlat_raw)
        tlon = parse_dms(tlon_raw)

        if tlat is not None and tlon is not None:
            tlat = round(tlat, 6)
            tlon = round(tlon, 6)
            target_coords = (tlat, tlon)
            map_url_target = f"https://www.openstreetmap.org/?mlat={tlat}&mlon={tlon}#map=16/{tlat}/{tlon}"

        # Altitud
        alt_raw = metadata.get("GPSAltitude") or metadata.get("Exif_GPSAltitude")
        drone_alt = None
        if alt_raw:
            # Intentar limpiar string "3.8 m Below Sea Level" -> 3.8
            try:
                # Extraer solo la parte numérica inicial
                match_alt = re.match(r"([-+]?[\d\.]+)", str(alt_raw))
                if match_alt:
                    drone_alt = float(match_alt.group(1))
            except:
                pass

        # Guardar en sesión
        clean_meta = clean_metadata_for_session(metadata)
        request.session["exif_metadata"] = clean_meta
        request.session["exif_filename"] = uploaded.name
        request.session["exif_drone_coords"] = drone_coords
        request.session["exif_target_coords"] = target_coords
        request.session["exif_map_drone_url"] = map_url_drone
        request.session["exif_map_target_url"] = map_url_target
        request.session["exif_drone_alt"] = drone_alt

        return redirect(reverse("exiftool:metadata"))

    return render(request, "exiftool/upload.html")


def show_metadata(request):
    # Sin cambios en esta función
    metadata = request.session.get("exif_metadata")
    filename = request.session.get("exif_filename", "-")
    map_drone = request.session.get("exif_map_drone_url")
    map_target = request.session.get("exif_map_target_url")
    drone_coords = request.session.get("exif_drone_coords")
    target_coords = request.session.get("exif_target_coords")
    drone_alt = request.session.get("exif_drone_alt")

    return render(
        request,
        "exiftool/metadata.html",
        {
            "metadata": metadata,
            "filename": filename,
            "map_drone": map_drone,
            "map_target": map_target,
            "drone_coords": drone_coords,
            "target_coords": target_coords,
            "drone_alt": drone_alt,
        },
    )
