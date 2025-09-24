# api_client.py - ACTUALIZADO PARA TU API REAL
import requests
import os

class APIClient:
    """Cliente genérico para interactuar con la API local de Innovación."""

    def __init__(self, table_name: str):
        self.table_name = table_name
        # Lee la URL base desde las variables de entorno (CORREGIDA)
        base_url = os.getenv("BACKEND_LOCAL_URL")  # http://localhost:5186/api/sgv
        self.api_url = base_url
        
        print(f"🔧 APIClient inicializado con URL: {self.api_url}")

    def _make_request(self, method="GET", endpoint="", **params):
        """Hace una petición a la API."""
        url = f"{self.api_url}/{endpoint}" if endpoint else f"{self.api_url}/{self.table_name}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, params=params, timeout=10)
            elif method.upper() == "POST":
                response = requests.post(url, json=params, timeout=10)
            else:
                raise ValueError(f"Método HTTP no soportado: {method}")
                
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"[APIClient] Error en la petición a {url}: {e}")
            return None

    def get_data(self, **kwargs):
        """Obtiene datos de la tabla."""
        data = self._make_request("GET", self.table_name, **kwargs)
        return data if data else []

    def get_user_by_email(self, email):
        """Método específico para buscar usuario por email."""
        users = self.get_data()
        if users:
            for user in users:
                if user.get('email') == email:
                    return user
        return None

    def insert_data(self, json_data=None):
        """Inserta datos en la tabla."""
        return self._make_request("POST", self.table_name, **json_data)

    def update_data(self, user_id, json_data=None):
        """Actualiza datos de un usuario específico."""
        endpoint = f"{self.table_name}/{user_id}"
        return self._make_request("PUT", endpoint, **json_data)

    def delete_data(self, user_id):
        """Elimina un usuario específico."""
        endpoint = f"{self.table_name}/{user_id}"
        return self._make_request("DELETE", endpoint)