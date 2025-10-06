# api_client.py
import requests
import os

class APIClient:
    """Cliente genérico para interactuar con la API de ConoceMed."""

    def __init__(self, table_name: str):
        self.table_name = table_name
        base_url = os.getenv("API_URL")  # Ejemplo: http://localhost:5031/api
        if not base_url:
            raise ValueError("⚠️ La variable de entorno API_URL no está configurada.")
        self.api_url = base_url.rstrip("/")  # Quita una barra final si la hay

    # ------------------------ MÉTODO BASE ------------------------
    def _make_request(self, method="GET", endpoint="", json_data=None, files=None, **params):
        """
        Realiza una solicitud HTTP a la API.
        Soporta GET, POST, PUT y DELETE.
        """
        url = f"{self.api_url}/{endpoint}" if endpoint else f"{self.api_url}/{self.table_name}"

        try:
            if method.upper() == "GET":
                response = requests.get(url, params=params, timeout=10)

            elif method.upper() == "POST":
                if files:  # Si hay archivos, se usa multipart/form-data
                    response = requests.post(url, data=json_data, files=files, timeout=15)
                else:
                    response = requests.post(url, json=json_data, timeout=10)

            elif method.upper() == "PUT":
                response = requests.put(url, json=json_data, timeout=10)

            elif method.upper() == "DELETE":
                response = requests.delete(url, timeout=10)

            else:
                raise ValueError(f"Método HTTP no soportado: {method}")

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            print(f"[APIClient] Error en la petición a {url}: {e}")
            return None

    # ------------------------ MÉTODOS DE UTILIDAD ------------------------
    def get_data(self, **kwargs):
        """
        Obtiene los datos de la tabla (devuelve solo la lista de 'datos').
        Ejemplo de retorno: [ {idLugar: ..., nombre: ...}, ... ]
        """
        response = self._make_request("GET", self.table_name, **kwargs)
        if response and isinstance(response, dict):
            return response.get("datos", [])
        return []

    def insert_data(self, json_data=None, files=None):
        """
        Inserta datos en la tabla. Soporta archivos (images/videos).
        """
        return self._make_request("POST", self.table_name, json_data=json_data, files=files)

    def update_data(self, record_id, json_data=None):
        """Actualiza un registro por su ID."""
        endpoint = f"{self.table_name}/{record_id}"
        return self._make_request("PUT", endpoint, json_data=json_data)

    def delete_data(self, record_id):
        """Elimina un registro por su ID."""
        endpoint = f"{self.table_name}/{record_id}"
        return self._make_request("DELETE", endpoint)

    # ------------------------ MÉTODO ESPECIAL (EJEMPLO) ------------------------
    def get_user_by_email(self, email):
        """Busca un usuario en la API por su email."""
        users = self.get_data()
        for user in users:
            if user.get("email") == email:
                return user
        return None
