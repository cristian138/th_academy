# Guía de Instalación en Windows Server 2025 + IIS
## Sistema de Talento Humano - Academia Jotuns Club SAS
## Dominio: th.academiajotuns.com

---

## Requisitos del Servidor
- **Sistema Operativo:** Windows Server 2025
- **RAM:** Mínimo 4GB (recomendado 8GB)
- **Disco:** Mínimo 40GB
- **IIS:** Ya instalado
- **Acceso:** Administrador

---

## Paso 1: Instalar Python 3.11+

1. Descargar desde: https://www.python.org/downloads/
2. Ejecutar el instalador
3. **IMPORTANTE:** Marcar la casilla **"Add Python to PATH"**
4. Seleccionar **"Install for all users"**
5. Ruta recomendada: `C:\Python311\`

Verificar en PowerShell (ejecutar como Administrador):
```powershell
python --version
pip --version
```

---

## Paso 2: Instalar Node.js 18+

1. Descargar desde: https://nodejs.org/en/download/
2. Ejecutar el instalador con opciones por defecto
3. Marcar **"Automatically install the necessary tools"** si aparece

Verificar:
```powershell
node --version
npm --version
```

---

## Paso 3: Instalar MongoDB 7.0

1. Descargar desde: https://www.mongodb.com/try/download/community
   - Seleccionar: Windows x64, MSI
2. Ejecutar el instalador
3. Seleccionar **"Complete"**
4. Marcar **"Install MongoDB as a Service"**
5. Dejar la opción **"Run service as Network Service user"**
6. Instalar **MongoDB Compass** (opcional, es la interfaz gráfica)

Verificar que el servicio esté corriendo:
```powershell
Get-Service MongoDB
# Debe mostrar Status: Running
```

Si no está corriendo:
```powershell
Start-Service MongoDB
Set-Service MongoDB -StartupType Automatic
```

---

## Paso 4: Instalar Git

1. Descargar desde: https://git-scm.com/download/win
2. Instalar con opciones por defecto

Verificar:
```powershell
git --version
```

---

## Paso 5: Crear Estructura de Directorios

```powershell
# Crear directorio principal
New-Item -Path "C:\inetpub\jotuns-th" -ItemType Directory -Force

# Crear directorios de almacenamiento
New-Item -Path "C:\inetpub\jotuns-th\storage\bills" -ItemType Directory -Force
New-Item -Path "C:\inetpub\jotuns-th\storage\documents" -ItemType Directory -Force
New-Item -Path "C:\inetpub\jotuns-th\storage\vouchers" -ItemType Directory -Force
New-Item -Path "C:\inetpub\jotuns-th\storage\contracts" -ItemType Directory -Force
```

---

## Paso 6: Descargar el Código

```powershell
cd C:\inetpub\jotuns-th
git clone https://github.com/cristian138/th_academy.git .
```

Si ya tiene el repositorio y quiere actualizar:
```powershell
cd C:\inetpub\jotuns-th
git fetch origin
git reset --hard origin/main
```

---

## Paso 7: Configurar el Backend (FastAPI)

### 7.1 Crear entorno virtual e instalar dependencias

```powershell
cd C:\inetpub\jotuns-th\backend

# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
.\venv\Scripts\Activate.ps1

# Instalar dependencias
pip install -r requirements.txt
```

### 7.2 Crear archivo de configuración `.env`

Crear el archivo `C:\inetpub\jotuns-th\backend\.env` con el siguiente contenido:

```env
MONGO_URL=mongodb://localhost:27017
DB_NAME=jotuns_talento_humano
JWT_SECRET_KEY=CAMBIAR_POR_UNA_CLAVE_SECRETA_LARGA
JWT_ALGORITHM=HS256
CORS_ORIGINS=https://th.academiajotuns.com,http://localhost:3000
SMTP_SERVER=smtp.office365.com
SMTP_PORT=587
SMTP_USER=th.system@academiajotuns.com
SMTP_PASSWORD=SU_CONTRASEÑA_SMTP
SMTP_FROM=th.system@academiajotuns.com
SMTP_FROM_NAME=Sistema Talento Humano - Jotuns Club
STORAGE_TYPE=local
```

Generar clave secreta JWT:
```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```
Copiar el resultado y reemplazar `CAMBIAR_POR_UNA_CLAVE_SECRETA_LARGA` en el `.env`.

### 7.3 Verificar que el backend funciona

```powershell
cd C:\inetpub\jotuns-th\backend
.\venv\Scripts\Activate.ps1
uvicorn server:app --host 0.0.0.0 --port 8002
```

En otra ventana de PowerShell:
```powershell
Invoke-RestMethod http://localhost:8002/api/health
# Debe mostrar: status=healthy
```

Detener con Ctrl+C después de verificar.

---

## Paso 8: Compilar el Frontend (React)

### 8.1 Instalar dependencias y compilar

```powershell
cd C:\inetpub\jotuns-th\frontend

