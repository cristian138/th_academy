"""
Script to seed initial data for testing
Run: python seed_data.py
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from services.auth_service import auth_service
from models import UserRole, ContractType, ContractStatus, DocumentType, DocumentStatus, PaymentStatus
from datetime import datetime, timedelta, timezone
import uuid
import os
from dotenv import load_dotenv

load_dotenv()

mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
db_name = os.environ.get('DB_NAME', 'sportsadmin_db')

async def seed_database():
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    print("🌱 Seeding database...")
    
    # Clear existing data
    await db.users.delete_many({})
    await db.contracts.delete_many({})
    await db.documents.delete_many({})
    await db.payments.delete_many({})
    await db.notifications.delete_many({})
    await db.audit_logs.delete_many({})
    
    print("✅ Cleared existing data")
    
    # Create users
    users = [
        {
            "id": str(uuid.uuid4()),
            "email": "superadmin@sportsadmin.com",
            "name": "Super Administrador",
            "role": UserRole.SUPERADMIN,
            "hashed_password": auth_service.hash_password("admin123"),
            "identification": "1234567890",
            "phone": "+57 300 123 4567",
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        },
        {
            "id": str(uuid.uuid4()),
            "email": "admin@sportsadmin.com",
            "name": "Administrador General",
            "role": UserRole.ADMIN,
            "hashed_password": auth_service.hash_password("admin123"),
            "identification": "1234567891",
            "phone": "+57 300 123 4568",
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        },
        {
            "id": str(uuid.uuid4()),
            "email": "legal@sportsadmin.com",
            "name": "Representante Legal",
            "role": UserRole.LEGAL_REP,
            "hashed_password": auth_service.hash_password("legal123"),
            "identification": "1234567892",
            "phone": "+57 300 123 4569",
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        },
        {
            "id": str(uuid.uuid4()),
            "email": "contador@sportsadmin.com",
            "name": "Contador Principal",
            "role": UserRole.ACCOUNTANT,
            "hashed_password": auth_service.hash_password("contador123"),
            "identification": "1234567893",
            "phone": "+57 300 123 4570",
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        },
        {
            "id": str(uuid.uuid4()),
            "email": "carlos.rodriguez@coach.com",
            "name": "Carlos Rodríguez",
            "role": UserRole.COLLABORATOR,
            "hashed_password": auth_service.hash_password("carlos123"),
            "identification": "1001234567",
            "phone": "+57 310 234 5678",
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        },
        {
            "id": str(uuid.uuid4()),
            "email": "maria.gonzalez@coach.com",
            "name": "María González",
            "role": UserRole.COLLABORATOR,
            "hashed_password": auth_service.hash_password("maria123"),
            "identification": "1001234568",
            "phone": "+57 310 234 5679",
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        },
        {
            "id": str(uuid.uuid4()),
            "email": "juan.martinez@coach.com",
            "name": "Juan Martínez",
            "role": UserRole.COLLABORATOR,
            "hashed_password": auth_service.hash_password("juan123"),
            "identification": "1001234569",
            "phone": "+57 310 234 5680",
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
    ]
    
    await db.users.insert_many(users)
    print(f"✅ Created {len(users)} users")
    
    # Get user IDs for reference
    collaborators = [u for u in users if u["role"] == UserRole.COLLABORATOR]
    legal_rep = [u for u in users if u["role"] == UserRole.LEGAL_REP][0]
    admin = [u for u in users if u["role"] == UserRole.ADMIN][0]
    accountant = [u for u in users if u["role"] == UserRole.ACCOUNTANT][0]
    
    # Create documents for collaborators
    doc_types = [
        DocumentType.CEDULA,
        DocumentType.RUT,
        DocumentType.CERT_LABORAL,
        DocumentType.CERT_EDUCATIVA,
        DocumentType.CUENTA_BANCARIA,
        DocumentType.ANTECEDENTES
    ]
    
    all_documents = []
    for collaborator in collaborators:
        for doc_type in doc_types:
            doc = {
                "id": str(uuid.uuid4()),
                "document_type": doc_type,
                "user_id": collaborator["id"],
                "file_name": f"{doc_type.value}_{collaborator['name']}.pdf",
                "status": DocumentStatus.APPROVED,
                "onedrive_file_id": f"mock_file_{uuid.uuid4()}",
                "file_url": "#",
                "reviewed_by": admin["id"],
                "expiry_date": datetime.now(timezone.utc) + timedelta(days=365) if doc_type in [DocumentType.CUENTA_BANCARIA, DocumentType.ANTECEDENTES] else None,
                "created_at": datetime.now(timezone.utc) - timedelta(days=30),
                "updated_at": datetime.now(timezone.utc) - timedelta(days=25)
            }
            all_documents.append(doc)
    
    await db.documents.insert_many(all_documents)
    print(f"✅ Created {len(all_documents)} documents")
    
    # Create contracts
    contracts = [
        {
            "id": str(uuid.uuid4()),
            "contract_type": ContractType.SERVICE,
            "collaborator_id": collaborators[0]["id"],
            "title": "Contrato Entrenador de Fútbol - Carlos Rodríguez",
            "description": "Contrato de prestación de servicios como entrenador principal del equipo de fútbol juvenil",
            "start_date": datetime.now(timezone.utc) - timedelta(days=60),
            "end_date": datetime.now(timezone.utc) + timedelta(days=305),
            "monthly_payment": 3500000,
            "status": ContractStatus.ACTIVE,
            "created_by": legal_rep["id"],
            "approved_by": legal_rep["id"],
            "signed_file_id": f"mock_signed_{uuid.uuid4()}",
            "created_at": datetime.now(timezone.utc) - timedelta(days=60),
            "updated_at": datetime.now(timezone.utc) - timedelta(days=50)
        },
        {
            "id": str(uuid.uuid4()),
            "contract_type": ContractType.SERVICE,
            "collaborator_id": collaborators[1]["id"],
            "title": "Contrato Instructora de Natación - María González",
            "description": "Contrato de prestación de servicios como instructora de natación para niveles principiante e intermedio",
            "start_date": datetime.now(timezone.utc) - timedelta(days=45),
            "end_date": datetime.now(timezone.utc) + timedelta(days=320),
            "monthly_payment": 2800000,
            "status": ContractStatus.ACTIVE,
            "created_by": legal_rep["id"],
            "approved_by": legal_rep["id"],
            "signed_file_id": f"mock_signed_{uuid.uuid4()}",
            "created_at": datetime.now(timezone.utc) - timedelta(days=45),
            "updated_at": datetime.now(timezone.utc) - timedelta(days=35)
        },
        {
            "id": str(uuid.uuid4()),
            "contract_type": ContractType.EVENT,
            "collaborator_id": collaborators[2]["id"],
            "title": "Contrato Sesiones de Tenis - Juan Martínez",
            "description": "Contrato por sesión para clases particulares de tenis",
            "start_date": datetime.now(timezone.utc) - timedelta(days=20),
            "end_date": datetime.now(timezone.utc) + timedelta(days=160),
            "payment_per_session": 150000,
            "status": ContractStatus.PENDING_APPROVAL,
            "created_by": legal_rep["id"],
            "created_at": datetime.now(timezone.utc) - timedelta(days=20),
            "updated_at": datetime.now(timezone.utc) - timedelta(days=15)
        },
        {
            "id": str(uuid.uuid4()),
            "contract_type": ContractType.SERVICE,
            "collaborator_id": collaborators[0]["id"],
            "title": "Contrato Coordinador Deportivo - Carlos Rodríguez",
            "description": "Contrato adicional como coordinador del área deportiva",
            "start_date": datetime.now(timezone.utc) + timedelta(days=15),
            "end_date": datetime.now(timezone.utc) + timedelta(days=380),
            "monthly_payment": 4500000,
            "status": ContractStatus.UNDER_REVIEW,
            "created_by": legal_rep["id"],
            "created_at": datetime.now(timezone.utc) - timedelta(days=5),
            "updated_at": datetime.now(timezone.utc) - timedelta(days=2)
        }
    ]
    
    await db.contracts.insert_many(contracts)
    print(f"✅ Created {len(contracts)} contracts")
    
    # Create payments for active contracts
    active_contracts = [c for c in contracts if c["status"] == ContractStatus.ACTIVE]
    payments = []
    
    for contract in active_contracts[:2]:
        # Create 2 paid payments
        for i in range(2):
            payment = {
                "id": str(uuid.uuid4()),
                "contract_id": contract["id"],
                "amount": contract.get("monthly_payment", 150000),
                "payment_date": datetime.now(timezone.utc) - timedelta(days=60-i*30),
                "description": f"Pago mes {i+1}",
                "status": PaymentStatus.PAID,
                "created_by": accountant["id"],
                "bill_file_id": f"mock_bill_{uuid.uuid4()}",
                "voucher_file_id": f"mock_voucher_{uuid.uuid4()}",
                "created_at": datetime.now(timezone.utc) - timedelta(days=65-i*30),
                "updated_at": datetime.now(timezone.utc) - timedelta(days=58-i*30)
            }
            payments.append(payment)
        
        # Create 1 pending payment
        payment = {
            "id": str(uuid.uuid4()),
            "contract_id": contract["id"],
            "amount": contract.get("monthly_payment", 150000),
            "payment_date": datetime.now(timezone.utc),
            "description": "Pago mes actual",
            "status": PaymentStatus.PENDING_BILL,
            "created_by": accountant["id"],
            "created_at": datetime.now(timezone.utc) - timedelta(days=5),
            "updated_at": datetime.now(timezone.utc) - timedelta(days=5)
        }
        payments.append(payment)
    
    await db.payments.insert_many(payments)
    print(f"✅ Created {len(payments)} payments")
    
    # Create some notifications
    notifications = [
        {
            "user_id": collaborators[0]["id"],
            "title": "Nuevo Pago Pendiente",
            "message": "Tiene un pago pendiente por $3,500,000. Por favor cargue su cuenta de cobro.",
            "notification_type": "payment_created",
            "read": False,
            "created_at": datetime.now(timezone.utc) - timedelta(days=5)
        },
        {
            "user_id": legal_rep["id"],
            "title": "Contrato Pendiente de Aprobación",
            "message": "El contrato 'Contrato Sesiones de Tenis - Juan Martínez' requiere su aprobación",
            "notification_type": "contract_pending_approval",
            "read": False,
            "created_at": datetime.now(timezone.utc) - timedelta(days=3)
        },
        {
            "user_id": admin["id"],
            "title": "Contrato en Revisión",
            "message": "Nuevo contrato 'Contrato Coordinador Deportivo' requiere revisión administrativa",
            "notification_type": "contract_under_review",
            "read": False,
            "created_at": datetime.now(timezone.utc) - timedelta(days=2)
        }
    ]
    
    await db.notifications.insert_many(notifications)
    print(f"✅ Created {len(notifications)} notifications")
    
    print("\n🎉 Database seeded successfully!\n")
    print("📧 Test User Credentials:")
    print("   Superadmin: superadmin@sportsadmin.com / admin123")
    print("   Admin: admin@sportsadmin.com / admin123")
    print("   Legal Rep: legal@sportsadmin.com / legal123")
    print("   Accountant: contador@sportsadmin.com / contador123")
    print("   Collaborator 1: carlos.rodriguez@coach.com / carlos123")
    print("   Collaborator 2: maria.gonzalez@coach.com / maria123")
    print("   Collaborator 3: juan.martinez@coach.com / juan123")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(seed_database())
