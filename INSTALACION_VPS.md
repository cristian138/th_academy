# Guía de Instalación en VPS
## Sistema de Talento Humano - Academia Jotuns Club SAS
## Dominio: th.academiajotuns.com

### Requisitos del Servidor
- **Sistema Operativo:** Ubuntu 20.04/22.04 LTS
- **RAM:** Mínimo 2GB (recomendado 4GB)
- **Disco:** Mínimo 20GB
- **CPU:** 1-2 cores

---

## Paso 1: Actualizar el Sistema

```bash
sudo apt update && sudo apt upgrade -y
```

---

## Paso 2: Instalar Dependencias del Sistema

```bash
# Instalar herramientas básicas
sudo apt install -y curl git wget unzip software-properties-common

# Instalar Python 3.11
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev python3-pip

# Instalar Node.js 18.x
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Instalar yarn
npm install -g yarn

# Instalar Nginx
sudo apt install -y nginx

# Instalar Supervisor
sudo apt install -y supervisor
```

---

## Paso 3: Instalar MongoDB

```bash
# Importar la clave GPG
curl -fsSL https://pgp.mongodb.com/server-7.0.asc | \
   sudo gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg --dearmor

# Agregar el repositorio (Ubuntu 22.04)
echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | \
   sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list

# Instalar MongoDB
sudo apt update
sudo apt install -y mongodb-org

# Iniciar y habilitar MongoDB
sudo systemctl start mongod
sudo systemctl enable mongod

# Verificar que está corriendo
sudo systemctl status mongod
```

---

## Paso 4: Crear Directorio de la Aplicación

```bash
# Crear directorio de la aplicación
sudo mkdir -p /var/www/jotuns-th
sudo chown www-data:www-data /var/www/jotuns-th

# Crear directorio para archivos subidos
sudo mkdir -p /var/www/jotuns-th/storage/{bills,documents,vouchers,contracts}
sudo chown -R www-data:www-data /var/www/jotuns-th/storage
```

---

## Paso 5: Subir el Código de la Aplicación

**Opción A: Usando Git (recomendado)**
```bash
cd /var/www/jotuns-th
sudo -u www-data git clone https://github.com/cristian138/th_academy.git .
```

**Opción B: Usando SCP desde su máquina local**
```bash
# Desde su máquina local
scp -r ./backend ./frontend usuario@su-servidor:/var/www/jotuns-th/

# Luego en el servidor, ajustar permisos
sudo chown -R www-data:www-data /var/www/jotuns-th
```

---

## Paso 6: Configurar el Backend

```bash
# Cambiar al directorio del backend
cd /var/www/jotuns-th/backend

# Crear entorno virtual
sudo -u www-data python3.11 -m venv venv

# Activar entorno virtual
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### Crear archivo de configuración `.env`

```bash
sudo nano /var/www/jotuns-th/backend/.env
```

Contenido del archivo:
```env
# MongoDB
MONGO_URL=mongodb://localhost:27017
DB_NAME=jotuns_talento_humano

# JWT - IMPORTANTE: Cambiar esta clave
JWT_SECRET_KEY=GENERAR_UNA_CLAVE_SECRETA_LARGA_AQUI
JWT_ALGORITHM=HS256

# CORS
CORS_ORIGINS=https://th.academiajotuns.com,http://localhost:3000

# SMTP (Email) - Configurar con sus credenciales
SMTP_SERVER=smtp.office365.com
SMTP_PORT=587
SMTP_USER=th.system@academiajotuns.com
SMTP_PASSWORD=SU_CONTRASEÑA_SMTP
SMTP_FROM=th.system@academiajotuns.com
SMTP_FROM_NAME=Sistema Talento Humano - Jotuns Club

# Storage
STORAGE_TYPE=local
```

**Generar clave secreta JWT:**
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

---

## Paso 7: Configurar el Frontend

```bash
cd /var/www/jotuns-th/frontend

# Instalar dependencias
sudo -u www-data yarn install
```

### Crear archivo de configuración `.env`

```bash
sudo nano /var/www/jotuns-th/frontend/.env
```

Contenido:
```env
REACT_APP_BACKEND_URL=https://th.academiajotuns.com
```

### Compilar el frontend para producción

```bash
sudo -u www-data yarn build
```

---

## Paso 8: Configurar Supervisor

### Backend Service

```bash
sudo nano /etc/supervisor/conf.d/jotuns-backend.conf
```

Contenido:
```ini
[program:jotuns-backend]
directory=/var/www/jotuns-th/backend
command=/var/www/jotuns-th/backend/venv/bin/uvicorn server:app --host 0.0.0.0 --port 8001
user=www-data
autostart=true
autorestart=true
stderr_logfile=/var/log/supervisor/jotuns-backend.err.log
stdout_logfile=/var/log/supervisor/jotuns-backend.out.log
environment=PATH="/var/www/jotuns-th/backend/venv/bin"
```

### Recargar Supervisor

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start jotuns-backend
```

### Verificar que está corriendo

```bash
sudo supervisorctl status jotuns-backend
curl http://localhost:8001/api/health
```

---

## Paso 9: Configurar Nginx con SSL

### Primero, configurar Nginx sin SSL para obtener el certificado

```bash
sudo nano /etc/nginx/sites-available/jotuns-th
```

Contenido inicial (sin SSL):
```nginx
server {
    listen 80;
    server_name th.academiajotuns.com;

    root /var/www/jotuns-th/frontend/build;
    index index.html;

    client_max_body_size 50M;

    location /api {
        proxy_pass http://127.0.0.1:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
    }

    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

### Activar el sitio y obtener certificado SSL

```bash
# Activar sitio
sudo ln -s /etc/nginx/sites-available/jotuns-th /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx

