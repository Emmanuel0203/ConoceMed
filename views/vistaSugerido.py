from flask import Blueprint, render_template, request, jsonify
from utils.api_client import APIClient
from forms.formSugerido import LugarSugeridoForm  # tu formulario Flask-WTF
from werkzeug.utils import secure_filename
import os
import uuid
import requests

vistaSugerido = Blueprint('vistaSugerido', __name__)
UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@vistaSugerido.route('/sugerir', methods=['GET', 'POST'])
def sugerir_lugar():
    form = LugarSugeridoForm()
    api_lugares = APIClient("Lugar_Sugerido")
    api_localidades = APIClient("Localidad")
    api_multimedia = APIClient("Multimedia")
    api_categorias = APIClient("Categoria_Turistica")

    # 🔹 Obtener localidades para llenar el select dinámicamente
    localidades_data = api_localidades.get_data()
    localidades = localidades_data.get("datos", []) if isinstance(localidades_data, dict) else localidades_data
    print("✅ Localidades (primeros 3):", localidades[:3])
    for l in localidades[:3]:
        print(f"ID: {l.get('idLocalidad')}, Nombre: {l.get('nombre')}")

    form.idLocalidad.choices = [(str(l["idLocalidad"]), l["nombre"]) for l in localidades]
    print(form.idLocalidad.choices)

    # � Obtener categorías turísticas para llenar el select dinámicamente
    categorias_data = api_categorias.get_data()
    categorias = categorias_data.get("datos", []) if isinstance(categorias_data, dict) else categorias_data
    form.idCategoria_Turistica.choices = [(str(c["idCategoria_Turistica"]), c["nombre"]) for c in categorias]
    print(form.idCategoria_Turistica.choices)

    # �📩 Si el formulario es enviado (fetch)
    if request.method == 'POST':
        if form.validate_on_submit():
            # Datos del lugar
            nombre = form.nombre.data
            direccion = form.direccion.data
            descripcion = form.descripcion.data
            latitud = form.latitud.data
            longitud = form.longitud.data
            horario_apertura = form.horario_apertura.data
            horario_cierre = form.horario_cierre.data
            tarifa = float(form.tarifa.data)
            id_localidad = form.idLocalidad.data
            id_categoria = form.idCategoria_Turistica.data

            print(request.form.get('tarifa'))
            print("Valor recibido en tarifa:", form.tarifa.data, request.form.get('tarifa'))

            idLugar_Sugerido = str(uuid.uuid4())

            # Crear JSON para Lugar_Sugerido
            nuevo_lugar = {
                "idLugar_Sugerido": idLugar_Sugerido,
                "nombre": nombre,
                "direccion": direccion,
                "descripcion": descripcion,
                "latitud": float(latitud),
                "longitud": float(longitud),
                "horario_apertura": horario_apertura.strftime("%H:%M:%S"),
                "horario_cierre": horario_cierre.strftime("%H:%M:%S"),
                "tarifa": tarifa,
                "estado": "Pendiente",
                "fkidLocalidad": id_localidad,
                "fkidCategoria_Turistica": id_categoria
            }

            # Enviar solo el diccionario del lugar a la API
            print("Datos del lugar enviados a la API:")
            for k, v in nuevo_lugar.items():
                print(f"  {k}: {v} (type: {type(v)})")
            url = "http://localhost:5031/api/Lugar_Sugerido"  # Define la URL de tu API
            datos = nuevo_lugar  # Usa el diccionario que ya preparaste

            try:
                response = requests.post(url, json=datos)
                print(response.status_code)
                print(response.text)  # Aquí verás el JSON de error devuelto por la API
            except requests.exceptions.RequestException as e:
                if hasattr(e, 'response') and e.response is not None:
                    print(e.response.text)
                else:
                    print("No se recibió respuesta de la API:", e)


            id_lugar = None
            try:
                id_lugar = response.json().get("idLugar_Sugerido")
            except Exception as e:
                print("❌ Error al extraer idLugar_Sugerido de la respuesta:", e)
                print("Respuesta completa:", response.text)
            print("ID lugar recibido de la API:", id_lugar)

            # Procesar archivos multimedia
            archivos = request.files.getlist("archivos")
            for archivo in archivos:
                filename = secure_filename(archivo.filename)
                file_path = os.path.join(UPLOAD_FOLDER, filename)
                archivo.save(file_path)

                tipo = "1" if archivo.mimetype.startswith("image") else "3" if archivo.mimetype.startswith("video") else "2"

                nuevo_multimedia = {
                    "titulo": filename,
                    "url": f"/{file_path}",
                    "descripcion": f"Archivo asociado al lugar {nombre}",
                    "fkidTipo_Multi": tipo,
                    "fkidLugar_Sugerido": id_lugar
                }
                print("➡️ Enviando multimedia a la API:", nuevo_multimedia)
                multimedia_response = api_multimedia.insert_data(json_data=nuevo_multimedia)
                print("Respuesta de la API multimedia:", multimedia_response)

            return jsonify(success=True, message="Lugar sugerido con éxito", idLugar_Sugerido=id_lugar)

        else:
            print(form.errors)  # Esto mostrará los errores de validación en la terminal
            return jsonify(success=False, message="Formulario inválido")

    # Render inicial del formulario
    return render_template("seccion4.html", form=form, localidades=localidades)
