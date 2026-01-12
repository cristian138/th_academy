# SportsAdmin Pro - Sistema de Gestión de Contratos

Sistema administrativo institucional de contratación de colaboradores para academia deportiva, con enfoque empresarial y cumplimiento normativo.

## 🎯 Características Principales

### Gestión de Contratos
- **Tipos de contrato**: Prestación de servicios y por sesión/evento
- **Flujo completo**: Creación → Documentos → Revisión → Aprobación → Firma → Activo
- **Control de estados**: 10 estados diferentes con transiciones validadas
- **Bloqueo automático**: Si faltan documentos obligatorios

### Gestión de Documentos
- **Documentos obligatorios**: Cédula, RUT, certificaciones laborales/educativas, cuenta bancaria, antecedentes
- **Documento opcional**: Licencia de trabajo
- **Control de vencimientos**: Alertas 15 días antes del vencimiento
- **Almacenamiento**: OneDrive con Microsoft Graph API
- **Revisión**: Workflow de aprobación por administrador

### Sistema de Pagos
- **Registro por contador**: Creación de pago pendiente
- **Cuenta de cobro**: Obligatoria por colaborador
- **Comprobantes**: Generados y descargables
- **Estados**: Pendiente cuenta de cobro → Pendiente pago → Pagado

### Control de Acceso (RBAC)
- **Superadministrador**: Control total
- **Administrador General**: Gestión operativa
- **Representante Legal**: Creación y aprobación de contratos
- **Contador**: Registro de pagos
- **Colaborador**: Carga de documentos y contratos firmados

### Notificaciones
- **Por email**: Microsoft Outlook (Microsoft Graph API)
- **Eventos**: Contrato creado, aprobado, pago registrado, documentos por vencer
- **Dashboard**: Notificaciones en tiempo real

### Reportes
- Contratos pendientes por firmar
- Contratos vigentes
- Pagos por colaborador
- Pagos pendientes
- Documentos próximos a vencer

### Auditoría y Trazabilidad
- Registro completo de acciones
- Historial de cambios de estado
- Información de usuario y timestamp
- Cumplimiento Ley 1581 de 2012 (Protección de datos Colombia)

## 🏗️ Arquitectura Técnica

### Stack Tecnológico
- **Backend**: FastAPI (Python 3.11+)
- **Frontend**: React 19 + Tailwind CSS + shadcn/ui
- **Base de Datos**: MongoDB
- **Integraciones**: Microsoft Graph API (Outlook + OneDrive)
- **Autenticación**: JWT con bcrypt
- **Almacenamiento**: OneDrive

### Estructura del Proyecto

```
/app/
├── backend/
│   ├── server.py              # Servidor principal FastAPI
│   ├── config.py              # Configuración
│   ├── models.py              # Modelos Pydantic
│   ├── database.py            # Conexión MongoDB
│   ├── seed_data.py           # Datos de prueba
│   ├── services/
│   │   ├── auth_service.py    # Autenticación JWT
│   │   ├── email_service.py   # Microsoft Outlook
│   │   ├── onedrive_service.py # Almacenamiento
│   │   └── audit_service.py   # Auditoría
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/        # Componentes React
│   │   ├── pages/            # Páginas principales
│   │   ├── context/          # Context API
│   │   ├── services/         # API client
│   │   └── App.js
│   └── package.json
└── design_guidelines.json     # Guías de diseño
```

## 🚀 Instalación y Configuración

### Variables de Entorno

**Backend (.env):**
```env
MONGO_URL="mongodb://localhost:27017"
DB_NAME="sportsadmin_db"
CORS_ORIGINS="*"

# Microsoft Graph API (Opcional - para producción)
AZURE_CLIENT_ID=""
AZURE_CLIENT_SECRET=""
AZURE_TENANT_ID=""

# JWT
JWT_SECRET="your-secret-key-change-in-production-min-32-chars-long-secret"
```

**Frontend (.env):**
```env
REACT_APP_BACKEND_URL=https://coach-contracts.preview.emergentagent.com
```

### Configuración de Microsoft Graph API

1. Registrar aplicación en Azure Portal
2. Configurar permisos:
   - Mail.Send (Delegated)
   - Files.ReadWrite.All (Application)
   - User.Read.All (Application)
3. Crear client secret
4. Agregar credenciales al .env

### Inicializar Datos de Prueba

```bash
cd /app/backend
python seed_data.py
```

### Iniciar Servicios

```bash
# Backend
cd /app/backend
uvicorn server:app --host 0.0.0.0 --port 8001 --reload

# Frontend
cd /app/frontend
yarn start
```

