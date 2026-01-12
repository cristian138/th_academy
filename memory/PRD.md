# PRD - Sistema de Gestión de Talento Humano
## Academia Jotuns Club SAS

### Problema Original
Sistema administrativo para una academia deportiva para gestionar la contratación de colaboradores con los siguientes requisitos:

1. **Gestión de Contratos:** Para servicios y eventos, con flujo de trabajo: creación → carga de documentos → revisión → aprobación → firma → archivo.
2. **Documentos:** Gestión de documentos obligatorios (cédula, RUT, etc.) y opcionales.
3. **Usuarios y Roles (RBAC):** Superadministrador, Administrador General, Representante Legal, Contador, Colaborador.
4. **Pagos:** Registro de pagos vinculado a cuentas de cobro creadas por el colaborador.
5. **Notificaciones:** Envío de correos electrónicos en puntos clave.
6. **Reportes:** Contratos pendientes, vigentes, pagos, etc.
7. **Seguridad:** Cumplimiento de ley de protección de datos, cifrado, auditoría.
8. **Branding:** Logo, colores (#002d54) y nombre de "Talento Humano | Academia Jotuns Club SAS".

---

### Arquitectura Técnica
- **Backend:** FastAPI (Python) + MongoDB
- **Frontend:** React + Tailwind CSS + Shadcn/UI
- **Autenticación:** JWT con RBAC
- **Almacenamiento:** Sistema de archivos local (`/app/storage/`)
- **Notificaciones:** SMTP (Microsoft 365)

---

### Funcionalidades Implementadas

#### ✅ Autenticación y Autorización
- Login con JWT
- Control de acceso basado en roles (RBAC)
- Protección de rutas en frontend y backend

#### ✅ Gestión de Usuarios
- Creación de usuarios por admin
- Listado y actualización de usuarios
- Roles: superadmin, admin, legal_rep, accountant, collaborator

#### ✅ Gestión de Contratos
- Creación de contratos (por representante legal)
- Flujo de estados: draft → pending_documents → under_review → pending_approval → approved → active
- Visualización de contratos por rol
- Carga de contrato firmado

#### ✅ Gestión de Documentos
- Carga de documentos obligatorios (cédula, RUT, certificaciones, etc.)
- Revisión y aprobación de documentos
- Alertas de documentos por vencer

#### ✅ Flujo de Pagos (Cuentas de Cobro)
- **Colaborador:** Crear cuenta de cobro, subir PDF
- **Contador:** Ver, aprobar o rechazar cuentas de cobro
- **Rechazo:** Motivo del rechazo visible para colaborador
- **Reenvío:** Colaborador puede corregir y resubir cuenta rechazada
- **Comprobante:** Contador genera comprobante de pago

#### ✅ Dashboard
- Estadísticas por rol
- Vista de contratos, documentos y pagos pendientes

#### ✅ Notificaciones
- Sistema de notificaciones en la aplicación
- Envío de correos (requiere configuración SMTP del usuario)

#### ✅ Reportes
- Contratos pendientes de firma
- Contratos activos
- Pagos pendientes

#### ✅ Auditoría
- Registro de todas las acciones importantes
- Trazabilidad de cambios

---

### Estado de Servicios Externos

| Servicio | Estado | Notas |
|----------|--------|-------|
| MongoDB | ✅ Funcionando | Base de datos local |
| Almacenamiento | ✅ Local | Archivos en `/app/storage/` |
| Email SMTP | ⚠️ Bloqueado | Requiere configuración del tenant de Microsoft 365 |

---

### Pendientes (Backlog)

#### P1 - Alta Prioridad
- **Habilitar SMTP:** El usuario debe habilitar autenticación SMTP en Microsoft 365 siguiendo `/app/HABILITAR_SMTP.md`

#### P2 - Media Prioridad
- **Migración a SharePoint/OneDrive:** Opcional si se resuelven permisos de API
- **Refactorización de server.py:** Dividir en módulos (routes/contracts.py, routes/payments.py, etc.)

#### P3 - Baja Prioridad
- Exportación de reportes a Excel/PDF
- Dashboard con gráficos avanzados
- Notificaciones push

---

### Credenciales de Prueba
| Usuario | Email | Password | Rol |
|---------|-------|----------|-----|
| Colaborador | colaborador@test.com | password | collaborator |
| Contador | contador@test.com | password | accountant |
| Admin | admin@test.com | password | admin |

---

### Archivos de Referencia Importantes
- `/app/backend/server.py` - API principal
- `/app/frontend/src/pages/PaymentsPage.js` - Flujo de pagos
- `/app/backend/services/storage_service.py` - Almacenamiento de archivos
- `/app/backend/services/email_service.py` - Servicio de correo
- `/app/HABILITAR_SMTP.md` - Instrucciones para configurar SMTP

---

### Última Actualización
**Fecha:** 12 de Enero, 2026
**Versión:** 1.0.0
**Último cambio:** Implementación completa del flujo de rechazo de cuentas de cobro
