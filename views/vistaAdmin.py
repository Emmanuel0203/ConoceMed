from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app, session
from utils.api_client import APIClient
from utils.geocode import geocode, normalize_address, geocode_with_variants
from controllers.controlAdmin import build_payload_from_form, validate_required_fks, apply_geocode, save_and_register_files, save_and_register_files_background, allowed_file
import os
import urllib.parse
from werkzeug.utils import secure_filename
import uuid
from decimal import Decimal, InvalidOperation
from datetime import time
from flask import session
from werkzeug.datastructures import FileStorage
import mimetypes

vistaAdmin = Blueprint('vistaAdmin', __name__)


# geocoding normalization and variant attempts are provided by utils.geocode:
# - normalize_address(address)
# - geocode_with_variants(address, fkidLocalidad=None, api_client_factory=None)



@vistaAdmin.route('/admin', methods=['GET'])
def admin_panel():
    # Mostrar índice del panel de administración con enlaces a los dos paneles
    return render_template('panel.html')

@vistaAdmin.route('/admin/editar/<id>', methods=['GET', 'POST'])
def editar_lugar(id):
    # Normalizar id por si vino con '<' o '>' (errores de copia/pegar en URL)
    try:
        id = str(id).strip('<>')
    except Exception:
        pass
    api_lugares = APIClient("Sitios")
    if request.method == 'POST':
        # Factory to obtain APIClient instances for resources when needed
        api_client_factory = lambda resource: APIClient(resource)

        # Build payload from form
        datos = build_payload_from_form(request.form)

        # Validate required FK
        ok, message = validate_required_fks(datos)
        if not ok:
            flash(message, 'danger')
            return redirect(request.url)

        # Apply geocode using controlAdmin helper (this will prioritize localidad)
        try:
            geo, used_variant = apply_geocode(datos, api_client_factory=api_client_factory)
        except Exception:
            current_app.logger.exception('Error during geocoding in editar_lugar')
            geo, used_variant = None, None

        # send update to API using key-based route expected by EntidadesController
        try:
            resp = api_lugares.update_data_by_key('idSitio', id, json_data=datos)
            current_app.logger.debug(f"editar_lugar: respuesta update API: {resp}")
            if not resp:
                current_app.logger.warning(f"editar_lugar: update API devolvió None o error para id={id}")
                flash('Error en la API al actualizar sitio (ver logs).', 'danger')
                return redirect(request.url)
            # EntidadesController devuelve un objeto con 'estado' y 'filasAfectadas'
            estado = resp.get('estado') if isinstance(resp, dict) else None
            filas = resp.get('filasAfectadas', 0) if isinstance(resp, dict) else 0
            if estado != 200 and filas <= 0:
                current_app.logger.warning(f"editar_lugar: update no afectó filas ni devolvió estado 200: {resp}")
                flash('No se actualizó el sitio (no encontrado o sin cambios).', 'warning')
                # continue: still attempt to process files so user can add multimedia
        except Exception as e:
            current_app.logger.exception(e)
            flash('Error al actualizar sitio.', 'danger')
            return redirect(request.url)

        # Process uploaded files (multimedia)
        files = []
        try:
            # Template uses input name 'archivos' for uploads; ensure we read the same field
            files = request.files.getlist('archivos') if request.files else []
        except Exception:
            files = []

        try:
            # Process files in background to speed up the response
            if files:
                started = save_and_register_files_background(files, id, api_client_factory)
                if started:
                    current_app.logger.info(f'editar_lugar: multimedia registration started in background for sitio={id}')
                else:
                    # Fallback to synchronous if background start failed
                    results = save_and_register_files(files, id, api_client_factory)
                    failed = [r for r in results if not r.get('success')]
                    if failed:
                        current_app.logger.warning(f"editar_lugar: fallos al registrar multimedia (sync fallback): {failed}")
                        flash(f'Algunos archivos no pudieron registrarse: {len(failed)}. Revisa los logs.', 'warning')
        except Exception:
            current_app.logger.exception('Error processing files in editar_lugar')

        flash('Sitio actualizado correctamente.', 'success')
        # Redirigir según el estado del lugar: si Aprobado -> sitios_turisticos, si no -> lugares_sugeridos
        try:
            estado_lugar = datos.get('estado') or (lugar.get('estado') if isinstance(lugar, dict) else None)
        except Exception:
            estado_lugar = None
        try:
            if estado_lugar == 'Aprobado':
                return redirect(url_for('vistaAdmin.gestionar_sitios_turisticos'))
            else:
                return redirect(url_for('vistaAdmin.gestionar_lugares_sugeridos'))
        except Exception:
            # Fallback seguro
            return redirect(url_for('vistaAdmin.admin_panel'))
    try:
        # Obtener el lugar por su clave idSitio
        current_app.logger.debug(f"editar_lugar: solicitando idSitio={id}")
        lugar_response = api_lugares.get_data_by_key("idSitio", id)
        # Si el parámetro debug=1 está presente devolver las respuestas crudas
        if request.args.get('debug') == '1':
            api_localidades = APIClient("Localidad")
            localidades = api_localidades.get_data() or []
            api_categorias = APIClient("Categoria_Turistica")
            categorias = api_categorias.get_data() or []
            api_multimedia = APIClient('Multimedia')
            multimedia_resp = api_multimedia.get_data_by_key('fkidSitio', id)
            return {
                'lugar_response': lugar_response,
                'localidades': localidades,
                'categorias': categorias,
                'multimedia_resp': multimedia_resp
            }
        current_app.logger.debug(f"editar_lugar: respuesta get_data_by_key for id={id}: type={type(lugar_response)} content={str(lugar_response)[:800]}")
        lugar = None
        # Handle several shapes the API might return:
        # - {'tabla':..., 'datos':[ {...} ]}
        # - {'idSitio':..., 'nombre':...} (single object)
        # - [ {...}, ... ] (list)
        try:
            if lugar_response is None:
                lugar = None
            elif isinstance(lugar_response, dict):
                # Preferred shape: dict with 'datos' list
                if 'datos' in lugar_response and isinstance(lugar_response.get('datos'), list) and lugar_response.get('datos'):
                    lugar = lugar_response.get('datos')[0]
                else:
                    # Maybe the API returned a single entity as a dict
                    # Check for identifying keys
                    if any(k in lugar_response for k in ('idSitio', 'nombre')):
                        lugar = lugar_response
            elif isinstance(lugar_response, list) and len(lugar_response) > 0:
                lugar = lugar_response[0]
        except Exception as ex_proc:
            current_app.logger.exception(f"editar_lugar: error procesando lugar_response: {ex_proc}")
        # Fallback: si no se encontró el lugar por la consulta exacta, intentar buscar en la lista completa
        if not lugar:
            try:
                all_lugares = api_lugares.get_data() or []
                current_app.logger.debug(f"editar_lugar: tamaño all_lugares={len(all_lugares)}")
                for candidate in all_lugares:
                    # comparar contra varios nombres de clave que puedan contener el id
                    candidate_ids = [candidate.get('idSitio'), candidate.get('id'), candidate.get('idLugar_Sugerido')]
                    if any((str(cid) == str(id) for cid in candidate_ids if cid)):
                        lugar = candidate
                        current_app.logger.info(f"Fallback: sitio encontrado por búsqueda en lista para id={id} -> candidate id keys {candidate_ids}")
                        break
            except Exception as ex:
                current_app.logger.debug(f"Fallback search failed: {ex}")

        # Si después de los fallbacks no tenemos lugar, mostrar una página con candidatas para elegir
        if not lugar:
            try:
                candidates = api_lugares.get_data() or []
            except Exception:
                candidates = []
            return render_template('editar_no_encontrado.html', buscado_id=id, candidates=candidates[:50])
        # Obtener listas de Localidad y Categoria_Turistica para los selects
        api_localidades = APIClient("Localidad")
        try:
            localidades = api_localidades.get_data() or []
        except Exception:
            localidades = []

        api_categorias = APIClient("Categoria_Turistica")
        try:
            categorias = api_categorias.get_data() or []
        except Exception:
            categorias = []

        # Obtener multimedia asociada al sitio para permitir gestionarla desde el editor
        api_multimedia = APIClient('Multimedia')
        try:
            multimedia_resp = api_multimedia.get_data_by_key('fkidSitio', id)
            multimedia = multimedia_resp.get('datos', []) if multimedia_resp and isinstance(multimedia_resp, dict) else []
        except Exception:
            multimedia = []

        # Determinar URL de 'Cancelar' dinámicamente según el estado del lugar
        try:
            if lugar and isinstance(lugar, dict) and lugar.get('estado') == 'Aprobado':
                cancel_url = url_for('vistaAdmin.gestionar_sitios_turisticos')
            else:
                cancel_url = url_for('vistaAdmin.gestionar_lugares_sugeridos')
        except Exception:
            cancel_url = url_for('vistaAdmin.gestionar_lugares_sugeridos')

        return render_template('editar_lugar.html', lugar=lugar, localidades=localidades, categorias=categorias, multimedia=multimedia, cancel_url=cancel_url)  # Página de edición
    except Exception as e:
        current_app.logger.exception(f'Error al obtener los datos del lugar id={id}: {e}')
        flash(f'Error al obtener los datos del lugar: {str(e)}', 'danger')
        return redirect(url_for('vistaAdmin.gestionar_lugares_sugeridos'))

