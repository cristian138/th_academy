import httpx
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

PRESUPUESTO_BASE_URL = "https://presupuesto.academiajotuns.com"
PRESUPUESTO_WEBHOOK_URL = f"{PRESUPUESTO_BASE_URL}/api/webhook/talento-humano"


async def notify_presupuesto_payment_approved(
    payment_id: str,
    collaborator_name: str,
    amount: float,
    approval_date: datetime,
    payment_description: str = None
) -> dict:
    """
    Notifica al sistema de presupuesto que un pago ha sido aprobado en Talento Humano.
    Envía un webhook con los datos del pago para que se cree automáticamente
    el registro correspondiente en el sistema de presupuesto.
    """
    try:
        payload = {
            "source": "talento_humano",
            "event_type": "payment_approved",
            "payment_id": payment_id,
            "collaborator_name": collaborator_name,
            "amount": amount,
            "approval_date": approval_date.isoformat() if isinstance(approval_date, datetime) else str(approval_date),
            "description": payment_description or f"Pago aprobado para {collaborator_name}",
            "category": "Talento Humano"
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                PRESUPUESTO_WEBHOOK_URL,
                json=payload,
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 200:
                data = response.json()
                logger.info(f"Pago {payment_id} sincronizado con presupuesto exitosamente")
                return {
                    "success": True,
                    "message": "Sincronizado con sistema de presupuesto",
                    "presupuesto_id": data.get("presupuesto_id") or data.get("budget_id"),
                    "monthly_budget_id": data.get("monthly_budget_id")
                }
            else:
                logger.warning(
                    f"Error al sincronizar pago {payment_id} con presupuesto: "
                    f"HTTP {response.status_code} - {response.text}"
                )
                return {
                    "success": False,
                    "message": f"Error HTTP {response.status_code}: {response.text[:200]}"
                }

    except httpx.TimeoutException:
        logger.warning(f"Timeout al sincronizar pago {payment_id} con presupuesto")
        return {
            "success": False,
            "message": "Timeout al conectar con el sistema de presupuesto"
        }
    except httpx.ConnectError:
        logger.warning(f"No se pudo conectar al sistema de presupuesto para pago {payment_id}")
        return {
            "success": False,
            "message": "No se pudo conectar con el sistema de presupuesto"
        }
    except Exception as e:
        logger.error(f"Error inesperado al sincronizar pago {payment_id}: {str(e)}")
        return {
            "success": False,
            "message": f"Error inesperado: {str(e)}"
        }
