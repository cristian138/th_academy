# 📧 Configuración de SMTP en Microsoft 365

## ⚠️ Problema Actual

El sistema está configurado para enviar correos pero **SMTP está deshabilitado en tu tenant de Microsoft 365**.

**Error actual:**
```
Authentication unsuccessful, SmtpClientAuthentication is disabled for the Tenant
```

## ✅ Solución: Habilitar SMTP Auth en Microsoft 365

### Opción 1: Habilitar SMTP para toda la organización

1. **Acceder al Centro de administración de Microsoft 365**
   - Ir a: https://admin.microsoft.com
   - Iniciar sesión como administrador global

2. **Ir a Configuración**
   - Settings → Org settings
   - Click en "Modern authentication"

3. **Habilitar SMTP AUTH**
   - Buscar la opción "SMTP AUTH"
   - Activar el toggle
   - Guardar cambios

### Opción 2: Habilitar SMTP solo para la cuenta específica

1. **Acceder a Exchange Admin Center**
   - Ir a: https://admin.exchange.microsoft.com
   - Iniciar sesión como administrador

2. **Configurar la cuenta**
   - Recipients → Mailboxes
   - Buscar y seleccionar: `th.system@academiajotuns.com`
   - Click en "Mail flow settings"
   - Buscar "SMTP AUTH"
   - Activar y guardar

### Opción 3: Usar Modern Authentication (Recomendado)

En lugar de SMTP tradicional, puedes usar **OAuth 2.0** con Microsoft Graph API (más seguro):

1. En Azure Portal, configurar permisos `Mail.Send`
2. Usar las credenciales que ya tienes:
   - Client ID: `aa7ba963-5181-462f-987a-256cdfc37994`
   - Tenant ID: `51eb774f-af90-4f7c-b3b4-35dfeebdeadd`
   
Yo puedo implementar esto si prefieres (es más seguro y no requiere contraseñas).

---

## 🔧 Estado Actual del Sistema

**Mientras tanto:**
- ✅ El sistema funciona sin bloqueos
- ✅ Los correos se "simulan" en los logs
- ✅ No afecta el flujo de trabajo
- ℹ️ Los logs muestran: `📧 Email simulated to...`

**Cuando habilites SMTP:**
- Los correos se enviarán automáticamente
- Desde: `Sistema Talento Humano - Jotuns Club <th.system@academiajotuns.com>`
- No requiere cambios en el código

---

## 📂 SharePoint - Próximo Paso

Para conectar el sistema a tu carpeta de SharePoint:
```
https://clubjotuns-my.sharepoint.com/:f:/g/personal/cristian_prieto_academiajotuns_com/...
```

Necesitarás configurar permisos de aplicación en Azure:
1. `Sites.ReadWrite.All`
2. `Files.ReadWrite.All`

Por ahora estamos usando **almacenamiento local** en `/app/storage/` que funciona perfectamente.

---

## 🎯 Recomendaciones

1. **Para Producción**: Habilita SMTP Auth (Opción 1 o 2)
2. **Para Máxima Seguridad**: Usa OAuth 2.0 (Opción 3)
3. **Para SharePoint**: Configuramos permisos de Azure cuando tengas tiempo

**¿Qué prefieres hacer?**