@vistaAdmin.route('/admin/crear', methods=['GET', 'POST'])
def crear_lugar():
    api_lugares = APIClient("Sitios")
    api_localidades = APIClient("Localidad")
    api_categorias = APIClient("Categoria_Turistica")

    # GET: renderizar la misma plantilla de edición pero sin 'lugar' para reutilizar UI
    if request.method == 'GET':
        try:
            localidades = api_localidades.get_data() or []
        except Exception:
            localidades = []
        try:
            categorias = api_categorias.get_data() or []
        except Exception:
            categorias = []
        # Renderizar plantilla específica para creación para evitar el mensaje "No se encontró"
        debug_flag = request.args.get('debug') == '1'
        return render_template('crear_lugar.html', localidades=localidades, categorias=categorias, debug=debug_flag)

    # POST: crear nuevo sitio en la API y asociar multimedia si existen archivos
    raw = request.form.to_dict()
    try:
        # Log incoming request file metadata for debugging uploads
        files_keys = list(request.files.keys()) if request.files else []
        archivos_count = len(request.files.getlist('archivos')) if request.files and 'archivos' in request.files else (len(request.files) if request.files else 0)
        current_app.logger.debug('crear_lugar: request.content_type=%s files_keys=%s archivos_count=%s', request.content_type, files_keys, archivos_count)
    except Exception:
        current_app.logger.exception('crear_lugar: fallo al inspeccionar request.files')
    # Use centralized payload builder to normalize inputs including location provenance
    datos = build_payload_from_form(request.form)

    # time fields: horario_apertura / horario_cierre (expect strings 'HH:MM' or 'HH:MM:SS')
    def normalize_time(val):
        if not val:
            return None
        v = str(val).strip()
        if v == '':
            return None
        parts = v.split(':')
        try:
            if len(parts) == 2:
                h = int(parts[0]); m = int(parts[1]); s = 0
            else:
                h = int(parts[0]); m = int(parts[1]); s = int(float(parts[2]))
            return f"{h:02d}:{m:02d}:{s:02d}"
        except Exception:
            return None

    ha = normalize_time(raw.get('horario_apertura'))
    if ha is not None:
        datos['horario_apertura'] = ha
    hc = normalize_time(raw.get('horario_cierre'))
    if hc is not None:
        datos['horario_cierre'] = hc

    # As this is created from admin, set approved status
    datos['estado'] = 'Aprobado'

    # Determine creator
    creado_por = None
    try:
        creado_por = session.get('user_id')
    except Exception:
        creado_por = None
    if not creado_por:
        creado_por = current_app.config.get('CURRENT_USER_ID') or current_app.config.get('ADMIN_USER_ID') or '618ebb2e-ddf4-4344-8a06-e58c26038b70'
    datos['creado_por'] = creado_por

    # Validate creator exists to avoid FK errors
    try:
        api_usuarios = APIClient('Usuario')
        usuario_resp = api_usuarios.get_data_by_key('idUsuario', creado_por)
        if not usuario_resp or not isinstance(usuario_resp, dict) or not usuario_resp.get('datos'):
            flash('El usuario creador no existe en la base de datos. Verifica tu sesión.', 'danger')
            return redirect(url_for('vistaAdmin.crear_lugar'))
    except Exception:
        current_app.logger.warning('No se pudo validar creado_por con la API (falló la comprobación).')

    # Attempt server-side geocoding using centralized helper (it will skip if client/manual confidence is high)
    geo = None
    used = None
    try:
        api_client_factory = lambda resource: APIClient(resource)
        geo, used = apply_geocode(datos, api_client_factory=api_client_factory)
        current_app.logger.debug(f"crear_lugar: resultado geocode helper: geo={geo}, used={used}")
        # If geocode returned a non-ok result, decide whether to treat as fatal
        if geo and not geo.get('ok'):
            raw_err = geo.get('error') or (geo.get('raw') or {}).get('error_message') or (geo.get('raw') or {}).get('status')
            if raw_err and isinstance(raw_err, str) and 'referer' in raw_err.lower():
                current_app.logger.warning('crear_lugar: Google geocoding referer-restricted; skipping server geocode')
            else:
                current_app.logger.warning(f"crear_lugar: geocoding falló: {geo}")
                flash('No se pudo geocodificar la dirección. Verifica la dirección e inténtalo de nuevo.', 'danger')
                return redirect(url_for('vistaAdmin.crear_lugar'))
        # If geo ok but low confidence, warn and ask manual correction
        if geo and geo.get('ok') and geo.get('confidence', 1) < 0.6:
            current_app.logger.info(f"crear_lugar: geocoding ambigüo (confidence={geo.get('confidence')}) para '{datos.get('direccion')}'")
            flash('La dirección parece ambigua. Ajusta la dirección o usa el mapa para mayor precisión.', 'warning')
            return redirect(url_for('vistaAdmin.crear_lugar'))
    except Exception:
        current_app.logger.exception('crear_lugar: error durante geocoding helper')
        # continue: we will still attempt to create the sitio using available datos

    # Insertar sitio en la API (si el geocode falló o no, la inserción debe ocurrir)
    current_app.logger.debug(f"crear_lugar: enviando datos a API: {datos}")
    # Sanitize payload for API: include only fields that the Sitios table expects
    allowed_keys = ['nombre', 'direccion', 'latitud', 'longitud', 'descripcion', 'horario_apertura', 'horario_cierre', 'tarifa', 'estado', 'fkidCategoria_Turistica', 'fkidLocalidad', 'creado_por']
    datos_api = {k: datos[k] for k in allowed_keys if k in datos}
    # Log payload at debug level when debug flag present (avoid writing to disk)
    try:
        if request.args.get('debug') == '1':
            current_app.logger.debug('crear_lugar DEBUG payload: %s', datos)
    except Exception:
        current_app.logger.exception('crear_lugar: fallo al loggear payload debug')

    # Additional structured logging for QA: capture key fields so logs are easy to scan
    try:
        current_app.logger.info('crear_lugar: crear nuevo sitio nombre=%s localidad=%s categoria=%s estado=%s creado_por=%s',
                                datos.get('nombre'), datos.get('fkidLocalidad'), datos.get('fkidCategoria_Turistica'), datos.get('estado'), datos.get('creado_por'))
        current_app.logger.debug('crear_lugar: coords (lat,long)=%s,%s provenance=%s confidence=%s',
                                 datos.get('latitud'), datos.get('longitud'), datos.get('location_source'), datos.get('location_confidence'))
    except Exception:
        current_app.logger.exception('crear_lugar: fallo al escribir logs adicionales')
    response = None
    try:
        response = api_lugares.insert_data(json_data=datos_api)
    except Exception:
        current_app.logger.exception('crear_lugar: fallo al insertar en API')
        response = None
    current_app.logger.debug(f"crear_lugar: respuesta inicial de insert: {response}")
    try:
        if isinstance(response, dict):
            current_app.logger.info('crear_lugar: API insert estado=%s mensaje=%s idSitio=%s', response.get('estado'), response.get('mensaje'), response.get('idSitio') or (response.get('datos') and response.get('datos')[0].get('idSitio')))
        else:
            current_app.logger.info('crear_lugar: API insert returned non-dict response type=%s', type(response))
    except Exception:
        current_app.logger.exception('crear_lugar: fallo al loggear respuesta insert')
    # Log API response at debug level when debug flag present (avoid writing to disk)
    try:
        if request.args.get('debug') == '1':
            current_app.logger.debug('crear_lugar DEBUG api insert response: %s', response)
    except Exception:
        current_app.logger.exception('crear_lugar: fallo al loggear api response debug')
    # If APIClient returned None in debug mode, log the direct requests.post result for inspection
    try:
        if request.args.get('debug') == '1' and response is None:
            try:
                import requests as _requests, os as _os
                api_url = (_os.getenv('API_URL') or '').rstrip('/') + '/Sitios'
                _hdr = {'Content-Type': 'application/json'}
                _j = datos
                _r = _requests.post(api_url, json=_j, headers=_hdr, timeout=10)
                current_app.logger.debug('crear_lugar DEBUG direct post status: %s, body: %s', getattr(_r, 'status_code', None), getattr(_r, 'text', None))
            except Exception:
                current_app.logger.exception('crear_lugar: fallo al hacer direct requests.post for debug')
    except Exception:
        current_app.logger.exception('crear_lugar: fallo en debug direct-post wrapper')

    # Determinar el id del nuevo sitio: preferir idSitio en la respuesta
    new_id = None
    if response and isinstance(response, dict):
        new_id = response.get('idSitio') or response.get('id')
        # a veces la API incluye 'datos' con la entidad creada
        if not new_id:
            datos_resp = response.get('datos', [])
            if datos_resp and isinstance(datos_resp, list):
                new_id = datos_resp[0].get('idSitio') or datos_resp[0].get('id')

    # Si no viene id, intentar buscar por nombre con retries cortos (GET-after-POST)
    if not new_id:
        nombre_buscar = (datos.get('nombre') or '').strip().lower()
        if nombre_buscar:
            import time as _time
            attempts = 3
            for attempt in range(1, attempts + 1):
                try:
                    current_app.logger.debug(f"crear_lugar: intento {attempt} de GET-after-POST buscando nombre='{nombre_buscar}'")
                    candidatos = api_lugares.get_data() or []
                    for cand in candidatos:
                        if (cand.get('nombre') or '').strip().lower() == nombre_buscar:
                            new_id = cand.get('idSitio') or cand.get('id')
                            current_app.logger.info(f"crear_lugar: encontrado new_id por nombre en intento {attempt}: {new_id}")
                            break
                    if new_id:
                        break
                except Exception as ex:
                    current_app.logger.warning(f"crear_lugar: fallo al listar candidatos en intento {attempt}: {ex}")
                _time.sleep(0.5)

    # Si tras intentar insertar y reintentar por nombre no obtuvimos un id, tratar como error y mostrar info útil
    if not new_id:
        current_app.logger.warning(f"crear_lugar: No se obtuvo id del sitio tras insert: response={response}")
        # Mejorar el mensaje para el usuario si la respuesta de la API contiene detalles
        api_msg = ''
        try:
            if isinstance(response, dict):
                api_msg = response.get('mensaje') or response.get('error') or str(response)
            else:
                api_msg = str(response)
        except Exception:
            api_msg = ''
        flash('No se pudo crear el lugar. Verifica que todos los campos obligatorios estén completos. ' + (f"(API: {api_msg})" if api_msg else ''), 'danger')
        return redirect(url_for('vistaAdmin.crear_lugar'))

    # Procesar archivos subidos igual que en actualizar_lugar
    archivos = []
    try:
        archivos = request.files.getlist('archivos') if request.files else []
    except Exception:
        archivos = []

    # Validar archivos antes de intentar guardarlos/insertarlos
    for f in archivos:
        ok, reason = allowed_file(f)
        if not ok:
            flash(f'Archivo rechazado: {reason}', 'danger')
            return redirect(url_for('vistaAdmin.crear_lugar'))

    # Procesar archivos subidos (si la API devolvió el id del nuevo sitio)
    if archivos and new_id:
        api_multimedia = APIClient('Multimedia')
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

        for archivo in archivos:
            if not archivo or not archivo.filename:
                continue
            filename = f"{uuid.uuid4().hex}_{secure_filename(archivo.filename)}"
            file_path = os.path.join(upload_folder, filename)
            try:
                archivo.save(file_path)
                current_app.logger.info(f"Archivo guardado en crear_lugar: {file_path}")
            except Exception as e:
                current_app.logger.warning(f"No se pudo guardar archivo subido en crear_lugar: {e}")
                continue

            tipo = determinar_tipo_multimedia(filename)
            multimedia_data = {
                'idMultimedia': str(uuid.uuid4()),
                'url': f'/static/media/{filename}',
                'descripcion': 'Archivo subido desde crear sitio (admin)',
                'tipo': tipo,
                'fkidSitio': new_id
            }
            try:
                resp_m = api_multimedia.insert_data(json_data=multimedia_data)
                current_app.logger.info(f"Registro multimedia creado en crear_lugar: {resp_m}")
                # Log summary for QA
                current_app.logger.debug('crear_lugar: multimedia registrado idMultimedia=%s fkidSitio=%s url=%s', multimedia_data.get('idMultimedia'), multimedia_data.get('fkidSitio'), multimedia_data.get('url'))
                if resp_m is None or (isinstance(resp_m, dict) and int(resp_m.get('estado', 0)) != 200):
                    current_app.logger.warning(f"crear_lugar: multimedia insert unexpected response: {resp_m}")
                    flash('Algunos archivos no se pudieron registrar en la API de multimedia. Revisa los logs.', 'warning')
            except Exception as ex:
                current_app.logger.warning(f"Fallo al registrar multimedia en API desde crear_lugar: {ex}")
                current_app.logger.exception('crear_lugar: excepción al insertar multimedia')
                flash('Error al registrar multimedia en la API. Revisa los logs.', 'danger')

    flash('Lugar creado correctamente.', 'success')
    # Si estamos en modo debug, renderizar la misma página de creación con la respuesta cruda para inspección
    debug_flag = request.args.get('debug') == '1'
    if debug_flag:
        try:
            localidades = api_localidades.get_data() or []
        except Exception:
            localidades = []
        try:
            categorias = api_categorias.get_data() or []
        except Exception:
            categorias = []
        api_resp = {
            'insert_response': response,
            'new_id': new_id
        }
        return render_template('crear_lugar.html', localidades=localidades, categorias=categorias, debug=True, api_response=api_resp)

    # Redirigir a la vista de sitios turísticos (solicitado por el usuario)
    return redirect(url_for('vistaAdmin.gestionar_sitios_turisticos'))