# Crear archivo .env
Set-Content -Path ".env" -Value "REACT_APP_BACKEND_URL=https://th.academiajotuns.com"

# Instalar dependencias
npm install

# Compilar para producción
npm run build
```

Esto generará la carpeta `C:\inetpub\jotuns-th\frontend\build` con los archivos estáticos.

---

## Paso 9: Instalar el Backend como Servicio de Windows (NSSM)

Para que el backend se ejecute automáticamente al iniciar Windows, usamos NSSM (Non-Sucking Service Manager).

### 9.1 Instalar NSSM

1. Descargar desde: https://nssm.cc/download
2. Extraer el ZIP
3. Copiar `nssm.exe` (de la carpeta `win64`) a `C:\Windows\System32\`

### 9.2 Crear el servicio

```powershell
nssm install JotunsBackend "C:\inetpub\jotuns-th\backend\venv\Scripts\uvicorn.exe"
nssm set JotunsBackend AppParameters "server:app --host 127.0.0.1 --port 8002"
nssm set JotunsBackend AppDirectory "C:\inetpub\jotuns-th\backend"
nssm set JotunsBackend DisplayName "Jotuns TH - Backend API"
nssm set JotunsBackend Description "Backend FastAPI para Sistema de Talento Humano"
nssm set JotunsBackend Start SERVICE_AUTO_START
nssm set JotunsBackend AppStdout "C:\inetpub\jotuns-th\logs\backend-out.log"
nssm set JotunsBackend AppStderr "C:\inetpub\jotuns-th\logs\backend-err.log"
nssm set JotunsBackend AppRotateFiles 1
nssm set JotunsBackend AppRotateBytes 5000000
```

### 9.3 Crear directorio de logs e iniciar el servicio

```powershell
New-Item -Path "C:\inetpub\jotuns-th\logs" -ItemType Directory -Force

# Iniciar el servicio
nssm start JotunsBackend

# Verificar estado
nssm status JotunsBackend
# Debe mostrar: SERVICE_RUNNING
```

### 9.4 Verificar

```powershell
Invoke-RestMethod http://localhost:8002/api/health
```

---

## Paso 10: Configurar IIS

### 10.1 Instalar módulos necesarios de IIS

Abrir PowerShell como Administrador:

```powershell
# Instalar URL Rewrite Module
# Descargar desde: https://www.iis.net/downloads/microsoft/url-rewrite
# Instalar el MSI descargado

