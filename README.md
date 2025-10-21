# ConoceMed 🏛️✨

### Descubre Medellín como nunca antes

**ConoceMed** es una innovadora plataforma de turismo patrimonial que transforma la manera en que exploras Medellín. Diseñada para conectarte con la rica historia, el vibrante arte y la profunda cultura de la ciudad, ConoceMed te invita a sumergirte en experiencias únicas que van más allá de lo tradicional.

#### ¿Qué hace especial a ConoceMed?

- 🎨 **Patrimonio Vivo**: Explora los tesoros históricos y culturales de Medellín de forma interactiva
- 🏨 **Experiencias Completas**: Descubre hotelería y servicios turísticos cuidadosamente seleccionados
- 🗺️ **Interfaz Intuitiva**: Navega por el patrimonio cultural con una experiencia de usuario moderna y atractiva
- 🌟 **Turismo Consciente**: Fomenta el turismo patrimonial responsable y el orgullo local

ConoceMed no es solo una guía turística, es tu compañero para redescubrir Medellín desde sus raíces hasta su presente cultural, haciendo que cada visita sea memorable y significativa.

---

## 🚀 Guía de Instalación

Este proyecto integra una base de datos SQL Server, una API en .NET y una aplicación Python para ofrecer una experiencia completa.

## 📋 Requisitos Previos

Antes de comenzar, asegúrate de tener instalado:

- **SQL Server Management Studio (SSMS)** - Versión 2019 o superior
- **.NET SDK** - Versión 9
- **Python** - Versión 3.8 o superior
- **Git** - Para clonar el repositorio

---

## 🗄️ Paso 1: Configuración de la Base de Datos

### Instalación de SSMS

1. Descarga SQL Server Management Studio desde el [sitio oficial de Microsoft](https://learn.microsoft.com/en-us/sql/ssms/download-sql-server-management-studio-ssms)
2. Ejecuta el instalador y sigue las instrucciones en pantalla
3. Una vez instalado, abre SSMS

### Importación de la Base de Datos

1. **Conectarse al servidor:**
   - Abre SQL Server Management Studio
   - Conecta a tu instancia local de SQL Server (normalmente `localhost` o `.\SQLEXPRESS`)

2. **Crear la base de datos:**
   - Click derecho en `Databases` en el Object Explorer
   - Selecciona `New Database...`
   - Nombra la base de datos como: **`bdConoceMed`**
   - Click en `OK`

3. **Ejecutar el script SQL:**
   - Click derecho sobre la base de datos `bdConoceMed` recién creada
   - Selecciona `New Query`
   - Abre el archivo `.sql` proporcionado:
     - Ve a `File` → `Open` → `File...`
     - Selecciona el archivo `bdConoceMed.sql`
   - Ejecuta el script presionando `F5` o haciendo click en el botón `Execute`
   
   > **¿Por qué?** Este script contiene todas las instrucciones para crear las tablas, relaciones, procedimientos almacenados y datos iniciales necesarios para el funcionamiento del sistema.

4. **Verificar la importación:**
   - Expande el nodo de `bdConoceMed` en el Object Explorer
   - Verifica que aparezcan las tablas y objetos de la base de datos

---

## ⚙️ Paso 2: Configuración de la API (.NET)

### Instalación de .NET 9

1. Descarga .NET 9 SDK desde [dotnet.microsoft.com](https://dotnet.microsoft.com/download)
2. Ejecuta el instalador y completa la instalación
3. Verifica la instalación abriendo una terminal y ejecutando:
   ```bash
   dotnet --version
   ```
   Deberías ver la versión 9.x.x

### Configuración de la API

1. **Descomprimir el archivo:**
   - Extrae el contenido del archivo `.zip` de la API en una carpeta de tu elección

2. **Abrir terminal en la carpeta de la API:**
   - Navega hasta la carpeta donde descomprimiste la API
   - Abre una terminal/consola en esa ubicación

3. **Limpiar compilaciones anteriores:**
   ```bash
   dotnet clean
   ```
   > **¿Para qué sirve?** Elimina todos los archivos compilados anteriormente y limpia los directorios `bin` y `obj`. Esto asegura que partimos de un estado limpio sin conflictos de versiones anteriores.

4. **Compilar el proyecto:**
   ```bash
   dotnet build
   ```
   > **¿Para qué sirve?** Compila el código fuente de la API, verifica que no haya errores de sintaxis o dependencias faltantes, y genera los archivos ejecutables en la carpeta `bin`. Si hay errores, se mostrarán en este paso.

5. **Ejecutar la API:**
   ```bash
   dotnet run
   ```
   > **¿Para qué sirve?** Inicia el servidor de la API. El comando compila (si es necesario) y ejecuta la aplicación. La API quedará escuchando peticiones HTTP en el puerto configurado (generalmente `http://localhost:5000` o `https://localhost:5001`).

6. **Verificar que la API está corriendo:**
   - Deberías ver un mensaje indicando que la aplicación está escuchando en un puerto específico
   - **No cierres esta terminal**, la API debe permanecer ejecutándose

---

## 🐍 Paso 3: Configuración de la Aplicación Python

### Clonar el repositorio

```bash
git clone [URL_DEL_REPOSITORIO]
cd ConoceMed
```

### Crear y activar el entorno virtual

Un entorno virtual aísla las dependencias del proyecto para evitar conflictos con otros proyectos Python.

**En Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**En macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

> **¿Para qué sirve?** El entorno virtual crea un espacio aislado donde se instalarán todas las librerías necesarias sin afectar la instalación global de Python en tu sistema.

### Instalar dependencias

```bash
pip install -r requirements.txt
```

> **¿Para qué sirve?** Este comando lee el archivo `requirements.txt` que contiene la lista de todas las librerías Python necesarias para el proyecto (como frameworks, conectores de base de datos, etc.) y las instala en el entorno virtual.

### Ejecutar la aplicación

```bash
python main.py
```

La aplicación debería iniciar correctamente y estar lista para usarse.

---

## 🔐 Credenciales de Acceso

Para iniciar sesión en el sistema, utiliza las siguientes credenciales:

- **Usuario:** `example@ejemplo.com`
- **Contraseña:** `123`

---

## 📝 Notas Importantes

- Asegúrate de tener todos los servicios corriendo simultáneamente:
  - SQL Server con la base de datos `bdConoceMed`
  - API de .NET ejecutándose
  - Aplicación Python ejecutándose

- Si encuentras errores de conexión, verifica:
  - Que SQL Server esté corriendo
  - Que la cadena de conexión en la API apunte a `bdConoceMed`
  - Que la API esté configurada con el puerto correcto en la aplicación Python

---

## 🆘 Solución de Problemas

### Error al conectar a SQL Server
- Verifica que SQL Server esté corriendo
- Confirma el nombre de tu instancia de SQL Server
- Revisa la cadena de conexión en la configuración de la API

### Error al ejecutar la API
- Asegúrate de tener .NET 9 instalado correctamente
- Verifica que no haya otro proceso usando el mismo puerto

### Error al ejecutar la aplicación Python
- Confirma que el entorno virtual esté activado
- Verifica que todas las dependencias se instalaron correctamente
- Asegúrate de que la API esté corriendo antes de iniciar la aplicación

---

## 📞 Soporte

Para reportar problemas o solicitar ayuda, contacta al equipo de desarrollo.

---

**¡Listo!** Ahora tienes ConoceMed completamente configurado y funcionando. 🎉