@vistaAdmin.route('/admin/actualizar/<id>', methods=['POST'])
def actualizar_lugar(id):
    try:
        id = str(id).strip('<>')
    except Exception:
        pass
    api_lugares = APIClient("Sitios")
    raw = request.form.to_dict()
    # Use centralized helpers to build and validate payload
    api_client_factory = lambda resource: APIClient(resource)
    datos = build_payload_from_form(request.form)

    # Validate required foreign keys
    ok, message = validate_required_fks(datos)
    if not ok:
        flash(message, 'danger')
        return redirect(request.referrer or url_for('vistaAdmin.gestionar_lugares_sugeridos'))

    # Try server-side geocode (non-fatal)
    try:
        geo, used = apply_geocode(datos, api_client_factory=api_client_factory)
        current_app.logger.debug(f"actualizar_lugar: geocode result={geo}, used={used}")
    except Exception:
        current_app.logger.exception('actualizar_lugar: error in geocoding')

    # Log key fields for QA
    try:
        current_app.logger.info('actualizar_lugar: id=%s nombre=%s fkidLocalidad=%s fkidCategoria=%s estado=%s', id, datos.get('nombre'), datos.get('fkidLocalidad'), datos.get('fkidCategoria_Turistica'), datos.get('estado'))
        current_app.logger.debug('actualizar_lugar: coords before update lat=%s long=%s provenance=%s confidence=%s', datos.get('latitud'), datos.get('longitud'), datos.get('location_source'), datos.get('location_confidence'))
    except Exception:
        current_app.logger.exception('actualizar_lugar: fallo al escribir logs adicionales')

    # Update via API
    try:
        # Sanitize payload for API update: only include fields expected by Sitios
        allowed_keys = ['nombre', 'direccion', 'latitud', 'longitud', 'descripcion', 'horario_apertura', 'horario_cierre', 'tarifa', 'estado', 'fkidCategoria_Turistica', 'fkidLocalidad']
        datos_api = {k: datos[k] for k in allowed_keys if k in datos}
        resp = api_lugares.update_data_by_key('idSitio', id, json_data=datos_api)
        current_app.logger.debug(f"actualizar_lugar: api update response={resp}")
        try:
            if isinstance(resp, dict):
                current_app.logger.info('actualizar_lugar: API update estado=%s filasAfectadas=%s', resp.get('estado'), resp.get('filasAfectadas'))
            else:
                current_app.logger.info('actualizar_lugar: API update returned non-dict type=%s', type(resp))
        except Exception:
            current_app.logger.exception('actualizar_lugar: fallo al loggear respuesta update')
        if not resp:
            flash('Error en la API al actualizar sitio (ver logs).', 'danger')
            return redirect(request.referrer or url_for('vistaAdmin.gestionar_lugares_sugeridos'))
    except Exception:
        current_app.logger.exception('actualizar_lugar: fallo al llamar a la API para actualizar')
        flash('Error al actualizar sitio.', 'danger')
        return redirect(request.referrer or url_for('vistaAdmin.gestionar_lugares_sugeridos'))

    # Process uploaded files (archivos/multimedia)
    files = []
    try:
        files = request.files.getlist('archivos') if request.files else []
    except Exception:
        files = []

    try:
        # Note: save_and_register_files expects the multimedia API client factory
        if files:
            started = save_and_register_files_background(files, id, api_client_factory)
            if started:
                current_app.logger.info(f'actualizar_lugar: multimedia registration started in background for sitio={id}')
            else:
                results = save_and_register_files(files, id, api_client_factory)
                failed = [r for r in results if not r.get('success')]
                if failed:
                    current_app.logger.warning(f"actualizar_lugar: fallos al registrar multimedia (sync fallback): {failed}")
                    flash(f'Algunos archivos no pudieron registrarse: {len(failed)}. Revisa los logs.', 'warning')
    except Exception:
        current_app.logger.exception('actualizar_lugar: error processing files')
        current_app.logger.warning('actualizar_lugar: archivos procesados count=%s', len(files) if files is not None else 0)

    # Decide redirect based on estado: if aprobado -> sitios_turisticos else lugares_sugeridos
    estado_lugar = datos.get('estado')
    try:
        if not estado_lugar:
            # try to fetch the updated record to know its estado
            rec = api_lugares.get_data_by_key('idSitio', id)
            if rec and isinstance(rec, dict):
                datos_list = rec.get('datos', [])
                if datos_list:
                    estado_lugar = datos_list[0].get('estado')
    except Exception:
        current_app.logger.exception('actualizar_lugar: error fetching updated record for redirect decision')

    if estado_lugar == 'Aprobado':
        return redirect(url_for('vistaAdmin.gestionar_sitios_turisticos'))
    return redirect(url_for('vistaAdmin.gestionar_lugares_sugeridos'))
    

