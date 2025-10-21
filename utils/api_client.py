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

        response = None
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

            # No lanzar excepciones aquí; manejar status codes explícitamente para poder registrar body
            status = getattr(response, 'status_code', None)
            if status is None:
                try:
                    import logging
                    logging.getLogger(__name__).warning(f"[APIClient] Sin status_code en respuesta para {url}")
                except Exception:
                    pass
                return None

            # Registrar y devolver None para códigos de error (>=400), incluyendo body para diagnóstico
            if status >= 400:
                try:
                    import logging
                    body = response.text if hasattr(response, 'text') else '<no-body>'
                    logging.getLogger(__name__).warning(f"[APIClient] Error {status} en {url}: {body}")
                except Exception:
                    pass
                return None

            # Algunas respuestas pueden ser 204 No Content o no contener JSON.
            if status == 204 or not response.content:
                return {}
            try:
                return response.json()
            except ValueError:
                # Respuesta no JSON pero status OK
                return {}
        except requests.exceptions.RequestException as e:
            # Registrar el error y devolver None para que el llamador lo maneje
            try:
                import logging
                logging.getLogger(__name__).warning(f"[APIClient] Error en la petición a {url}: {e}")
            except Exception:
                pass
            # Si hay una respuesta disponible, intentar registrar body también
            try:
                if response is not None and hasattr(response, 'text'):
                    import logging
                    logging.getLogger(__name__).warning(f"[APIClient] Body de la respuesta de error: {response.text}")
            except Exception:
                pass
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

    def get_data_by_id(self, record_id):
        """Obtiene un registro específico por su ID."""
        # Construir la URL según el formato esperado por la API
        endpoint = f"{self.table_name}/idUsuario/{record_id}"
        return self._make_request("GET", endpoint)

    def get_data_by_key(self, key_name, key_value, schema=None):
        """
        Obtiene registros filtrados por una clave específica.
        """
        # Normalizar key_value para evitar que venga con caracteres angulares '<' '>'
        try:
            key_value = str(key_value).strip('<>')
        except Exception:
            key_value = key_value
        endpoint = f"{self.table_name}/{key_name}/{key_value}"
        params = {"esquema": schema} if schema else {}
        return self._make_request("GET", endpoint, **params)

    def update_data_by_key(self, key_name, key_value, json_data=None):
        """
        Actualiza un registro existente basado en una clave específica.
        """
        try:
            key_value = str(key_value).strip('<>')
        except Exception:
            pass
        endpoint = f"{self.table_name}/{key_name}/{key_value}"
        return self._make_request("PUT", endpoint, json_data=json_data)

    def delete_data_by_key(self, key_name, key_value, schema=None):
        """
        Elimina un registro existente basado en una clave específica.
        """
        try:
            key_value = str(key_value).strip('<>')
        except Exception:
            pass
        endpoint = f"{self.table_name}/{key_name}/{key_value}"
        params = {"esquema": schema} if schema else {}
        return self._make_request("DELETE", endpoint, **params)

    # ------------------------ MÉTODO ESPECIAL (EJEMPLO) ------------------------
    def get_user_by_email(self, email):
        """Busca un usuario en la API por su email."""
        users = self.get_data()
        for user in users:
            if user.get("email") == email:
                return user
        return None
