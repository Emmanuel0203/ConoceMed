from typing import Tuple, List, Optional, Callable, Dict
from flask import current_app, flash
import os
import uuid
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from decimal import Decimal
from utils.geocode import geocode_with_variants
import threading


def build_payload_from_form(raw: dict) -> dict:
    """Normalize form data into the payload expected by the API."""
    datos = {}
    datos['nombre'] = raw.get('nombre', '').strip()
    datos['direccion'] = raw.get('direccion', '').strip()
    datos['descripcion'] = raw.get('descripcion', '').strip()
    if raw.get('fkidLocalidad'):
        datos['fkidLocalidad'] = raw.get('fkidLocalidad').strip()
    if raw.get('fkidCategoria_Turistica'):
        datos['fkidCategoria_Turistica'] = raw.get('fkidCategoria_Turistica').strip()

    def to_decimal(val):
        if val is None:
            return None
        v = str(val).strip()
        if v == '':
            return None
        try:
            return float(Decimal(v))
        except Exception:
            return None

    lat = to_decimal(raw.get('latitud'))
    if lat is not None:
        datos['latitud'] = lat
    lon = to_decimal(raw.get('longitud'))
    if lon is not None:
        datos['longitud'] = lon

    tarifa_val = to_decimal(raw.get('tarifa'))
    if tarifa_val is not None:
        datos['tarifa'] = tarifa_val

    if raw.get('estado'):
        datos['estado'] = raw.get('estado')

    # Optional location provenance and confidence (from client autocomplete or manual marker)
    if raw.get('location_source'):
        datos['location_source'] = raw.get('location_source')
    if raw.get('location_confidence'):
        try:
            datos['location_confidence'] = float(str(raw.get('location_confidence')).strip())
        except Exception:
            # ignore parse errors
            pass

    return datos


def validate_required_fks(datos: dict) -> Tuple[bool, Optional[str]]:
    if not datos.get('fkidLocalidad'):
        return False, 'Seleccione una localidad.'
    if not datos.get('fkidCategoria_Turistica'):
        return False, 'Seleccione una categoría.'
    return True, None


def apply_geocode(datos: dict, api_client_factory: Callable = None) -> Tuple[dict, Optional[str]]:
    """Attempt geocoding variants and fill datos with lat/lng and formatted address when available.
    Returns (geo_result, used_variant)
    """
    address = (datos.get('direccion') or '').strip()
    if not address:
        return None, None

    # If client supplied a high-confidence location (from Places Autocomplete or manual), skip server geocode
    try:
        threshold = float(current_app.config.get('LOCATION_CONFIDENCE_THRESHOLD', 0.8))
    except Exception:
        threshold = 0.8

    loc_src = (datos.get('location_source') or '').lower()
    loc_conf = datos.get('location_confidence')
    try:
        loc_conf = float(loc_conf) if loc_conf is not None else None
    except Exception:
        loc_conf = None

    if datos.get('latitud') is not None and datos.get('longitud') is not None and loc_src in ('client', 'manual') and loc_conf is not None and loc_conf >= threshold:
        current_app.logger.debug(f"controlAdmin.apply_geocode: skipping server geocode because client source={loc_src} confidence={loc_conf} >= {threshold}")
        return None, 'client-skip'

    geo, used = geocode_with_variants(address, fkidLocalidad=datos.get('fkidLocalidad'), api_client_factory=api_client_factory)
    current_app.logger.debug(f"controlAdmin.apply_geocode: geo={geo}, used={used}")
    if geo and geo.get('ok'):
        if geo.get('lat') is not None and geo.get('lng') is not None:
            datos['latitud'] = float(geo.get('lat'))
            datos['longitud'] = float(geo.get('lng'))
        if geo.get('formatted_address'):
            datos['direccion'] = geo.get('formatted_address')
        # annotate provenance
        datos['location_source'] = 'server'
        if geo.get('confidence') is not None:
            try:
                datos['location_confidence'] = float(geo.get('confidence'))
            except Exception:
                pass
        # Attempt to validate locality/city to avoid matches in other cities
        try:
            from utils.geocode import extract_locality_from_google, extract_locality_from_nominatim
            preferred_locality = None
            try:
                preferred_locality = current_app.config.get('DEFAULT_LOCALITY_NAME')
            except Exception:
                preferred_locality = None
            city_name = ''
            # Determine provider by inspecting raw
            raw = geo.get('raw')
            if isinstance(raw, dict) and raw.get('address_components'):
                city_name = extract_locality_from_google(raw)
            elif isinstance(raw, dict) and raw.get('display_name'):
                city_name = extract_locality_from_nominatim(raw)
            if city_name:
                datos['location_city'] = city_name
                if preferred_locality and (not datos.get('fkidLocalidad')):
                    try:
                        # Normalize both names (remove accents, case) before comparing.
                        # Previous logic flagged results when the detected city was NOT the preferred locality.
                        # The intended behavior (only "filter" / prompt when the detected city IS the preferred locality,
                        # e.g., only Medellín addresses) requires the opposite comparison.
                        import unicodedata
                        def _norm(s):
                            if s is None:
                                return ''
                            s2 = str(s)
                            s2 = unicodedata.normalize('NFKD', s2)
                            # remove diacritics
                            s2 = ''.join(ch for ch in s2 if not unicodedata.combining(ch))
                            return s2.lower().strip()

                        if _norm(city_name) == _norm(preferred_locality):
                            # mark as needing confirmation by user when the detected city MATCHES the preferred locality
                            datos['location_needs_confirmation'] = True
                    except Exception:
                        pass
        except Exception:
            # ignore locality extraction errors
            pass
    return geo, used