@vistaAdmin.route('/admin/eliminar/<id>', methods=['POST'])
def eliminar_lugar(id):
    try:
        id = str(id).strip('<>')
    except Exception:
        pass
    api_lugares = APIClient("Sitios")
    api_multimedia = APIClient('Multimedia')
    try:
        current_app.logger.info('eliminar_lugar: iniciando proceso de eliminación para id=%s', id)

        # 1) listar multimedia asociada y eliminar archivos físicos + registros en la API
        try:
            multimedia_response = api_multimedia.get_data_by_key('fkidSitio', id)
            multimedia_list = multimedia_response.get('datos', []) if multimedia_response and isinstance(multimedia_response, dict) else []
        except Exception as ex:
            current_app.logger.warning('eliminar_lugar: no se pudo obtener multimedia para id=%s : %s', id, ex)
            multimedia_list = []

        current_app.logger.info('eliminar_lugar: multimedia_count=%s for sitio=%s', len(multimedia_list) if multimedia_list is not None else 0, id)
        for item in multimedia_list:
            try:
                url = item.get('url') or ''
                raw_path = urllib.parse.urlparse(url).path if url else ''
                filename = os.path.basename(raw_path) if raw_path else ''
                filename = urllib.parse.unquote(filename).lstrip('/\\')

                candidates = []
                upload_folder = current_app.config.get('UPLOAD_FOLDER') or os.path.join(current_app.root_path, 'static', 'media')
                if filename:
                    candidates.append(os.path.join(upload_folder, filename))
                    candidates.append(os.path.join(current_app.root_path, 'static', 'media', filename))
                    if raw_path and raw_path.lstrip('/\\') != filename:
                        candidates.append(os.path.join(current_app.root_path, raw_path.lstrip('/\\')))

                file_removed = False
                for p in candidates:
                    try:
                        p = os.path.normpath(p)
                        if os.path.exists(p):
                            os.remove(p)
                            current_app.logger.info('eliminar_lugar: archivo eliminado: %s', p)
                            file_removed = True
                            break
                        else:
                            current_app.logger.debug('eliminar_lugar: candidato no existe: %s', p)
                    except Exception as exf:
                        current_app.logger.warning('eliminar_lugar: error borrando archivo %s : %s', p, exf)

                if not file_removed:
                    current_app.logger.warning('eliminar_lugar: no se encontró archivo multimedia para item id=%s url=%s', item.get('idMultimedia'), url)

                # eliminar registro multimedia en la API
                try:
                    api_multimedia.delete_data(item.get('idMultimedia'))
                    current_app.logger.info('eliminar_lugar: registro multimedia eliminado id=%s', item.get('idMultimedia'))
                except Exception as exdm:
                    current_app.logger.warning('eliminar_lugar: fallo al eliminar registro multimedia id=%s : %s', item.get('idMultimedia'), exdm)
            except Exception as ex_item:
                current_app.logger.exception('eliminar_lugar: excepción al procesar multimedia item: %s', ex_item)

        # 2) finalmente eliminar el sitio
        current_app.logger.info('eliminar_lugar: solicitando delete Sitio id=%s', id)
        response = api_lugares.delete_data_by_key("idSitio", id)
        current_app.logger.debug('eliminar_lugar: respuesta delete API: %s', response)
        flash('Lugar eliminado correctamente (registros multimedia procesados).', 'success')
    except Exception as e:
        current_app.logger.exception('eliminar_lugar: fallo general al eliminar id=%s: %s', id, e)
        flash(f'Error al eliminar el lugar: {str(e)}', 'danger')
    return redirect(url_for('vistaAdmin.gestionar_sitios_turisticos'))

