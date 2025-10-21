from flask import Blueprint, render_template, request, jsonify, current_app
from utils.api_client import APIClient
from forms.formSugerido import LugarSugeridoForm  # tu formulario Flask-WTF
from werkzeug.utils import secure_filename
import os
import uuid
import requests
import logging

vistaSugerido = Blueprint('vistaSugerido', __name__)


@vistaSugerido.route('/sugerir', methods=['GET', 'POST'])
def sugerir_lugar():
    try:
        form = LugarSugeridoForm()
        api_sitios = APIClient("Sitios")
        api_multimedia = APIClient("Multimedia")
        api_localidades = APIClient("Localidad")
        api_categorias = APIClient("Categoria_Turistica")

        # Obtener localidades y categorías para el formulario
        localidades = api_localidades.get_data()
        categorias = api_categorias.get_data()

        form.idLocalidad.choices = [(loc['idLocalidad'], loc['nombre']) for loc in localidades]
        form.idCategoria_Turistica.choices = [(cat['idCategoria_Turistica'], cat['nombre']) for cat in categorias]

        if request.method == 'POST':
            print("[DEBUG] Datos enviados al formulario:", request.form.to_dict())
            print("[DEBUG] Archivos enviados:", request.files.getlist('archivos'))

            if form.validate_on_submit():
                print("[DEBUG] Formulario validado correctamente")

                # Datos del lugar
                nuevo_sitio = {
                    "idSitio": str(uuid.uuid4()),
                    "nombre": form.nombre.data,
                    "direccion": form.direccion.data,
                    "descripcion": form.descripcion.data,
                    "latitud": float(form.latitud.data) if form.latitud.data else None,
                    "longitud": float(form.longitud.data) if form.longitud.data else None,
                    "horario_apertura": form.horario_apertura.data.strftime("%H:%M:%S") if form.horario_apertura.data else None,
                    "horario_cierre": form.horario_cierre.data.strftime("%H:%M:%S") if form.horario_cierre.data else None,
                    "tarifa": float(form.tarifa.data) if form.tarifa.data else None,
                    "estado": "Sugerido",
                    "fkidLocalidad": form.idLocalidad.data,
                    "fkidCategoria_Turistica": form.idCategoria_Turistica.data,
                    "creado_por": "618ebb2e-ddf4-4344-8a06-e58c26038b70"
                }

                print("[DEBUG] Datos preparados para el sitio:", nuevo_sitio)

                # Enviar datos del sitio a la API
                sitio_response = api_sitios.insert_data(json_data=nuevo_sitio)
                print("[DEBUG] Respuesta de la API para el sitio:", sitio_response)

                # La API puede devolver estructuras diferentes. Consideramos éxito si:
                # - existe la clave 'success' con valor truthy
                # - o 'estado' == 200
                # - o se devuelve un 'idSitio'
                sitio_ok = False
                if isinstance(sitio_response, dict):
                    if sitio_response.get("success"):
                        sitio_ok = True
                    elif sitio_response.get("estado") == 200:
                        sitio_ok = True
                    elif sitio_response.get("idSitio"):
                        sitio_ok = True

                if not sitio_ok:
                    print("[ERROR] Respuesta inválida al crear sitio:", sitio_response)
                    return jsonify(success=False, message="Error al guardar el sitio", respuesta=sitio_response)

                # Determinar el idSitio: preferir el id devuelto por la API si es válido,
                # en caso contrario usar el id local que generamos (nuevo_sitio["idSitio"]).
                generated_id = nuevo_sitio.get("idSitio")
                api_id = None
                if isinstance(sitio_response, dict):
                    api_id = sitio_response.get("idSitio")

                print("[DEBUG] ID generado localmente:", generated_id)
                print("[DEBUG] ID devuelto por la API:", api_id)

                zero_guid = '00000000-0000-0000-0000-000000000000'
                if api_id and api_id != zero_guid:
                    id_sitio = api_id
                else:
                    print("[WARN] API no devolvió un id válido; usando id local generado.")
                    id_sitio = generated_id

                # Procesar archivos multimedia
                archivos = request.files.getlist('archivos')

                print("[DEBUG] Iniciando procesamiento de archivos multimedia")
                if not archivos:
                    print("[ERROR] No se encontraron archivos multimedia en la solicitud.")
                    return jsonify(success=False, message="No se encontraron archivos multimedia en la solicitud.")

                print("[DEBUG] Archivos detectados para procesamiento:", [archivo.filename for archivo in archivos])

                def determinar_tipo_multimedia(filename):
                    extension = filename.rsplit('.', 1)[1].lower()
                    if extension in ['jpg', 'jpeg', 'png', 'gif']:
                        return "imagen"
                    elif extension in ['mp4', 'avi', 'mov']:
                        return "video"
                    return "desconocido"

                # Validar y guardar archivos multimedia
                for archivo in archivos:
                    print("[DEBUG] Procesando archivo:", archivo.filename)

                    if not archivo.filename:
                        print("[ERROR] Archivo sin nombre válido.")
                        return jsonify(success=False, message="Archivo sin nombre válido")

                    # Generar nombre único para evitar colisiones
                    filename = f"{uuid.uuid4().hex}_{secure_filename(archivo.filename)}"
                    upload_folder = current_app.config.get('UPLOAD_FOLDER')
                    if not upload_folder:
                        print("[ERROR] app.config['UPLOAD_FOLDER'] no está definido")
                        return jsonify(success=False, message="Configuración de uploads inválida")

                    file_path = os.path.join(upload_folder, filename)

                    # Validar si el archivo fue recibido correctamente
                    if not archivo:
                        print("[ERROR] No se recibió ningún archivo.")
                        return jsonify(success=False, message="No se recibió ningún archivo")

                    print("[DEBUG] Archivo recibido:", archivo.filename)

                    # Intentar guardar el archivo
                    try:
                        archivo.save(file_path)
                        print("[DEBUG] Archivo guardado en:", file_path)
                    except Exception as e:
                        print("[ERROR] Error al guardar el archivo:", e)
                        return jsonify(success=False, message="Error al guardar el archivo")

                    # Verificar si el archivo existe en la ruta esperada
                    if not os.path.exists(file_path):
                        print("[ERROR] El archivo no se encuentra en la ruta esperada:", file_path)
                        return jsonify(success=False, message="Error al verificar el archivo guardado")

                    print("[DEBUG] Archivo validado y guardado correctamente.")

                    tipo_multimedia = determinar_tipo_multimedia(filename)
                    print("[DEBUG] Tipo de multimedia detectado:", tipo_multimedia)

                    multimedia_data = {
                        "idMultimedia": str(uuid.uuid4()),
                        "url": f"/static/media/{filename}",
                        "descripcion": "Archivo subido automáticamente",
                        "tipo": tipo_multimedia,
                        "fkidSitio": id_sitio
                    }

                    # Enviar datos a la API
                    print("[DEBUG] Enviando datos a la API de multimedia:", multimedia_data)
                    multimedia_response = api_multimedia.insert_data(json_data=multimedia_data)
                    print("[DEBUG] Respuesta completa de la API para multimedia:", multimedia_response)

                    # Aceptar varias formas de respuesta: success flag, estado==200, o devolución de idMultimedia/idSitio
                    multimedia_ok = False
                    if isinstance(multimedia_response, dict):
                        if multimedia_response.get("success"):
                            multimedia_ok = True
                        elif multimedia_response.get("estado") == 200:
                            multimedia_ok = True
                        elif multimedia_response.get("idMultimedia") or multimedia_response.get("idSitio"):
                            multimedia_ok = True

                    if not multimedia_ok:
                        print("[ERROR] Error al guardar multimedia en la API. Respuesta:", multimedia_response)
                        return jsonify(success=False, message="Error al guardar multimedia en la API", respuesta=multimedia_response)

                return jsonify(success=True, message="Lugar sugerido con éxito", idSitio=id_sitio)

            else:
                print("[DEBUG] Errores en el formulario:", form.errors)
                return jsonify(success=False, message="Formulario inválido", errors=form.errors)

        print("[DEBUG] Localidades cargadas:", localidades)
        print("[DEBUG] Categorías cargadas:", categorias)

        return render_template("seccion4.html", form=form, localidades=localidades, categorias=categorias)
    except Exception as e:
        print("[ERROR] Ocurrió un error en sugerir_lugar:", e)
        return jsonify(success=False, message="Ocurrió un error interno. Consulte los logs para más detalles.")

@vistaSugerido.route('/lugares', methods=['GET'])
def obtener_lugares():
    try:
        api_client = APIClient("Sitios")
        lugares = api_client.get_data()
        # Si lugares es una lista, devuélvela directamente
        if isinstance(lugares, list):
            return jsonify(lugares)
        # Si lugares es un diccionario, extrae la clave "datos"
        return jsonify(lugares.get("datos", []))
    except Exception as e:
        logging.error(f"Error al obtener sitios sugeridos: {str(e)}")
        return jsonify({'error': str(e)}), 500