# Instalar ARR (Application Request Routing)
# Descargar desde: https://www.iis.net/downloads/microsoft/application-request-routing
# Instalar el MSI descargado
```

**Descargas directas:**
- URL Rewrite: https://www.iis.net/downloads/microsoft/url-rewrite
- ARR 3.0: https://www.iis.net/downloads/microsoft/application-request-routing

Reiniciar IIS después de instalar:
```powershell
iisreset
```

### 10.2 Habilitar Proxy en ARR

1. Abrir **IIS Manager** (inetmgr)
2. Hacer clic en el **nombre del servidor** (nivel raíz, no un sitio)
3. Doble clic en **"Application Request Routing Cache"**
4. A la derecha, clic en **"Server Proxy Settings..."**
5. Marcar **"Enable proxy"**
6. Clic en **Apply**

### 10.3 Crear el Sitio Web en IIS

1. Abrir **IIS Manager**
2. Clic derecho en **"Sites"** → **"Add Website..."**
3. Configurar:
   - **Site name:** `JotunsTH`
   - **Physical path:** `C:\inetpub\jotuns-th\frontend\build`
   - **Binding:**
     - Type: `http`
     - IP: `All Unassigned`
     - Port: `80`
     - Host name: `th.academiajotuns.com`
4. Clic en **OK**

### 10.4 Configurar URL Rewrite (Reverse Proxy para API)

Crear el archivo `C:\inetpub\jotuns-th\frontend\build\web.config` con este contenido:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<configuration>
    <system.webServer>
        <rewrite>
            <rules>
                <!-- Regla 1: Reverse Proxy para API Backend -->
                <rule name="API Backend" stopProcessing="true">
                    <match url="^api/(.*)" />
                    <action type="Rewrite" url="http://127.0.0.1:8002/api/{R:1}" />
                </rule>

                <!-- Regla 2: React SPA - Redirigir todo al index.html -->
                <rule name="React Routes" stopProcessing="true">
                    <match url=".*" />
                    <conditions logicalGrouping="MatchAll">
                        <add input="{REQUEST_FILENAME}" matchType="IsFile" negate="true" />
                        <add input="{REQUEST_FILENAME}" matchType="IsDirectory" negate="true" />
                    </conditions>
                    <action type="Rewrite" url="/index.html" />
                </rule>
            </rules>
        </rewrite>

        <!-- Configurar tipos MIME -->
        <staticContent>
            <remove fileExtension=".json" />
            <mimeMap fileExtension=".json" mimeType="application/json" />
            <remove fileExtension=".woff" />
            <mimeMap fileExtension=".woff" mimeType="font/woff" />
            <remove fileExtension=".woff2" />
            <mimeMap fileExtension=".woff2" mimeType="font/woff2" />
        </staticContent>

        <!-- Tamaño máximo de archivos (50MB) -->
        <security>
            <requestFiltering>
                <requestLimits maxAllowedContentLength="52428800" />
            </requestFiltering>
        </security>

        <!-- Cache para archivos estáticos -->
        <httpProtocol>
            <customHeaders>
                <add name="X-Content-Type-Options" value="nosniff" />
            </customHeaders>
        </httpProtocol>
    </system.webServer>
</configuration>
```

### 10.5 Dar permisos a IIS sobre la carpeta de storage

```powershell
$acl = Get-Acl "C:\inetpub\jotuns-th\storage"
$rule = New-Object System.Security.AccessControl.FileSystemAccessRule("IIS_IUSRS", "FullControl", "ContainerInherit,ObjectInherit", "None", "Allow")
$acl.SetAccessRule($rule)
Set-Acl "C:\inetpub\jotuns-th\storage" $acl

# También para la carpeta de logs
$acl2 = Get-Acl "C:\inetpub\jotuns-th\logs"
$rule2 = New-Object System.Security.AccessControl.FileSystemAccessRule("IIS_IUSRS", "FullControl", "ContainerInherit,ObjectInherit", "None", "Allow")
$acl2.SetAccessRule($rule2)
Set-Acl "C:\inetpub\jotuns-th\logs" $acl2
```

### 10.6 Reiniciar IIS y verificar

```powershell
iisreset
Invoke-RestMethod http://localhost/api/health
# Debe mostrar: status=healthy
```

---

## Paso 11: Configurar SSL con win-acme (Let's Encrypt)

**Requisito previo:** El dominio `th.academiajotuns.com` debe apuntar a la IP del servidor Windows.

### 11.1 Descargar win-acme

1. Ir a: https://www.win-acme.com/
2. Descargar la versión más reciente (64-bit, pluggable)
3. Extraer en: `C:\tools\win-acme\`

### 11.2 Ejecutar win-acme

```powershell
cd C:\tools\win-acme
.\wacs.exe
```

Seguir el asistente interactivo:
1. Seleccionar **N** (Create certificate with default settings)
2. Seleccionar el sitio **JotunsTH**
3. Confirmar el dominio **th.academiajotuns.com**
4. win-acme configurará automáticamente:
   - El certificado SSL
   - El binding HTTPS en IIS
   - La renovación automática como tarea programada

### 11.3 Forzar HTTPS (Redirigir HTTP → HTTPS)

Agregar esta regla al inicio de las `<rules>` en el `web.config`:

```xml
<!-- Regla 0: Forzar HTTPS -->
<rule name="Force HTTPS" stopProcessing="true">
    <match url="(.*)" />
    <conditions>
        <add input="{HTTPS}" pattern="off" />
    </conditions>
    <action type="Redirect" url="https://{HTTP_HOST}/{R:1}" redirectType="Permanent" />