@vistaAdmin.route('/admin/aprobar/<id>', methods=['POST'])
def aprobar_lugar(id):
    try:
        id = str(id).strip('<>')
    except Exception:
        pass
    api_lugares = APIClient("Sitios")
    try:
        print(f"🔍 Intentando aprobar lugar con ID: {id}")

        # Actualizar el estado del lugar sugerido a "Aprobado"
        current_app.logger.debug(f"aprobar_lugar: actualizando id={id} a estado=Aprobado")
        update_response = api_lugares.update_data_by_key("idSitio", id, json_data={"estado": "Aprobado"})
        current_app.logger.info('aprobar_lugar: update_response=%s for id=%s', update_response, id)
        try:
            # extra logging to capture before/after
            sit_before = api_lugares.get_data_by_key('idSitio', id)
            current_app.logger.debug('aprobar_lugar: sitio before update: %s', sit_before)
        except Exception:
            current_app.logger.debug('aprobar_lugar: no se pudo obtener sitio antes del approve')
        if not update_response:
            flash(f"Error al actualizar el estado del lugar con ID: {id}", 'danger')
            return redirect(url_for('vistaAdmin.gestionar_lugares_sugeridos'))

        # Cuando el estado se actualiza, ya está en la tabla Sitios. No hay tabla separada "Sitio_Turistico".
        # Opcional: podríamos sincronizar otras tablas si aún existen en su API.

        # Transferir multimedia: si existiera multimedia en una tabla relacionada de sugeridos, se asume
        # que la API ya guarda multimedia con fkidSitio, así que no hay acción adicional requerida aquí.

        flash('Lugar aprobado y marcado como aprobado.', 'success')
    except Exception as e:
        current_app.logger.exception('aprobar_lugar: fallo al aprobar sitio id=%s', id)
        flash(f'Error al aprobar el lugar: {str(e)}', 'danger')
    return redirect(url_for('vistaAdmin.gestionar_lugares_sugeridos'))

