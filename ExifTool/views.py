import os
import tempfile
import shlex
import subprocess
import logging
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
                request, "El archivo excede el tamaño máximo permitido (10 MB)."
            )
            return redirect(reverse("exiftool:upload"))

        if uploaded.content_type not in ALLOWED_CONTENT_TYPES:
            messages.warning(
                request,
                "Tipo de archivo no recomendado; se intentará procesar de todos modos.",
            )

        # Guardar temporalmente
        tmp_dir = tempfile.mkdtemp(prefix="exif_")
        tmp_path = os.path.join(tmp_dir, uploaded.name)
        with open(tmp_path, "wb+") as f:
            for chunk in uploaded.chunks():
                f.write(chunk)

        # Intentar usar piexif para JPEG/EXIF (Python); si falla, fallback a exiftool subprocess
        metadata = {}
        try:
            import piexif

            exif_dict = piexif.load(tmp_path)
            # Convert piexif structure to a flat readable dict
            for ifd_name, ifd in exif_dict.items():
                if ifd is None:
                    continue
                for tag, val in ifd.items():
                    tag_info = piexif.TAGS.get(ifd_name, {}).get(tag, {})
                    tag_name = tag_info.get("name", str(tag))
                    # Decode bytes
                    if isinstance(val, bytes):
                        try:
                            v = val.decode("utf-8", errors="ignore")
                        except Exception:
                            v = str(val)
                    else:
                        v = val
                    metadata[tag_name] = v
        except Exception:
            # Fallback a subprocess exiftool si está disponible en el sistema
            try:
                cmd = f"exiftool -j {shlex.quote(tmp_path)}"
                proc = subprocess.run(
                    cmd, shell=True, capture_output=True, text=True, timeout=30
                )
                if proc.returncode == 0 and proc.stdout:
                    import json

                    parsed = json.loads(proc.stdout)
                    if isinstance(parsed, list) and parsed:
                        metadata = parsed[0]
                    else:
                        metadata = {}
                else:
                    metadata = {}
                    # Log stderr for debugging
                    logging.getLogger(__name__).warning(
                        "exiftool returned non-zero: %s", proc.stderr
                    )
            except Exception:
                metadata = {}

        # Si no se extrajeron metadatos, avisar al usuario con sugerencias
        if not metadata:
            # Log for debugging
            logging.getLogger(__name__).info(
                "No metadata extracted for file %s (content_type=%s)",
                uploaded.name,
                uploaded.content_type,
            )
            # User-facing message: more specific for JPEG vs others
            if uploaded.content_type == "image/jpeg":
                messages.warning(
                    request,
                    "No se encontraron metadatos EXIF. Asegúrate de que la imagen contiene EXIF o instala 'exiftool' en el servidor para una extracción más completa.",
                )
            else:
                messages.warning(
                    request,
                    "No se encontraron metadatos. Para formatos distintos a JPEG (PNG, PDF, vídeos) instala 'exiftool' en el sistema o sube un JPEG con EXIF.",
                )

        # Si el usuario no quiere guardar, borrar archivo
        if not keep:
            try:
                os.remove(tmp_path)
            except Exception:
                pass

        # Limpiar directorio temporal
        try:
            os.rmdir(tmp_dir)
        except Exception:
            pass

        # Preparar URLs de mapa si hay coordenadas (soporte para DJI)
        map_url_target = None
        map_url_drone = None
        target_coords = None
        drone_coords = None
        drone_alt = None

        def dms_to_decimal(dms_str):
            """Convert a DMS string like '18 deg 29' 56.56" N' to decimal degrees."""
            import re

            if not dms_str:
                return None

            # Handle piexif-style rational tuples: ((deg_num,deg_den),(min_num,min_den),(sec_num,sec_den))
            try:
                if isinstance(dms_str, (list, tuple)):
                    parts = list(dms_str)
                    # If nested rationals
                    if parts and isinstance(parts[0], (list, tuple)):

                        def rat_to_float(r):
                            try:
                                return float(r[0]) / float(r[1])
                            except Exception:
                                try:
                                    return float(r[0])
                                except Exception:
                                    return None

                        deg = rat_to_float(parts[0])
                        minutes = rat_to_float(parts[1]) if len(parts) > 1 else 0
                        seconds = rat_to_float(parts[2]) if len(parts) > 2 else 0
                        if deg is None:
                            return None
                        minutes = minutes or 0
                        seconds = seconds or 0
                        return deg + minutes / 60.0 + seconds / 3600.0

                    # If simple numeric tuple
                    try:
                        return float(parts[0])
                    except Exception:
                        pass
            except Exception:
                pass

            s = str(dms_str).strip()
            # Try to extract decimal directly
            try:
                return float(s)
            except Exception:
                pass

            # Regex to capture D M S and direction
            m = re.search(
                r"([0-9]{1,3})\D+([0-9]{1,3})\D+([0-9]{1,3}(?:\.[0-9]+)?)\D*([NnSsEeWw])",
                s,
            )
            if m:
                deg = float(m.group(1))
                minutes = float(m.group(2))
                seconds = float(m.group(3))
                dirc = m.group(4).upper()
                dec = deg + minutes / 60.0 + seconds / 3600.0
                if dirc in ("S", "W"):
                    dec = -dec
                return dec

            # Fallback: try to split by non-digit and parse first two numbers
            parts = re.findall(r"[-+]?[0-9]*\.?[0-9]+", s)
            if len(parts) >= 2:
                try:
                    deg = float(parts[0])
                    # If only one number, assume decimal
                    if len(parts) == 1:
                        return deg
                    # If two numbers and values look like D and M
                    if len(parts) >= 3:
                        minutes = float(parts[1])
                        seconds = float(parts[2])
                        dec = deg + minutes / 60.0 + seconds / 3600.0
                        return dec
                    else:
                        # two parts; interpret as decimal lat/lon
                        return float(parts[0])
                except Exception:
                    return None
            return None

        try:
            if isinstance(metadata, dict):
                # Target (LRF) - decimal values expected
                tlat = metadata.get("LRFTargetLat") or metadata.get("LRFTargetLatitude")
                tlon = metadata.get("LRFTargetLon") or metadata.get(
                    "LRFTargetLongitude"
                )
                if tlat is not None and tlon is not None:
                    try:
                        tlat_f = float(str(tlat))
                        tlon_f = float(str(tlon))
                        target_coords = (tlat_f, tlon_f)
                        map_url_target = f"https://www.openstreetmap.org/?mlat={tlat_f}&mlon={tlon_f}#map=18/{tlat_f}/{tlon_f}"
                    except Exception:
                        target_coords = None

                # Drone position - GPSLatitude/GPSLongitude (possibly DMS)
                g_lat = metadata.get("GPSLatitude") or metadata.get("Exif_GPSLatitude")
                g_lon = metadata.get("GPSLongitude") or metadata.get(
                    "Exif_GPSLongitude"
                )
                if g_lat and g_lon:
                    # Also check for latitude/longitude references (N/S, E/W)
                    lat_ref = metadata.get("GPSLatitudeRef") or metadata.get(
                        "Exif_GPSLatitudeRef"
                    )
                    lon_ref = metadata.get("GPSLongitudeRef") or metadata.get(
                        "Exif_GPSLongitudeRef"
                    )

                    lat_dec = dms_to_decimal(g_lat)
                    lon_dec = dms_to_decimal(g_lon)

                    # Apply sign from refs if available
                    try:
                        if lat_dec is not None and lat_ref:
                            lr = (
                                lat_ref.decode("utf-8")
                                if isinstance(lat_ref, (bytes, bytearray))
                                else str(lat_ref)
                            )
                            if lr.upper().startswith("S"):
                                lat_dec = -abs(lat_dec)
                        if lon_dec is not None and lon_ref:
                            rr = (
                                lon_ref.decode("utf-8")
                                if isinstance(lon_ref, (bytes, bytearray))
                                else str(lon_ref)
                            )
                            if rr.upper().startswith("W"):
                                lon_dec = -abs(lon_dec)
                    except Exception:
                        pass

                    if lat_dec is not None and lon_dec is not None:
                        drone_coords = (lat_dec, lon_dec)
                        map_url_drone = f"https://www.openstreetmap.org/?mlat={lat_dec}&mlon={lon_dec}#map=18/{lat_dec}/{lon_dec}"

                # Altitude
                g_alt = metadata.get("GPSAltitude") or metadata.get("Exif_GPSAltitude")
                if g_alt:
                    # GPSAltitude can be a rational tuple or a string; handle common cases
                    try:
                        # If piexif rational
                        if isinstance(g_alt, (list, tuple)):
                            # e.g., (2967, 10) -> 296.7
                            num = g_alt[0]
                            den = g_alt[1] if len(g_alt) > 1 else 1
                            drone_alt = float(num) / float(den) if den else None
                        else:
                            import re

                            parts = re.findall(r"[-+]?[0-9]*\.?[0-9]+", str(g_alt))
                            if parts:
                                drone_alt = float(parts[0])
                    except Exception:
                        drone_alt = None
        except Exception:
            pass

        # Redirigir a la vista de metadatos
        request.session["exif_metadata"] = metadata
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