# Instalar Certbot
sudo apt install -y certbot python3-certbot-nginx

# Obtener certificado SSL (asegúrese que el dominio apunte al servidor)
sudo certbot --nginx -d th.academiajotuns.com
```

### Configuración final con SSL (Certbot la actualiza automáticamente)

Después de ejecutar Certbot, el archivo se actualizará automáticamente. Debería verse así:

```nginx
server {
    listen 80;
    server_name th.academiajotuns.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name th.academiajotuns.com;

    # SSL (Let's Encrypt - generado por Certbot)
    ssl_certificate /etc/letsencrypt/live/th.academiajotuns.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/th.academiajotuns.com/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    # Frontend
    root /var/www/jotuns-th/frontend/build;
    index index.html;

    # Tamaño máximo de archivos (50MB)
    client_max_body_size 50M;

    # API Backend
    location /api {
        proxy_pass http://127.0.0.1:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }

    # Frontend SPA
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Cache para archivos estáticos
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

---

## Paso 10: Crear Usuario Administrador

```bash
cd /var/www/jotuns-th/backend
source venv/bin/activate

python3 << 'EOF'
import asyncio
from database import connect_db, get_database
from services.auth_service import auth_service
from datetime import datetime, timezone
import uuid

async def create_admin():
    await connect_db()
    db = await get_database()
    
    # Verificar si ya existe
    existing = await db.users.find_one({"email": "admin@academiajotuns.com"})
    if existing:
        print("El usuario admin ya existe")
        return
    
    admin = {
        "id": str(uuid.uuid4()),
        "email": "admin@academiajotuns.com",
        "name": "Administrador",
        "role": "superadmin",
        "hashed_password": auth_service.hash_password("CambiarContraseña123!"),
        "is_active": True,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }
    
    await db.users.insert_one(admin)
    print(f"✓ Usuario admin creado: {admin['email']}")
    print("  Contraseña temporal: CambiarContraseña123!")
    print("  ¡IMPORTANTE: Cambie esta contraseña inmediatamente!")

asyncio.run(create_admin())
EOF
```

---

## Paso 11: Configurar Firewall

```bash
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw enable
sudo ufw status
```

---

## Paso 12: Verificar la Instalación

```bash
# Verificar backend
curl https://th.academiajotuns.com/api/health

# Verificar servicios
sudo supervisorctl status
sudo systemctl status mongod
sudo systemctl status nginx
```

Abrir en el navegador: **https://th.academiajotuns.com**

---

## Comandos Útiles de Mantenimiento

```bash
# Ver logs del backend
sudo tail -f /var/log/supervisor/jotuns-backend.out.log
sudo tail -f /var/log/supervisor/jotuns-backend.err.log

# Ver logs de Nginx
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Reiniciar servicios
sudo supervisorctl restart jotuns-backend
sudo systemctl restart nginx
sudo systemctl restart mongod

# Ver estado de servicios
sudo supervisorctl status
sudo systemctl status mongod
sudo systemctl status nginx

# Backup de MongoDB
mongodump --db jotuns_talento_humano --out /var/backups/mongodb/$(date +%Y%m%d)

# Restaurar MongoDB
mongorestore --db jotuns_talento_humano /var/backups/mongodb/FECHA/jotuns_talento_humano
```

---

## Actualizar la Aplicación

```bash
cd /var/www/jotuns-th

# Obtener últimos cambios
sudo -u www-data git pull

# Backend
cd backend
source venv/bin/activate
pip install -r requirements.txt
sudo supervisorctl restart jotuns-backend

# Frontend
cd ../frontend
sudo -u www-data yarn install
sudo -u www-data yarn build

# Reiniciar Nginx (opcional)
sudo systemctl reload nginx
```

---

## Renovación Automática de SSL

Certbot configura automáticamente la renovación. Verificar:

```bash
# Probar renovación
sudo certbot renew --dry-run

# Ver timer de renovación
sudo systemctl status certbot.timer
```

---

## Solución de Problemas

### El backend no inicia
```bash
sudo tail -50 /var/log/supervisor/jotuns-backend.err.log
sudo systemctl status mongod
```

### Error 502 Bad Gateway
```bash
curl http://localhost:8001/api/health
sudo supervisorctl restart jotuns-backend
```

### Problemas de permisos
```bash
sudo chown -R www-data:www-data /var/www/jotuns-th
sudo chmod -R 755 /var/www/jotuns-th/storage
```

### Certificado SSL no funciona
```bash
sudo certbot --nginx -d th.academiajotuns.com --force-renewal
```

---

## Resumen de Rutas Importantes

| Elemento | Ruta |
|----------|------|
| Aplicación | `/var/www/jotuns-th` |
| Backend | `/var/www/jotuns-th/backend` |
| Frontend Build | `/var/www/jotuns-th/frontend/build` |
| Archivos subidos | `/var/www/jotuns-th/storage` |
| Config Nginx | `/etc/nginx/sites-available/jotuns-th` |
| Config Supervisor | `/etc/supervisor/conf.d/jotuns-backend.conf` |
| Logs Backend | `/var/log/supervisor/jotuns-backend.*.log` |
| Logs Nginx | `/var/log/nginx/*.log` |
| SSL Certificados | `/etc/letsencrypt/live/th.academiajotuns.com/` |

---

## Credenciales Iniciales

| Usuario | Email | Contraseña |
|---------|-------|------------|
| Admin | admin@academiajotuns.com | CambiarContraseña123! |

**⚠️ IMPORTANTE:** Cambie la contraseña del administrador inmediatamente después del primer inicio de sesión.

---

**Dominio:** https://th.academiajotuns.com
**Soporte:** Contacte al equipo de desarrollo