@vistaAdmin.route('/admin/rechazar/<id>', methods=['POST'])
def rechazar_lugar(id):
    try:
        id = str(id).strip('<>')
    except Exception:
        pass
    api_lugares = APIClient("Sitios")
    api_multimedia = APIClient("Multimedia")
    try:
        # Antes de eliminar, listar contenido de la carpeta de uploads para debugging
        upload_folder = current_app.config.get('UPLOAD_FOLDER') or os.path.join(current_app.root_path, 'static', 'media')
        try:
            files_in_folder = os.listdir(upload_folder) if os.path.exists(upload_folder) else []
            current_app.logger.info(f"Contenido de UPLOAD_FOLDER ({upload_folder}): {files_in_folder}")
        except Exception as ex:
            current_app.logger.warning(f"No se pudo listar UPLOAD_FOLDER {upload_folder}: {ex}")

        # Eliminar multimedia asociada al sitio (si existe)
        multimedia_response = api_multimedia.get_data_by_key("fkidSitio", id)
        multimedia = multimedia_response.get("datos", []) if multimedia_response and isinstance(multimedia_response, dict) else []
        current_app.logger.info('rechazar_lugar: fkidSitio=%s multimedia_count=%s', id, len(multimedia) if multimedia is not None else 0)
        for item in multimedia:
            # también eliminar archivo físico si existe (primero el archivo, luego la fila en la API)
            try:
                url = item.get("url") or ""
                # obtener el nombre de archivo, decodificar y normalizar
                raw_path = urllib.parse.urlparse(url).path if url else ""
                filename = os.path.basename(raw_path)
                if filename:
                    filename = urllib.parse.unquote(filename).lstrip('/\\')

                    # Ruta preferida desde la configuración
                    upload_folder = current_app.config.get('UPLOAD_FOLDER')
                    candidates = []
                    if upload_folder:
                        candidates.append(os.path.join(upload_folder, filename))

                    # Fallback: path relativo dentro del proyecto (por ejemplo 'static/media/<file>')
                    candidates.append(os.path.join(current_app.root_path, 'static', 'media', filename))

                    # Fallback 2: si el stored path contenía subcarpetas (p.e. static/media/...), intentar unir con root
                    if raw_path and raw_path.lstrip('/\\') != filename:
                        candidates.append(os.path.join(current_app.root_path, raw_path.lstrip('/\\')))

                    removed = False
                    print(f"Intentando eliminar archivo asociado: {filename} (URL: {url})")
                    for file_path in candidates:
                        try:
                            file_path = os.path.normpath(file_path)
                            print(f"Comprobando existencia: {file_path}")
                            if os.path.exists(file_path):
                                os.remove(file_path)
                                print(f"Archivo eliminado: {file_path}")
                                current_app.logger.info(f"Archivo eliminado: {file_path}")
                                removed = True
                                break
                            else:
                                print(f"No existe: {file_path}")
                        except Exception as ex:
                            print(f"Error al eliminar {file_path}: {ex}")
                            current_app.logger.warning(f"No se pudo eliminar archivo {file_path}: {ex}")

                    if not removed:
                        current_app.logger.warning(f"Archivo no encontrado para eliminar: {filename} (URL: {url})")
            except Exception as ex:
                # no detener la operación principal por errores de archivo
                print(f"Error manejando archivo multimedia al rechazar: {ex}")
                current_app.logger.warning(f"Error manejando archivo multimedia al rechazar: {ex}")
                pass

            # eliminar por idMultimedia en la API (después de intento de borrado físico)
            try:
                current_app.logger.info('rechazar_lugar: eliminando registro multimedia id=%s', item.get('idMultimedia'))
                api_multimedia.delete_data(item.get("idMultimedia"))
                current_app.logger.info('rechazar_lugar: registro Multimedia eliminado id=%s', item.get('idMultimedia'))
            except Exception as ex:
                current_app.logger.warning(f"Fallo al eliminar registro Multimedia id={item.get('idMultimedia')}: {ex}")

        # Eliminar el lugar sugerido (registro en Sitios)
        lugar_response = api_lugares.delete_data_by_key("idSitio", id)
        if lugar_response:
            flash('Lugar rechazado y eliminado correctamente.', 'warning')
        else:
            flash('Error al eliminar el lugar sugerido.', 'danger')
    except Exception as e:
        flash(f'Error al rechazar y eliminar el lugar: {str(e)}', 'danger')
    return redirect(url_for('vistaAdmin.gestionar_lugares_sugeridos'))