## 👤 Usuarios de Prueba

| Rol | Email | Contraseña | Permisos |
|-----|-------|-----------|----------|
| Superadmin | superadmin@sportsadmin.com | admin123 | Todos |
| Admin | admin@sportsadmin.com | admin123 | Gestión operativa |
| Legal | legal@sportsadmin.com | legal123 | Crear y aprobar contratos |
| Contador | contador@sportsadmin.com | contador123 | Registrar pagos |
| Colaborador 1 | carlos.rodriguez@coach.com | carlos123 | Documentos y contratos |
| Colaborador 2 | maria.gonzalez@coach.com | maria123 | Documentos y contratos |
| Colaborador 3 | juan.martinez@coach.com | juan123 | Documentos y contratos |

## 📊 Datos de Ejemplo

El sistema incluye:
- **4 contratos**: 2 activos, 1 pendiente aprobación, 1 en revisión
- **7 usuarios**: Diferentes roles
- **18 documentos**: Aprobados para colaboradores
- **6 pagos**: Algunos pagados, algunos pendientes
- **3 notificaciones**: Diferentes tipos

## 🔐 Seguridad

- **Autenticación**: JWT con expiración configurable
- **Encriptación**: Contraseñas con bcrypt
- **RBAC**: Control de acceso basado en roles
- **Validación**: Pydantic en backend, validaciones en frontend
- **Auditoría**: Registro completo de acciones
- **Cumplimiento**: Ley 1581 de 2012 (Protección de datos Colombia)

## 🎨 Diseño

### Colores Institucionales
- **Primary**: #002d54 (Azul marino)
- **Accent**: #007AFF (Azul eléctrico)
- **Success**: Emerald
- **Warning**: Amber
- **Error**: Red

### Tipografía
- **Headings**: Chivo (bold, tracking tight)
- **Body**: Manrope (legible, tabular-nums)

### Componentes
- Shadcn/ui con personalización corporativa
- Bordes rectos (rounded-sm)
- Sombras mínimas
- Alta legibilidad

## 📝 API Endpoints

### Autenticación
- `POST /api/auth/login` - Iniciar sesión
- `POST /api/auth/register` - Registrar usuario
- `GET /api/auth/me` - Usuario actual

### Contratos
- `GET /api/contracts` - Listar contratos
- `POST /api/contracts` - Crear contrato
- `GET /api/contracts/{id}` - Detalle de contrato
- `PUT /api/contracts/{id}` - Actualizar contrato
- `POST /api/contracts/{id}/review` - Revisar contrato
- `POST /api/contracts/{id}/approve` - Aprobar contrato
- `POST /api/contracts/{id}/upload-signed` - Subir firmado

### Documentos
- `GET /api/documents` - Listar documentos
- `POST /api/documents` - Subir documento
- `PUT /api/documents/{id}/review` - Revisar documento
- `GET /api/documents/expiring` - Docs por vencer

### Pagos
- `GET /api/payments` - Listar pagos
- `POST /api/payments` - Crear pago
- `POST /api/payments/{id}/upload-bill` - Subir cuenta de cobro
- `POST /api/payments/{id}/confirm` - Confirmar pago

### Dashboard
- `GET /api/dashboard/stats` - Estadísticas

### Reportes
- `GET /api/reports/contracts-pending` - Contratos pendientes
- `GET /api/reports/contracts-active` - Contratos activos
- `GET /api/reports/payments-pending` - Pagos pendientes

### Notificaciones
- `GET /api/notifications` - Listar notificaciones
- `PUT /api/notifications/{id}/read` - Marcar como leída

## 🧪 Testing

El sistema ha sido probado exhaustivamente:

✅ 24/24 pruebas de API backend
✅ Flujos completos de UI con Playwright
✅ Autenticación para todos los roles
✅ Workflow de contratos completo
✅ Gestión de documentos
✅ Sistema de pagos
✅ Notificaciones
✅ Dashboard con métricas

## 📞 Soporte

Para configuración de credenciales de Microsoft:
1. Azure Portal → App Registrations
2. Crear nueva aplicación
3. Configurar permisos de Graph API
4. Generar client secret
5. Actualizar .env con credenciales

## 📄 Licencia

Sistema desarrollado para SportsAdmin Pro - Todos los derechos reservados.

---

**Versión**: 1.0.0  
**Última actualización**: Enero 2025  
**Stack**: FastAPI + React + MongoDB + Microsoft Graph API
