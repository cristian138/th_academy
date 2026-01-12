# Configuración de Microsoft Graph API - Jotuns Club

## 📧 Sistema de Correos (Microsoft Outlook)

### Credenciales Actuales:
```
AZURE_CLIENT_ID: aa7ba963-5181-462f-987a-256cdfc37994
AZURE_TENANT_ID: 51eb774f-af90-4f7c-b3b4-35dfeebdeadd
AZURE_CLIENT_SECRET: 9LT8Q~C2oSQBE..BOZuYOV1RNjqzJCkKURYNAa_-
```

### ¿Qué cuenta envía los correos?

Los correos se envían desde la cuenta de Microsoft 365 asociada a la aplicación de Azure. Para que funcione correctamente:

1. **Necesitas una cuenta de Microsoft 365 Business** (ejemplo: admin@jotuns.com)
2. Esta cuenta debe estar configurada en Azure AD
3. La aplicación debe tener permisos delegados para enviar correos "en nombre de" esa cuenta

### Permisos Necesarios en Azure:

Para **CORREOS** (Microsoft Outlook):
- `Mail.Send` - Permiso delegado o de aplicación
- `Mail.ReadWrite` - Opcional, para leer correos

**IMPORTANTE:** Los permisos de aplicación requieren consentimiento del administrador del tenant.

---

## 📁 Sistema de Almacenamiento (OneDrive)

### ¿Dónde se almacenan los archivos?

Los archivos se guardan en **OneDrive for Business** en la siguiente estructura:

```
OneDrive/
└── SportsAdmin/
    ├── Contracts/          # Contratos firmados
    ├── Documents/          # Documentos de colaboradores
    ├── Bills/             # Cuentas de cobro
    └── Vouchers/          # Comprobantes de pago
```

### Problema Actual - Error 400 al cargar archivos:

**Causa:** La aplicación de Azure necesita permisos específicos para OneDrive:

```
Files.ReadWrite.All (Application)
Sites.ReadWrite.All (Application)
```

**Estado Actual:**
- ✅ Autenticación funciona (token obtenido correctamente)
- ❌ Carga de archivos falla (status 400)
- **Razón:** Permisos insuficientes o ruta incorrecta

---

## 🔧 Solución: Configurar Permisos en Azure Portal

### Paso 1: Acceder a Azure Portal
1. Ir a https://portal.azure.com
2. Iniciar sesión con la cuenta de administrador
3. Ir a "Azure Active Directory" → "App registrations"
4. Buscar tu aplicación por Client ID: `aa7ba963-5181-462f-987a-256cdfc37994`

### Paso 2: Configurar Permisos para OneDrive
1. Click en tu aplicación
2. Ir a "API permissions" (Permisos de API)
3. Click en "Add a permission"
4. Seleccionar "Microsoft Graph"
5. Seleccionar "Application permissions"
6. Buscar y agregar:
   - `Files.ReadWrite.All` - Leer y escribir archivos en todos los sitios
   - `Sites.ReadWrite.All` - Acceso completo a SharePoint/OneDrive
7. Click en "Add permissions"
8. **IMPORTANTE:** Click en "Grant admin consent for [tu organización]"

### Paso 3: Configurar Permisos para Correo
1. En la misma sección "API permissions"
2. Verificar que tengas:
   - `Mail.Send` (Application permissions)
   - O `Mail.ReadWrite` (Application permissions)
3. Si no están, agregarlos siguiendo los mismos pasos
4. Click en "Grant admin consent"

### Paso 4: Verificar Cuenta de OneDrive
La aplicación necesita acceso a una cuenta de OneDrive específica. Tienes dos opciones:

**Opción A: OneDrive Personal de una cuenta M365**
- Usar `/me/drive/root` en la ruta
- Requiere que la app esté configurada con una cuenta específica

**Opción B: SharePoint/OneDrive Compartido**
- Usar `/sites/{site-id}/drive/root`
- Mejor para uso organizacional

---

## 🔄 Alternativa Temporal: Almacenamiento Local

Mientras configuras Azure, puedo cambiar el sistema para usar **almacenamiento local** temporalmente:

### Ventajas:
- ✅ Funciona inmediatamente sin configuración
- ✅ No depende de credenciales externas
- ✅ Bueno para desarrollo y pruebas

### Desventajas:
- ⚠️ Los archivos quedan en el servidor
- ⚠️ No hay backup automático en la nube
- ⚠️ Requiere gestión manual de espacio

### Ubicación de archivos locales:
```
/app/storage/
├── contracts/
├── documents/
├── bills/
└── vouchers/
```

---

## 📨 Alternativa para Correos: SMTP Simple

Si prefieres no usar Microsoft Graph, puedo configurar SMTP tradicional:

### Opciones SMTP:
1. **Gmail SMTP** (gmail.com)
2. **Outlook SMTP** (smtp.office365.com)
3. **SendGrid** (servicio dedicado)
4. **Otro proveedor SMTP**

### Configuración SMTP necesaria:
```env
SMTP_HOST=smtp.office365.com
SMTP_PORT=587
SMTP_USER=admin@jotuns.com
SMTP_PASSWORD=tu_password
SMTP_FROM=admin@jotuns.com
```

---

## ✅ Recomendación

Para un sistema de producción profesional como Jotuns Club, te recomiendo:

1. **Correo**: Usar Microsoft Graph API con cuenta M365
   - Más seguro (OAuth2 en lugar de contraseñas)
   - Mejor integración con Microsoft
   - Auditoría completa

2. **Almacenamiento**: 
   - **Producción**: OneDrive/SharePoint con permisos correctos
   - **Desarrollo/Pruebas**: Almacenamiento local mientras configuras Azure

---

## 🚀 ¿Qué prefieres hacer?

**Opción 1:** Te ayudo a configurar los permisos correctos en Azure Portal
- Necesitarás acceso al portal como administrador
- Te guiaré paso a paso

**Opción 2:** Cambio temporalmente a almacenamiento local
- Funciona inmediatamente
- Cambias a OneDrive cuando tengas tiempo

**Opción 3:** Configuramos SMTP tradicional para correos
- Más simple
- No requiere Azure App

Dime cuál opción prefieres y procedo con la implementación. 🎯