def allowed_file(fileobj: FileStorage) -> Tuple[bool, Optional[str]]:
    if not fileobj or not fileobj.filename:
        return False, 'Sin archivo'
    filename = fileobj.filename.lower()
    max_size = current_app.config.get('MAX_UPLOAD_SIZE_BYTES', 10 * 1024 * 1024)
    allowed_ext = ('.jpg', '.jpeg', '.png', '.gif', '.mp4', '.webm', '.avi', '.mp3', '.wav', '.ogg')
    if not any(filename.endswith(ext) for ext in allowed_ext):
        return False, 'Tipo de archivo no permitido'
    try:
        fileobj.stream.seek(0, os.SEEK_END)
        size = fileobj.stream.tell()
        fileobj.stream.seek(0)
        if size > max_size:
            return False, f'Archivo demasiado grande (max {max_size} bytes)'
    except Exception:
        pass
    return True, None


def save_and_register_files(archivos: List[FileStorage], fkidSitio: str, api_multimedia_client_factory: Callable):
    """Save uploaded files to disk and register them with the Multimedia API.
    api_multimedia_client_factory: callable that returns APIClient when called with 'Multimedia'
    """
    if not archivos:
        return []
    api_multimedia = api_multimedia_client_factory('Multimedia')
    upload_folder = current_app.config.get('UPLOAD_FOLDER') or os.path.join(current_app.root_path, 'static', 'media')
    os.makedirs(upload_folder, exist_ok=True)

    def determinar_tipo_multimedia(filename):
        try:
            extension = filename.rsplit('.', 1)[1].lower()
        except Exception:
            return 'desconocido'
        if extension in ['jpg', 'jpeg', 'png', 'gif']:
            return 'imagen'
        if extension in ['mp4', 'avi', 'mov', 'webm']:
            return 'video'
        return 'desconocido'

    results = []
    for archivo in archivos:
        if not archivo or not archivo.filename:
            continue
        ok, reason = allowed_file(archivo)
        if not ok:
            # Don't stop the entire operation; record the failure and continue
            current_app.logger.warning(f"save_and_register_files: archivo rechazado {getattr(archivo, 'filename', None)} reason={reason}")
            results.append({'filename': getattr(archivo, 'filename', None), 'success': False, 'error': reason})
            continue
        filename = f"{uuid.uuid4().hex}_{secure_filename(archivo.filename)}"
        file_path = os.path.join(upload_folder, filename)
        try:
            archivo.save(file_path)
            current_app.logger.info(f"Archivo guardado por controlAdmin: {file_path}")
        except Exception as e:
            current_app.logger.warning(f"No se pudo guardar archivo subido: {e}")
            results.append({'filename': getattr(archivo, 'filename', None), 'success': False, 'error': f'save_failed: {e}'})
            continue

        tipo = determinar_tipo_multimedia(filename)
        multimedia_data = {
            'idMultimedia': str(uuid.uuid4()),
            'url': f'/static/media/{filename}',
            'descripcion': 'Archivo subido (admin)',
            'tipo': tipo,
            'fkidSitio': fkidSitio
        }
        try:
            resp_m = api_multimedia.insert_data(json_data=multimedia_data)
            current_app.logger.info(f"Registro multimedia creado por controlAdmin: {resp_m}")
            # Normalize success determination: APIClient may return None on error or a dict with 'estado'
            if resp_m is None:
                results.append({'filename': filename, 'success': False, 'error': 'api_insert_returned_none'})
            elif isinstance(resp_m, dict) and resp_m.get('estado') and int(resp_m.get('estado')) == 200:
                results.append({'filename': filename, 'success': True, 'idMultimedia': resp_m.get('idMultimedia') or (resp_m.get('id') if isinstance(resp_m.get('id'), str) else None)})
            else:
                # API returned an unexpected payload
                results.append({'filename': filename, 'success': False, 'error': f'api_insert_unexpected_response: {resp_m}'})
        except Exception as ex:
            current_app.logger.warning(f"Fallo al registrar multimedia en API desde controlAdmin: {ex}")
            current_app.logger.exception(ex)
            results.append({'filename': filename, 'success': False, 'error': str(ex)})
    # end for
    return results


def save_and_register_files_background(archivos: List[FileStorage], fkidSitio: str, api_multimedia_client_factory: Callable):
    """Start a background thread that saves and registers files so the request can return faster.
    Returns True when the thread was started, False otherwise.
    """
    try:
        app = current_app._get_current_object()
    except Exception:
        # If no current_app (shouldn't happen when called from a view), fallback to synchronous
        try:
            save_and_register_files(archivos, fkidSitio, api_multimedia_client_factory)
            return False
        except Exception:
            return False

    def worker(a, fid, factory):
        try:
            with app.app_context():
                save_and_register_files(a, fid, factory)
        except Exception as e:
            app.logger.exception(f"Background save_and_register_files worker failed: {e}")

    try:
        t = threading.Thread(target=worker, args=(archivos, fkidSitio, api_multimedia_client_factory), daemon=True)
        t.start()
        current_app.logger.debug(f"controlAdmin: started background thread for {len(archivos)} files")
        return True
    except Exception as ex:
        current_app.logger.exception(f"controlAdmin: failed to start background worker: {ex}")
        return False