@vistaAdmin.route('/admin/uploads', methods=['GET'])
def listar_uploads():
    # Endpoint temporal para QA: listar archivos en la carpeta de uploads
    upload_folder = current_app.config.get('UPLOAD_FOLDER') or os.path.join(current_app.root_path, 'static', 'media')

    # Protección simple: requerir token en query string que coincida con ADMIN_UPLOADS_TOKEN
    token_required = current_app.config.get('ADMIN_UPLOADS_TOKEN')
    token = request.args.get('token')
    if token_required:
        if not token or token != token_required:
            current_app.logger.warning('Acceso denegado a /admin/uploads: token inválido o ausente')
            return render_template('403.html'), 403

    # Intentar obtener los registros desde la API Multimedia para mapear con Sitios
    try:
        api_multimedia = APIClient('Multimedia')
        multimedia_records = api_multimedia.get_data() or []
    except Exception as ex:
        current_app.logger.warning(f"Error obteniendo registros de Multimedia desde API: {ex}")
        multimedia_records = []

    api_sitios = APIClient('Sitios')
    sitio_cache = {}

    entries = []
    for m in multimedia_records:
        # obtener fkidSitio y resolver nombre
        fkid = m.get('fkidSitio')
        sitio_name = None
        if fkid:
            sitio_name = sitio_cache.get(fkid)
            if sitio_name is None:
                try:
                    sitio_resp = api_sitios.get_data_by_key('idSitio', fkid)
                    if sitio_resp and isinstance(sitio_resp, dict):
                        datos = sitio_resp.get('datos', [])
                        if datos:
                            sitio_name = datos[0].get('nombre')
                        else:
                            sitio_name = None
                    else:
                        sitio_name = None
                except Exception:
                    sitio_name = None
                sitio_cache[fkid] = sitio_name

        # extraer filename a partir de la URL (si disponible)
        url = m.get('url') or ''
        raw_path = urllib.parse.urlparse(url).path if url else ''
        filename = os.path.basename(raw_path) if raw_path else m.get('url') or ''
        filename = urllib.parse.unquote(filename).lstrip('/\\')

        href = url_for('static', filename=f'media/{filename}') if filename else url

        entries.append({
            'idMultimedia': m.get('idMultimedia'),
            'filename': filename,
            'sitio_name': sitio_name,
            'url': url,
            'href': href
        })

    return render_template('uploads_list.html', entries=entries, folder=upload_folder)

@vistaAdmin.route('/admin/lugares_sugeridos', methods=['GET'])
def gestionar_lugares_sugeridos():
    api_lugares = APIClient("Sitios")
    try:
        lugares = api_lugares.get_data() or []
        # Resolver nombres de localidad y categoria para mostrar en la tabla
        api_localidades = APIClient("Localidad")
        try:
            localidades = api_localidades.get_data() or []
        except Exception:
            localidades = []
        localidad_map = {}
        for loc in localidades:
            key = loc.get('idLocalidad') or loc.get('id')
            if key:
                localidad_map[str(key)] = loc.get('nombre')

        api_categorias = APIClient("Categoria_Turistica")
        try:
            categorias = api_categorias.get_data() or []
        except Exception:
            categorias = []
        categoria_map = {}
        for c in categorias:
            key = c.get('idCategoria_Turistica') or c.get('id')
            if key:
                categoria_map[str(key)] = c.get('nombre')

        lugares_pendientes = [lugar for lugar in lugares if lugar.get("estado") != "Aprobado"]
        # Anotar cada lugar con los nombres resueltos
        for lugar in lugares_pendientes:
            fk_local = lugar.get('fkidLocalidad') or lugar.get('idLocalidad') or lugar.get('localidad')
            lugar['localidad_nombre'] = localidad_map.get(str(fk_local)) if fk_local else (lugar.get('localidad') or '—')
            fk_cat = lugar.get('fkidCategoria_Turistica') or lugar.get('idCategoria_Turistica') or lugar.get('categoria')
            lugar['categoria_nombre'] = categoria_map.get(str(fk_cat)) if fk_cat else (lugar.get('categoria') or '—')

        return render_template('lugares_sugeridos.html', lugares=lugares_pendientes)
    except Exception as e:
        flash(f'Error al obtener lugares sugeridos: {str(e)}', 'danger')
        return redirect(url_for('vistaAdmin.admin_panel'))


