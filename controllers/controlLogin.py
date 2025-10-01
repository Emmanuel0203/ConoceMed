import os
import requests
from models.Usuario import Usuario

API_URL = os.getenv("API_URL")  # ej: http://localhost:5031/api

def autenticar_usuario(correo, password):
    try:
        url = f"{API_URL}/usuario?correo={correo}&password={password}"
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()

            if data.get("total", 0) > 0:
                usuario_data = data["datos"][0]  # 👈 aquí está el usuario real
                user = Usuario.from_dict(usuario_data)
                return True, user
            else:
                return False, None
        else:
            print(f"Error API: {response.status_code} - {response.text}")
            return False, None
    except Exception as e:
        print(f"Ocurrió un error: {e}")
        return False, None