</rule>
```

El `web.config` completo con HTTPS queda así:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<configuration>
    <system.webServer>
        <rewrite>
            <rules>
                <!-- Regla 0: Forzar HTTPS -->
                <rule name="Force HTTPS" stopProcessing="true">
                    <match url="(.*)" />
                    <conditions>
                        <add input="{HTTPS}" pattern="off" />
                    </conditions>
                    <action type="Redirect" url="https://{HTTP_HOST}/{R:1}" redirectType="Permanent" />
                </rule>

                <!-- Regla 1: Reverse Proxy para API Backend -->
                <rule name="API Backend" stopProcessing="true">
                    <match url="^api/(.*)" />
                    <action type="Rewrite" url="http://127.0.0.1:8002/api/{R:1}" />
                </rule>

                <!-- Regla 2: React SPA -->
                <rule name="React Routes" stopProcessing="true">
                    <match url=".*" />
                    <conditions logicalGrouping="MatchAll">
                        <add input="{REQUEST_FILENAME}" matchType="IsFile" negate="true" />
                        <add input="{REQUEST_FILENAME}" matchType="IsDirectory" negate="true" />
                    </conditions>
                    <action type="Rewrite" url="/index.html" />
                </rule>
            </rules>
        </rewrite>

        <staticContent>
            <remove fileExtension=".json" />
            <mimeMap fileExtension=".json" mimeType="application/json" />
            <remove fileExtension=".woff" />
            <mimeMap fileExtension=".woff" mimeType="font/woff" />
            <remove fileExtension=".woff2" />
            <mimeMap fileExtension=".woff2" mimeType="font/woff2" />
        </staticContent>

        <security>
            <requestFiltering>
                <requestLimits maxAllowedContentLength="52428800" />
            </requestFiltering>
        </security>

        <httpProtocol>
            <customHeaders>
                <add name="X-Content-Type-Options" value="nosniff" />
            </customHeaders>
        </httpProtocol>
    </system.webServer>
</configuration>
```

---

## Paso 12: Crear Usuario Administrador

```powershell
cd C:\inetpub\jotuns-th\backend
.\venv\Scripts\Activate.ps1

python -c @"
import asyncio
from database import connect_db, get_database
from services.auth_service import auth_service
from datetime import datetime, timezone
import uuid

async def create_admin():
    await connect_db()
    db = await get_database()
    existing = await db.users.find_one({'email': 'cristian.prieto@academiajotuns.com'})
    if existing:
        print('El usuario admin ya existe')
        return
    admin = {
        'id': str(uuid.uuid4()),
        'email': 'cristian.prieto@academiajotuns.com',
        'name': 'CRISTIAN CAMILO PRIETO ROA',
        'role': 'superadmin',
        'hashed_password': auth_service.hash_password('Cristian009*'),
        'is_active': True,
        'created_at': datetime.now(timezone.utc),
        'updated_at': datetime.now(timezone.utc)
    }
    await db.users.insert_one(admin)
    print(f'Usuario admin creado: {admin["email"]}')

asyncio.run(create_admin())
"@
```

---

## Paso 13: Migrar la Base de Datos desde el VPS Linux

### En el VPS Linux (exportar):

```bash
mongodump --db jotuns_talento_humano --out /tmp/mongo_backup
```

Descargar la carpeta `/tmp/mongo_backup/jotuns_talento_humano` a su PC local usando SCP o WinSCP.

### En el Windows Server (importar):

1. Copiar la carpeta de backup al servidor, por ejemplo: `C:\temp\mongo_backup\jotuns_talento_humano`

2. Ejecutar:
```powershell
mongorestore --db jotuns_talento_humano C:\temp\mongo_backup\jotuns_talento_humano
```

### Migrar archivos subidos

Copiar la carpeta `/var/www/jotuns-th/storage` del VPS Linux a `C:\inetpub\jotuns-th\storage\` en el Windows Server usando WinSCP o similar.

---

## Paso 14: Configurar Firewall de Windows

```powershell
# Permitir HTTP
New-NetFirewallRule -DisplayName "HTTP" -Direction Inbound -Protocol TCP -LocalPort 80 -Action Allow

# Permitir HTTPS
New-NetFirewallRule -DisplayName "HTTPS" -Direction Inbound -Protocol TCP -LocalPort 443 -Action Allow
```

---

## Paso 15: Verificar la Instalación

```powershell
# Verificar servicios
Get-Service MongoDB
nssm status JotunsBackend

# Verificar backend
Invoke-RestMethod http://localhost:8002/api/health

