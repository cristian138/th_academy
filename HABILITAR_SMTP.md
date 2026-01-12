# Habilitar SMTP en Microsoft 365

## Problema Actual
El envío de correos está fallando con el siguiente error:
```
Authentication unsuccessful, user is locked by your organization's security defaults policy
```

## Solución

### Opción 1: Habilitar SMTP AUTH para el usuario (Recomendado)

1. **Acceder al Centro de Administración de Microsoft 365**
   - Ir a: https://admin.microsoft.com

2. **Navegar a Usuarios > Usuarios activos**

3. **Buscar el usuario:** `th.system@academiajotuns.com`

4. **Seleccionar el usuario y hacer clic en "Correo"**

5. **Buscar "Aplicaciones de correo electrónico"** y hacer clic en "Administrar aplicaciones de correo"

6. **Habilitar "SMTP autenticado"**
   - Marcar la casilla ✅ "SMTP autenticado"
   - Guardar cambios

### Opción 2: Usar PowerShell (Alternativa)

Ejecutar en PowerShell con credenciales de administrador:

```powershell
# Conectar a Exchange Online
Connect-ExchangeOnline -UserPrincipalName admin@academiajotuns.com

# Habilitar SMTP AUTH para el usuario
Set-CASMailbox -Identity "th.system@academiajotuns.com" -SmtpClientAuthenticationDisabled $false

# Verificar el cambio
Get-CASMailbox -Identity "th.system@academiajotuns.com" | Select SmtpClientAuthenticationDisabled
```

### Opción 3: Deshabilitar Security Defaults (No recomendado para producción)

1. Ir a: https://portal.azure.com
2. Azure Active Directory > Propiedades
3. Administrar valores predeterminados de seguridad
4. Deshabilitar "Security defaults"

⚠️ **Advertencia:** Esta opción reduce la seguridad de toda la organización.

---

## Verificar que funciona

Después de realizar los cambios, espere 5-10 minutos y pruebe nuevamente desde el sistema.

Si el correo sigue sin funcionar, verifique:
- Que la contraseña sea correcta
- Que no haya políticas de acceso condicional bloqueando
- Que el usuario tenga licencia de Exchange Online

---

## Credenciales SMTP Actuales

```
Servidor: smtp.office365.com
Puerto: 587
Usuario: th.system@academiajotuns.com
```

## Contacto
Si necesita ayuda adicional, contacte al soporte de Microsoft 365 o al equipo de TI de la organización.
