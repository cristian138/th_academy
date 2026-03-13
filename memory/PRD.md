# PRD - Sistema de Gestión de Talento Humano
## Academia Jotuns Club SAS

### Problema Original
Sistema administrativo para una academia deportiva para gestionar la contratación de colaboradores con los siguientes requisitos:

1. **Gestión de Contratos:** Para servicios y eventos, con flujo de trabajo: creación - carga de documentos - revisión - aprobación - firma - archivo.
2. **Documentos:** Gestión de documentos obligatorios (cédula, RUT, etc.) y opcionales.
3. **Usuarios y Roles (RBAC):** Superadministrador, Administrador General, Representante Legal, Contador, Colaborador.
4. **Pagos:** Registro de pagos vinculado a cuentas de cobro creadas por el colaborador.
5. **Notificaciones:** Envío de correos electrónicos en puntos clave.
6. **Reportes:** Contratos pendientes, vigentes, pagos, etc.
7. **Seguridad:** Cumplimiento de ley de protección de datos, cifrado, auditoría.
8. **Branding:** Logo, colores (#002d54) y nombre de "Talento Humano | Academia Jotuns Club SAS".
9. **Integración con Presupuesto:** Sincronización automática de pagos aprobados con sistema de presupuesto externo.
10. **Certificados Laborales:** Generación de PDFs con logo, firma digital, QR de verificación.

---

### Arquitectura Técnica
- **Backend:** FastAPI (Python) + MongoDB
- **Frontend:** React + Tailwind CSS + Shadcn/UI
- **Autenticación:** JWT con RBAC
- **Almacenamiento:** Sistema de archivos local (`/app/storage/`)
- **Notificaciones:** SMTP (Microsoft 365)
- **Integración:** httpx para comunicación con sistema de presupuesto

---

### Funcionalidades Implementadas

#### Autenticación y Autorización
- Login con JWT
- Control de acceso basado en roles (RBAC)
- Protección de rutas en frontend y backend

#### Gestión de Usuarios
- Creación de usuarios por admin
- Listado y actualización de usuarios
- Roles: superadmin, admin, legal_rep, accountant, collaborator

#### Gestión de Contratos
- Creación de contratos (por representante legal)
- Flujo de estados: draft - pending_documents - under_review - pending_approval - approved - active
- Visualización de contratos por rol
- Carga de contrato firmado
- Edición de contratos por admin/superadmin

#### Gestión de Documentos
- Documentos obligatorios: Cédula, RUT, Certificación Bancaria, Antecedentes
- Documentos opcionales: Certificado Laboral, Certificado Educativo, Licencia
- Revisión y aprobación de documentos
- Eliminación de documentos antes de aprobación

#### Flujo de Pagos (Cuentas de Cobro)
- Colaborador: Crear cuenta de cobro, subir PDF
- Contador/Superadmin: Ver PDF, aprobar o rechazar cuentas de cobro
- Superadmin: Editar pagos pendientes (monto, descripción)
- Rechazo con motivo visible para colaborador
- Reenvío tras corrección
- Comprobante de pago generado por contador

#### Certificados Laborales (PDF)
- Generación con logo, firma digital, datos dinámicos y QR
- Página pública de verificación de certificados
- Módulo de configuración para cargar firma

#### Integración con Sistema de Presupuesto
- Sincronización automática al aprobar pagos
- Webhook receptor desde presupuesto (actualiza estado de pago)
- Panel de monitoreo de integración (sincronizados/pendientes/errores)
- Health check de conectividad con presupuesto
- Reintentos manuales de sincronización

#### Reportes y Exportación
- Reportes de contratos y pagos
- Exportación a Excel

#### Notificaciones
- Sistema de notificaciones in-app
- Correos con plantillas HTML profesionales
- Lógica optimizada de envío

#### Auditoría
- Registro de todas las acciones importantes

---

### Estado de Servicios Externos

| Servicio | Estado | Notas |
|----------|--------|-------|
| MongoDB | Funcionando | Base de datos local |
| Almacenamiento | Local | Archivos en `/app/storage/` |
| Email SMTP | Requiere config | Requiere configuración del tenant de Microsoft 365 |
| Presupuesto | Conectado | https://presupuesto.academiajotuns.com |

---

### Pendientes (Backlog)

#### P1 - Alta Prioridad
- **Refactorización de server.py:** Dividir en módulos (routes/contracts.py, routes/payments.py, etc.)

#### P2 - Media Prioridad
- Alertas de vencimiento de documentos
- Filtros de fecha para reportes
- Migración a SharePoint/OneDrive

#### P3 - Baja Prioridad
- Dashboard con gráficos avanzados
- Notificaciones push
- Script de despliegue automatizado

---

### Credenciales de Prueba
| Usuario | Email | Password | Rol |
|---------|-------|----------|-----|
| Super Admin | superadmin@sportsadmin.com | password | superadmin |
| Admin | admin@test.com | password | admin |
| Contador | contador@test.com | password | accountant |
| Colaborador | colaborador@test.com | password | collaborator |

---

### Archivos de Referencia Importantes
- `/app/backend/server.py` - API principal (monolítico, pendiente refactorización)
- `/app/backend/services/presupuesto_integration.py` - Integración con presupuesto
- `/app/backend/services/certificate_service.py` - Generación de certificados PDF
- `/app/backend/services/email_service.py` - Servicio de correo
- `/app/frontend/src/pages/IntegrationMonitorPage.js` - Panel de integración
- `/app/frontend/src/pages/PaymentsPage.js` - Flujo de pagos
- `/app/frontend/src/services/api.js` - API client

---

### Última Actualización
**Fecha:** Diciembre 2025
**Versión:** 1.4.0
**Últimos cambios:**
- Integración completa con sistema de presupuesto (sync, webhook, monitoreo, health check)
- Página de monitoreo de integración con estadísticas y reintentos
- Verificado: superadmin puede editar, aprobar y rechazar pagos
- Testing: 23/23 tests backend, 100% frontend