# Verificar integración con presupuesto
Invoke-RestMethod http://localhost:8002/api/integration/health

# Verificar IIS
Invoke-RestMethod http://localhost/api/health
```

Abrir en el navegador: **https://th.academiajotuns.com**

---

## Comandos de Mantenimiento

### Ver logs del backend
```powershell
Get-Content "C:\inetpub\jotuns-th\logs\backend-err.log" -Tail 50
Get-Content "C:\inetpub\jotuns-th\logs\backend-out.log" -Tail 50
```

### Reiniciar servicios
```powershell
# Backend
nssm restart JotunsBackend

# IIS
iisreset

# MongoDB
Restart-Service MongoDB
```

### Ver estado de servicios
```powershell
nssm status JotunsBackend
Get-Service MongoDB
Get-Service W3SVC
```

### Backup de MongoDB
```powershell
$fecha = Get-Date -Format "yyyyMMdd"
mongodump --db jotuns_talento_humano --out "C:\backups\mongodb\$fecha"
```

---

## Actualizar la Aplicación

```powershell
cd C:\inetpub\jotuns-th

# Obtener últimos cambios
git fetch origin
git reset --hard origin/main

# Backend
cd backend
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
nssm restart JotunsBackend

# Frontend
cd ..\frontend
npm install
npm run build

# Reiniciar IIS
iisreset

Write-Host "Actualización completada" -ForegroundColor Green
```

---

## Solución de Problemas

### El backend no inicia
```powershell
# Ver logs
Get-Content "C:\inetpub\jotuns-th\logs\backend-err.log" -Tail 50

# Verificar MongoDB
Get-Service MongoDB

# Probar manualmente
cd C:\inetpub\jotuns-th\backend
.\venv\Scripts\Activate.ps1
uvicorn server:app --host 127.0.0.1 --port 8002
```

### Error 502 Bad Gateway en IIS
```powershell
# Verificar que el backend responde
Invoke-RestMethod http://localhost:8002/api/health

# Reiniciar backend
nssm restart JotunsBackend

# Verificar que ARR está habilitado en IIS Manager
# Servidor > Application Request Routing > Server Proxy Settings > Enable proxy
```

### Las rutas de React dan error 404
```powershell
# Verificar que URL Rewrite está instalado
Get-WebGlobalModule | Where-Object { $_.Name -like "*Rewrite*" }

# Verificar que web.config existe
Test-Path "C:\inetpub\jotuns-th\frontend\build\web.config"
```

### Problemas de permisos
```powershell
# Dar permisos completos a IIS_IUSRS
icacls "C:\inetpub\jotuns-th\storage" /grant "IIS_IUSRS:(OI)(CI)F" /T
icacls "C:\inetpub\jotuns-th\logs" /grant "IIS_IUSRS:(OI)(CI)F" /T
```

### Certificado SSL no se renueva
```powershell
# Ejecutar renovación manual
cd C:\tools\win-acme
.\wacs.exe --renew --force
```

---

## Resumen de Rutas (Windows)

| Elemento | Ruta |
|----------|------|
| Aplicación | `C:\inetpub\jotuns-th` |
| Backend | `C:\inetpub\jotuns-th\backend` |
| Frontend Build | `C:\inetpub\jotuns-th\frontend\build` |
| web.config | `C:\inetpub\jotuns-th\frontend\build\web.config` |
| Archivos subidos | `C:\inetpub\jotuns-th\storage` |
| Logs Backend | `C:\inetpub\jotuns-th\logs` |
| NSSM | `C:\Windows\System32\nssm.exe` |
| win-acme | `C:\tools\win-acme` |
| MongoDB datos | `C:\Program Files\MongoDB\Server\7.0\data` |

---

## Orden de Instalación (Resumen)

1. Python 3.11 (con PATH)
2. Node.js 18+
3. Git
4. MongoDB 7.0 (como servicio)
5. Descargar código (git clone)
6. Backend: venv + pip install + .env
7. Frontend: npm install + npm run build
8. NSSM: instalar backend como servicio
9. IIS: URL Rewrite + ARR + sitio web + web.config
10. SSL: win-acme
11. Migrar base de datos y archivos desde VPS Linux
12. Crear usuario admin
13. Firewall
14. Verificar

---

**Dominio:** https://th.academiajotuns.com
**Soporte:** Contacte al equipo de desarrollo
