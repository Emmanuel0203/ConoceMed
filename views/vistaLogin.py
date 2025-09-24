# views/login.py - ADAPTADO A TU API REAL
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import requests
import os
from forms.formsLogin import LoginForm

vistaLogin = Blueprint("login", __name__, template_folder="templates")

@vistaLogin.route("/login", methods=["GET", "POST"])
def login_view():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        # 🎯 Usar la URL correcta según tu API real
        backend_url = os.getenv("BACKEND_LOCAL_URL")  # http://localhost:5186/api/sgv
        
        print(f"🔧 DEBUG: BACKEND_LOCAL_URL = '{backend_url}'")
        
        if not backend_url:
            print("❌ ERROR: BACKEND_LOCAL_URL no está configurada")
            flash("Error de configuración del sistema", "danger")
            return render_template("templatesLogin/login.html", form=form)

        try:
            # OPCIÓN 1: Buscar usuario por email (GET request)
            # Construir URL para buscar usuarios por email
            search_url = f"{backend_url}/usuario"  # Endpoint que ya funciona
            
            print(f"🌐 Buscando usuarios en: {search_url}")
            
            # Primero obtener todos los usuarios (tu endpoint funcional)
            response = requests.get(search_url, timeout=10)
            
            print(f"✅ Status: {response.status_code}")
            print(f"📄 Response: {response.text[:300]}...")
            
            if response.status_code == 200:
                users = response.json()
                print(f"👥 Total usuarios encontrados: {len(users)}")
                
                # Buscar el usuario con el email proporcionado
                user_found = None
                for user in users:
                    print(f"🔍 Verificando usuario: {user.get('email', 'No email')}")
                    if user.get('email') == email:
                        user_found = user
                        break
                
                if user_found:
                    print(f"👤 Usuario encontrado: {user_found}")
                    
                    # Verificar contraseña (ajustar según tu estructura)
                    # ⚠️ IMPORTANTE: En producción usa hash de contraseñas
                    stored_password = user_found.get('password') or user_found.get('contrasena')
                    
                    if stored_password == password:
                        # 🎯 CAMBIAR: En lugar de session["user"] = {...}
                        # Usar las variables que TU DASHBOARD ya espera:
                        
                        session["user_email"] = email
                        session["user_name"] = user_found.get("name") or user_found.get("nombre") or "Usuario"
                        session["user_role"] = user_found.get("role") or user_found.get("rol") or "Usuario"
                        session["user_id"] = user_found.get("id")
                        
                        print(f"✅ Sesión configurada para dashboard:")
                        print(f"   - user_email: {session['user_email']}")
                        print(f"   - user_name: {session['user_name']}")
                        print(f"   - user_role: {session['user_role']}")
                        print(f"   - user_id: {session['user_id']}")
                        
                        flash("¡Login exitoso! Bienvenido", "success")
                        return redirect(url_for("dashboard.index")) # Ajustar ruta
                    else:
                        print(f"❌ Contraseña incorrecta. Esperada: '{password}', Encontrada: '{stored_password}'")
                        flash("Contraseña incorrecta", "danger")
                else:
                    print(f"❌ Usuario con email '{email}' no encontrado")
                    flash("Usuario no encontrado", "danger")
            else:
                print(f"❌ Error HTTP: {response.status_code}")
                flash(f"Error del servidor: {response.status_code}", "danger")
                
        except requests.exceptions.ConnectionError as e:
            print(f"❌ ERROR DE CONEXIÓN: {e}")
            flash("No se puede conectar al servidor. Verifica que la API esté ejecutándose.", "danger")
            
        except requests.exceptions.Timeout:
            print(f"❌ TIMEOUT al conectar con {search_url}")
            flash("La conexión tardó demasiado tiempo", "danger")
            
        except Exception as e:
            print(f"❌ ERROR INESPERADO: {e}")
            flash("Error interno del sistema", "danger")

    return render_template("templatesLogin/login.html", form=form)

@vistaLogin.route('/logout')
def logout():
    session.clear()
    flash('Has cerrado sesión correctamente', 'success')
    return redirect(url_for('login.login_view'))

# 🧪 Ruta de prueba para verificar la estructura de usuarios
@vistaLogin.route('/test-users')
def test_users():
    """Ruta para ver la estructura de usuarios de tu API"""
    backend_url = os.getenv("BACKEND_LOCAL_URL")
    
    if not backend_url:
        return "❌ BACKEND_LOCAL_URL no configurada", 500
    
    try:
        response = requests.get(f"{backend_url}/usuario", timeout=5)
        users = response.json()
        
        # Mostrar estructura de los primeros usuarios (sin contraseñas)
        sample_users = []
        for user in users[:3]:  # Solo los primeros 3
            safe_user = {k: v for k, v in user.items() if 'password' not in k.lower() and 'contrasena' not in k.lower()}
            sample_users.append(safe_user)
        
        return f"""
        <h2>📊 Estructura de usuarios en tu API</h2>
        <p><strong>URL:</strong> {backend_url}/usuario</p>
        <p><strong>Total usuarios:</strong> {len(users)}</p>
        <p><strong>Estructura de campos:</strong></p>
        <pre>{sample_users}</pre>
        <p><strong>Campos disponibles en el primer usuario:</strong></p>
        <pre>{list(users[0].keys()) if users else 'No hay usuarios'}</pre>
        """
    except Exception as e:
        return f"❌ Error: {e}", 500