@vistaAdmin.route('/admin/multimedia/eliminar/<idMultimedia>/<idSitio>', methods=['POST'])
def eliminar_multimedia(idMultimedia, idSitio):
    try:
        idMultimedia = str(idMultimedia).strip('<>')
    except Exception:
        pass
    try:
        idSitio = str(idSitio).strip('<>')
    except Exception:
        pass
    api_multimedia = APIClient('Multimedia')
    try:
        # Obtener registro para intentar borrar archivo físico
        try:
            m = api_multimedia.get_data_by_key('idMultimedia', idMultimedia)
            registro = m.get('datos', [])[0] if m and isinstance(m, dict) and m.get('datos') else None
        except Exception:
            registro = None

        if registro:
            url = registro.get('url') or ''
            raw_path = urllib.parse.urlparse(url).path if url else ''
            filename = os.path.basename(raw_path) if raw_path else ''
            filename = urllib.parse.unquote(filename).lstrip('/\\')
            if filename:
                upload_folder = current_app.config.get('UPLOAD_FOLDER') or os.path.join(current_app.root_path, 'static', 'media')
                candidates = [os.path.join(upload_folder, filename), os.path.join(current_app.root_path, 'static', 'media', filename)]
                for p in candidates:
                    try:
                        p = os.path.normpath(p)
                        if os.path.exists(p):
                            os.remove(p)
                            current_app.logger.info(f"Archivo multimedia eliminado: {p}")
                            break
                    except Exception as ex:
                        current_app.logger.warning(f"No se pudo eliminar archivo multimedia {p}: {ex}")

        # Eliminar registro en la API
        try:
            delete_resp = api_multimedia.delete_data(idMultimedia)
            # APIClient devuelve None en caso de error/status>=400
            if delete_resp is None:
                current_app.logger.warning(f'API delete returned None for idMultimedia={idMultimedia}')
                flash('No se pudo eliminar la multimedia en la API.', 'danger')
            else:
                current_app.logger.info(f'API multimedia eliminado: id={idMultimedia} respuesta={delete_resp}')
                # Verificar realmente que el registro ya no exista
                try:
                    verify = api_multimedia.get_data_by_key('idMultimedia', idMultimedia)
                    # Si verify es dict con 'datos' o lista no vacío, la eliminación no se realizó
                    still_exists = False
                    if verify and isinstance(verify, dict):
                        datos = verify.get('datos')
                        if datos and len(datos) > 0:
                            still_exists = True
                    elif verify and isinstance(verify, list):
                        if len(verify) > 0:
                            still_exists = True

                    if still_exists:
                        current_app.logger.warning(f'Deletion not reflected in API for idMultimedia={idMultimedia} verify={verify}')
                        flash('La multimedia no pudo eliminarse completamente (registro aún presente).', 'warning')
                    else:
                        flash('Multimedia eliminada.', 'success')
                except Exception as ex2:
                    current_app.logger.exception(f'Error al verificar eliminación en API para id={idMultimedia}: {ex2}')
                    flash('Multimedia eliminada (no se pudo verificar en la API).', 'info')
        except Exception as ex:
            current_app.logger.exception(f'Excepción al llamar API delete para id={idMultimedia}: {ex}')
            flash('Error inesperado al eliminar la multimedia en la API.', 'danger')
    except Exception as e:
        current_app.logger.warning(f'Fallo al eliminar multimedia id={idMultimedia}: {e}')
        flash('No se pudo eliminar la multimedia.', 'danger')
    return redirect(url_for('vistaAdmin.editar_lugar', id=idSitio))

@vistaAdmin.route('/admin/sitios_turisticos', methods=['GET'])
def gestionar_sitios_turisticos():
    api_sitios = APIClient("Sitios")
    try:
        sitios = api_sitios.get_data() or []
        # Filtrar sitios aprobados
        sitios_aprobados = [s for s in sitios if s.get("estado") == "Aprobado"]

        # Resolver nombres de localidad y categoría para mostrar en la tabla
        api_localidades = APIClient("Localidad")
        try:
            localidades = api_localidades.get_data() or []
        except Exception:
            localidades = []
        localidad_map = {}
        for loc in localidades:
            key = loc.get('idLocalidad') or loc.get('id')
            if key:
                localidad_map[str(key)] = loc.get('nombre')

        api_categorias = APIClient("Categoria_Turistica")
        try:
            categorias = api_categorias.get_data() or []
        except Exception:
            categorias = []
        categoria_map = {}
        for c in categorias:
            key = c.get('idCategoria_Turistica') or c.get('id')
            if key:
                categoria_map[str(key)] = c.get('nombre')

        # Anotar cada sitio aprobado con los nombres resueltos (fallback a campos ya presentes)
        for sitio in sitios_aprobados:
            fk_local = sitio.get('fkidLocalidad') or sitio.get('idLocalidad') or sitio.get('localidad')
            sitio['localidad_nombre'] = localidad_map.get(str(fk_local)) if fk_local else (sitio.get('localidad') or '—')
            fk_cat = sitio.get('fkidCategoria_Turistica') or sitio.get('idCategoria_Turistica') or sitio.get('categoria')
            sitio['categoria_nombre'] = categoria_map.get(str(fk_cat)) if fk_cat else (sitio.get('categoria') or '—')

        return render_template('sitios_turisticos.html', sitios=sitios_aprobados)
    except Exception as e:
        flash(f'Error al obtener sitios turísticos: {str(e)}', 'danger')
        return redirect(url_for('vistaAdmin.admin_panel'))
