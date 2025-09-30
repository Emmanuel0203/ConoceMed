import requests
from config import Config
from models.Sitio import SitioTuristico

def obtener_sitios():
    try:
        response = requests.get(f"{Config.API_BASE_URL}/sitio_turistico")
        response.raise_for_status()
        data = response.json()
        sitios = [SitioTuristico.from_dict(item) for item in data.get("datos", [])]
        return sitios
    except Exception as e:
        print(f"Error al consumir la API: {e}")
        return []


def obtener_sitio_por_id(sitio_id):
    try:
        response = requests.get(f"{Config.API_BASE_URL}/sitio_turistico/{sitio_id}")
        response.raise_for_status()
        data = response.json()
        return SitioTuristico.from_dict(data) if data else None
    except Exception as e:
        print(f"Error al consumir la API: {e}")
        return None
    

def crear_sitio(payload, rol):
    if rol != "admin":
        raise PermissionError("No autorizado: solo administradores pueden crear sitios")
    try:
        response = requests.post(f"{Config.API_BASE_URL}/sitio_turistico", json=payload)
        response.raise_for_status()
        data = response.json()
        return SitioTuristico.from_dict(data)
    except Exception as e:
        print(f"Error al crear sitio: {e}")
        return None
    

def actualizar_sitio(sitio_id, payload, rol):
    if rol != "admin":
        raise PermissionError("No autorizado: solo administradores pueden actualizar sitios")
    try:
        response = requests.put(f"{Config.API_BASE_URL}/sitio_turistico/{sitio_id}", json=payload)
        response.raise_for_status()
        data = response.json()
        return SitioTuristico.from_dict(data)
    except Exception as e:
        print(f"Error al actualizar sitio: {e}")
        return None
    

def eliminar_sitio(sitio_id, rol):
    if rol != "admin":
        raise PermissionError("No autorizado: solo administradores pueden eliminar sitios")
    try:
        response = requests.delete(f"{Config.API_BASE_URL}/sitio_turistico/{sitio_id}")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error al eliminar sitio: {e}")
        return None
