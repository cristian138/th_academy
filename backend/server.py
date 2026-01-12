from fastapi import FastAPI, HTTPException, Depends, status, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from contextlib import asynccontextmanager
from database import connect_db, close_db, get_database
from config import settings
from models import (
    User, UserCreate, UserLogin, UserRole, UserUpdate,
    Contract, ContractCreate, ContractUpdate, ContractStatus, ContractType,
    Document, DocumentCreate, DocumentUpdate, DocumentStatus, DocumentType,
    Payment, PaymentCreate, PaymentUpdate, PaymentStatus,
    DashboardStats, Notification
)
from services.auth_service import auth_service
from services.email_service import email_service
from services.onedrive_service import onedrive_service
from services.audit_service import audit_service
from typing import List, Optional
from datetime import datetime, timedelta, timezone
import logging
import uuid

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

security = HTTPBearer()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await connect_db()
    yield
    # Shutdown
    await close_db()

app = FastAPI(
    title="SportsAdmin API",
    description="Sistema de Gesti\u00f3n de Contratos para Academia Deportiva",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(','),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get current user
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = auth_service.decode_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    db = await get_database()
    user_data = await db.users.find_one({"id": payload["sub"]})
    
    if not user_data or not user_data.get("is_active"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    return User(**user_data)

# Dependency to check role
def require_role(required_role: UserRole):
    async def role_checker(current_user: User = Depends(get_current_user)):
        if not auth_service.has_permission(current_user.role, required_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    return role_checker

# ============= AUTHENTICATION ROUTES =============

@app.post("/api/auth/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register(user_create: UserCreate):
    """Register a new user (only superadmin can create users)"""
    db = await get_database()
    
    # Check if email already exists
    existing_user = await db.users.find_one({"email": user_create.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash password
    hashed_password = auth_service.hash_password(user_create.password)
    
    # Create user
    user_dict = user_create.model_dump(exclude={"password"})
    user_dict.update({
        "id": str(uuid.uuid4()),
        "hashed_password": hashed_password,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    })
    
    await db.users.insert_one(user_dict)
    return User(**user_dict)

@app.post("/api/auth/login")
async def login(credentials: UserLogin):
    """Login and get access token"""
    db = await get_database()
    
    user_data = await db.users.find_one({"email": credentials.email})
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    if not auth_service.verify_password(credentials.password, user_data["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    if not user_data.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive"
        )
    
    # Create access token
    access_token = auth_service.create_access_token(
        user_id=user_data["id"],
        email=user_data["email"],
        role=user_data["role"]
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": User(**user_data)
    }

@app.get("/api/auth/me", response_model=User)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user info"""
    return current_user

# ============= USER ROUTES =============

@app.get("/api/users", response_model=List[User])
async def list_users(
    role: Optional[UserRole] = None,
    current_user: User = Depends(require_role(UserRole.ADMIN))
):
    """List all users (admin only)"""
    db = await get_database()
    query = {}
    if role:
        query["role"] = role
    
    users = await db.users.find(query, {"_id": 0, "hashed_password": 0}).to_list(1000)
    return [User(**user) for user in users]

@app.get("/api/users/{user_id}", response_model=User)
async def get_user(
    user_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get user by ID"""
    db = await get_database()
    user_data = await db.users.find_one({"id": user_id}, {"_id": 0, "hashed_password": 0})
    
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")
    
    return User(**user_data)

@app.put("/api/users/{user_id}", response_model=User)
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    current_user: User = Depends(require_role(UserRole.ADMIN))
):
    """Update user (admin only)"""
    db = await get_database()
    
    update_data = user_update.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No data to update")
    
    update_data["updated_at"] = datetime.now(timezone.utc)
    
    result = await db.users.update_one(
        {"id": user_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    updated_user = await db.users.find_one({"id": user_id}, {"_id": 0, "hashed_password": 0})
    return User(**updated_user)

# ============= CONTRACT ROUTES =============

@app.post("/api/contracts", response_model=Contract, status_code=status.HTTP_201_CREATED)
async def create_contract(
    contract_create: ContractCreate,
    current_user: User = Depends(require_role(UserRole.LEGAL_REP))
):
    """Create a new contract (legal representative only)"""
    db = await get_database()
    
    # Verify collaborator exists
    collaborator = await db.users.find_one({"id": contract_create.collaborator_id, "role": UserRole.COLLABORATOR})
    if not collaborator:
        raise HTTPException(status_code=404, detail="Collaborator not found")
    
    # Check if collaborator has all required documents
    required_docs = [
        DocumentType.CEDULA,
        DocumentType.RUT,
        DocumentType.CERT_LABORAL,
        DocumentType.CERT_EDUCATIVA,
        DocumentType.CUENTA_BANCARIA,
        DocumentType.ANTECEDENTES
    ]
    
    for doc_type in required_docs:
        doc = await db.documents.find_one({
            "user_id": contract_create.collaborator_id,
            "document_type": doc_type,
            "status": DocumentStatus.APPROVED
        })
        if not doc:
            # Create notification for missing documents
            await db.notifications.insert_one({
                "user_id": contract_create.collaborator_id,
                "title": "Documentos Pendientes",
                "message": f"Por favor cargue el documento: {doc_type.value}",
                "notification_type": "document_missing",
                "read": False,
                "created_at": datetime.now(timezone.utc)
            })
    
    # Determine initial status
    has_all_docs = all([
        await db.documents.find_one({
            "user_id": contract_create.collaborator_id,
            "document_type": doc_type,
            "status": DocumentStatus.APPROVED
        }) for doc_type in required_docs
    ])
    
    initial_status = ContractStatus.UNDER_REVIEW if has_all_docs else ContractStatus.PENDING_DOCUMENTS
    
    # Create contract
    contract_dict = contract_create.model_dump()
    contract_dict.update({
        "id": str(uuid.uuid4()),
        "status": initial_status,
        "created_by": current_user.id,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    })
    
    await db.contracts.insert_one(contract_dict)
    
    # Create audit log
    await audit_service.log(
        user_id=current_user.id,
        action="create_contract",
        resource_type="contract",
        resource_id=contract_dict["id"],
        details={"collaborator_id": contract_create.collaborator_id}
    )
    
    # Send notification to collaborator
    await db.notifications.insert_one({
        "user_id": contract_create.collaborator_id,
        "title": "Nuevo Contrato Creado",
        "message": f"Se ha creado un nuevo contrato: {contract_create.title}",
        "notification_type": "contract_created",
        "read": False,
        "created_at": datetime.now(timezone.utc)
    })
    
    # Send email
    await email_service.send_email(
        recipient_email=collaborator["email"],
        subject="Nuevo Contrato Creado - SportsAdmin",
        body=f"<h2>Nuevo Contrato</h2><p>Se ha creado un nuevo contrato: <strong>{contract_create.title}</strong></p><p>Por favor revise los detalles en el sistema.</p>"
    )
    
    return Contract(**contract_dict)

@app.get("/api/contracts", response_model=List[Contract])
async def list_contracts(
    status: Optional[ContractStatus] = None,
    collaborator_id: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """List contracts"""
    db = await get_database()
    query = {}
    
    if status:
        query["status"] = status
    
    if current_user.role == UserRole.COLLABORATOR:
        query["collaborator_id"] = current_user.id
    elif collaborator_id:
        query["collaborator_id"] = collaborator_id
    
    contracts = await db.contracts.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return [Contract(**contract) for contract in contracts]

@app.get("/api/contracts/{contract_id}", response_model=Contract)
async def get_contract(
    contract_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get contract by ID"""
    db = await get_database()
    contract = await db.contracts.find_one({"id": contract_id}, {"_id": 0})
    
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    
    # Check permissions
    if current_user.role == UserRole.COLLABORATOR and contract["collaborator_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return Contract(**contract)

@app.put("/api/contracts/{contract_id}", response_model=Contract)
async def update_contract(
    contract_id: str,
    contract_update: ContractUpdate,
    current_user: User = Depends(require_role(UserRole.LEGAL_REP))
):
    """Update contract (legal representative only)"""
    db = await get_database()
    
    update_data = contract_update.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No data to update")
    
    update_data["updated_at"] = datetime.now(timezone.utc)
    
    result = await db.contracts.update_one(
        {"id": contract_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Contract not found")
    
    await audit_service.log(
        user_id=current_user.id,
        action="update_contract",
        resource_type="contract",
        resource_id=contract_id
    )
    
    updated_contract = await db.contracts.find_one({"id": contract_id}, {"_id": 0})
    return Contract(**updated_contract)

@app.post("/api/contracts/{contract_id}/review")
async def review_contract(
    contract_id: str,
    current_user: User = Depends(require_role(UserRole.ADMIN))
):
    """Review contract and move to pending approval"""
    db = await get_database()
    
    contract = await db.contracts.find_one({"id": contract_id})
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    
    if contract["status"] != ContractStatus.UNDER_REVIEW:
        raise HTTPException(status_code=400, detail="Contract is not under review")
    
    # Update status
    await db.contracts.update_one(
        {"id": contract_id},
        {"$set": {"status": ContractStatus.PENDING_APPROVAL, "updated_at": datetime.now(timezone.utc)}}
    )
    
    # Create notification for legal representative
    legal_reps = await db.users.find({"role": UserRole.LEGAL_REP}).to_list(100)
    for legal_rep in legal_reps:
        await db.notifications.insert_one({
            "user_id": legal_rep["id"],
            "title": "Contrato Pendiente de Aprobaci\u00f3n",
            "message": f"El contrato {contract['title']} requiere su aprobaci\u00f3n",
            "notification_type": "contract_pending_approval",
            "read": False,
            "created_at": datetime.now(timezone.utc)
        })
        
        # Send email
        await email_service.send_email(
            recipient_email=legal_rep["email"],
            subject="Contrato Pendiente de Aprobaci\u00f3n",
            body=f"<h2>Contrato Pendiente</h2><p>El contrato <strong>{contract['title']}</strong> requiere su aprobaci\u00f3n.</p>"
        )
    
    await audit_service.log(
        user_id=current_user.id,
        action="review_contract",
        resource_type="contract",
        resource_id=contract_id
    )
    
    return {"message": "Contract reviewed successfully"}

@app.post("/api/contracts/{contract_id}/approve")
async def approve_contract(
    contract_id: str,
    current_user: User = Depends(require_role(UserRole.LEGAL_REP))
):
    """Approve contract"""
    db = await get_database()
    
    contract = await db.contracts.find_one({"id": contract_id})
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    
    if contract["status"] != ContractStatus.PENDING_APPROVAL:
        raise HTTPException(status_code=400, detail="Contract is not pending approval")
    
    # Update status
    await db.contracts.update_one(
        {"id": contract_id},
        {"$set": {
            "status": ContractStatus.APPROVED,
            "approved_by": current_user.id,
            "updated_at": datetime.now(timezone.utc)
        }}
    )
    
    # Notify collaborator
    collaborator = await db.users.find_one({"id": contract["collaborator_id"]})
    await db.notifications.insert_one({
        "user_id": contract["collaborator_id"],
        "title": "Contrato Aprobado",
        "message": f"Su contrato {contract['title']} ha sido aprobado. Por favor descargue, firme y cargue el documento firmado.",
        "notification_type": "contract_approved",
        "read": False,
        "created_at": datetime.now(timezone.utc)
    })
    
    # Send email
    await email_service.send_email(
        recipient_email=collaborator["email"],
        subject="Contrato Aprobado - SportsAdmin",
        body=f"<h2>Contrato Aprobado</h2><p>Su contrato <strong>{contract['title']}</strong> ha sido aprobado.</p><p>Por favor descargue, firme y cargue el documento firmado en el sistema.</p>"
    )
    
    await audit_service.log(
        user_id=current_user.id,
        action="approve_contract",
        resource_type="contract",
        resource_id=contract_id
    )
    
    return {"message": "Contract approved successfully"}

@app.post("/api/contracts/{contract_id}/upload-signed")
async def upload_signed_contract(
    contract_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Upload signed contract"""
    db = await get_database()
    
    contract = await db.contracts.find_one({"id": contract_id})
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    
    # Check permissions
    if current_user.role == UserRole.COLLABORATOR and contract["collaborator_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if contract["status"] not in [ContractStatus.APPROVED, ContractStatus.PENDING_SIGNATURE]:
        raise HTTPException(status_code=400, detail="Contract cannot be signed in current status")
    
    # Upload to OneDrive
    file_content = await file.read()
    result = await onedrive_service.upload_file(
        file_content=file_content,
        file_name=f"contract_{contract_id}_{file.filename}",
        folder_path="SportsAdmin/Contracts"
    )
    
    if not result:
        raise HTTPException(status_code=500, detail="Failed to upload file")
    
    # Update contract
    await db.contracts.update_one(
        {"id": contract_id},
        {"$set": {
            "status": ContractStatus.ACTIVE,
            "signed_file_id": result["id"],
            "updated_at": datetime.now(timezone.utc)
        }}
    )
    
    await audit_service.log(
        user_id=current_user.id,
        action="upload_signed_contract",
        resource_type="contract",
        resource_id=contract_id
    )
    
    return {"message": "Signed contract uploaded successfully", "file_id": result["id"]}

# ============= DOCUMENT ROUTES =============

@app.post("/api/documents", response_model=Document, status_code=status.HTTP_201_CREATED)
async def upload_document(
    document_type: DocumentType,
    file: UploadFile = File(...),
    expiry_date: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Upload document"""
    db = await get_database()
    
    # Upload to OneDrive
    file_content = await file.read()
    result = await onedrive_service.upload_file(
        file_content=file_content,
        file_name=f"{document_type.value}_{current_user.id}_{file.filename}",
        folder_path="SportsAdmin/Documents"
    )
    
    if not result:
        raise HTTPException(status_code=500, detail="Failed to upload file")
    
    # Create document record
    doc_dict = {
        "id": str(uuid.uuid4()),
        "document_type": document_type,
        "user_id": current_user.id,
        "file_name": file.filename,
        "status": DocumentStatus.UPLOADED,
        "onedrive_file_id": result["id"],
        "file_url": result.get("webUrl", "#"),
        "expiry_date": datetime.fromisoformat(expiry_date) if expiry_date else None,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }
    
    await db.documents.insert_one(doc_dict)
    
    # Notify admin
    admins = await db.users.find({"role": UserRole.ADMIN}).to_list(100)
    for admin in admins:
        await db.notifications.insert_one({
            "user_id": admin["id"],
            "title": "Nuevo Documento Cargado",
            "message": f"{current_user.name} ha cargado un documento: {document_type.value}",
            "notification_type": "document_uploaded",
            "read": False,
            "created_at": datetime.now(timezone.utc)
        })
    
    await audit_service.log(
        user_id=current_user.id,
        action="upload_document",
        resource_type="document",
        resource_id=doc_dict["id"]
    )
    
    return Document(**doc_dict)

@app.get("/api/documents", response_model=List[Document])
async def list_documents(
    user_id: Optional[str] = None,
    document_type: Optional[DocumentType] = None,
    current_user: User = Depends(get_current_user)
):
    """List documents"""
    db = await get_database()
    query = {}
    
    if current_user.role == UserRole.COLLABORATOR:
        query["user_id"] = current_user.id
    elif user_id:
        query["user_id"] = user_id
    
    if document_type:
        query["document_type"] = document_type
    
    documents = await db.documents.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return [Document(**doc) for doc in documents]

@app.put("/api/documents/{document_id}/review")
async def review_document(
    document_id: str,
    document_update: DocumentUpdate,
    current_user: User = Depends(require_role(UserRole.ADMIN))
):
    """Review and approve/reject document"""
    db = await get_database()
    
    update_data = document_update.model_dump(exclude_unset=True)
    update_data["reviewed_by"] = current_user.id
    update_data["updated_at"] = datetime.now(timezone.utc)
    
    result = await db.documents.update_one(
        {"id": document_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Document not found")
    
    document = await db.documents.find_one({"id": document_id})
    
    # Notify user
    await db.notifications.insert_one({
        "user_id": document["user_id"],
        "title": "Documento Revisado",
        "message": f"Su documento {document['document_type']} ha sido revisado. Estado: {update_data.get('status', 'N/A')}",
        "notification_type": "document_reviewed",
        "read": False,
        "created_at": datetime.now(timezone.utc)
    })
    
    await audit_service.log(
        user_id=current_user.id,
        action="review_document",
        resource_type="document",
        resource_id=document_id
    )
    
    updated_doc = await db.documents.find_one({"id": document_id}, {"_id": 0})
    return Document(**updated_doc)

@app.get("/api/documents/expiring")
async def get_expiring_documents(
    days: int = 15,
    current_user: User = Depends(require_role(UserRole.ADMIN))
):
    """Get documents expiring soon"""
    db = await get_database()
    
    threshold_date = datetime.now(timezone.utc) + timedelta(days=days)
    
    documents = await db.documents.find({
        "expiry_date": {"$lte": threshold_date, "$gte": datetime.now(timezone.utc)},
        "status": DocumentStatus.APPROVED
    }, {"_id": 0}).to_list(1000)
    
    return [Document(**doc) for doc in documents]

# ============= PAYMENT ROUTES =============

@app.post("/api/payments", response_model=Payment, status_code=status.HTTP_201_CREATED)
async def create_payment(
    payment_create: PaymentCreate,
    current_user: User = Depends(get_current_user)
):
    """Create payment record (collaborator creates cuenta de cobro)"""
    db = await get_database()
    
    # Verify contract exists and belongs to collaborator
    contract = await db.contracts.find_one({"id": payment_create.contract_id})
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    
    # Check if collaborator owns the contract
    if current_user.role == UserRole.COLLABORATOR and contract["collaborator_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Create payment
    payment_dict = payment_create.model_dump()
    payment_dict.update({
        "id": str(uuid.uuid4()),
        "status": PaymentStatus.DRAFT,
        "created_by": current_user.id,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    })
    
    await db.payments.insert_one(payment_dict)
    
    await audit_service.log(
        user_id=current_user.id,
        action="create_payment",
        resource_type="payment",
        resource_id=payment_dict["id"]
    )
    
    return Payment(**payment_dict)

@app.get("/api/payments", response_model=List[Payment])
async def list_payments(
    contract_id: Optional[str] = None,
    status: Optional[PaymentStatus] = None,
    current_user: User = Depends(get_current_user)
):
    """List payments"""
    db = await get_database()
    query = {}
    
    if contract_id:
        query["contract_id"] = contract_id
    
    if status:
        query["status"] = status
    
    # If collaborator, only show their payments
    if current_user.role == UserRole.COLLABORATOR:
        contracts = await db.contracts.find({"collaborator_id": current_user.id}, {"_id": 0, "id": 1}).to_list(1000)
        contract_ids = [c["id"] for c in contracts]
        query["contract_id"] = {"$in": contract_ids}
    
    payments = await db.payments.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return [Payment(**payment) for payment in payments]

@app.post("/api/payments/{payment_id}/upload-bill")
async def upload_bill(
    payment_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Upload payment bill (cuenta de cobro) - collaborator submits for approval"""
    db = await get_database()
    
    payment = await db.payments.find_one({"id": payment_id})
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    # Verify collaborator
    contract = await db.contracts.find_one({"id": payment["contract_id"]})
    if current_user.role == UserRole.COLLABORATOR and contract["collaborator_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Upload to OneDrive
    file_content = await file.read()
    result = await onedrive_service.upload_file(
        file_content=file_content,
        file_name=f"bill_{payment_id}_{file.filename}",
        folder_path="SportsAdmin/Bills"
    )
    
    if not result:
        raise HTTPException(status_code=500, detail="Failed to upload file")
    
    # Update payment - move to pending approval
    await db.payments.update_one(
        {"id": payment_id},
        {"$set": {
            "status": PaymentStatus.PENDING_APPROVAL,
            "bill_file_id": result["id"],
            "updated_at": datetime.now(timezone.utc)
        }}
    )
    
    # Notify accountants
    accountants = await db.users.find({"role": UserRole.ACCOUNTANT}).to_list(100)
    for accountant in accountants:
        await db.notifications.insert_one({
            "user_id": accountant["id"],
            "title": "Nueva Cuenta de Cobro",
            "message": f"Cuenta de cobro por ${payment['amount']} requiere aprobación",
            "notification_type": "payment_approval_needed",
            "read": False,
            "created_at": datetime.now(timezone.utc)
        })
        
        # Send email
        await email_service.send_email(
            recipient_email=accountant["email"],
            subject="Nueva Cuenta de Cobro - Jotuns Club",
            body=f"<h2>Cuenta de Cobro Pendiente</h2><p>Una cuenta de cobro por <strong>${payment['amount']}</strong> requiere su aprobación.</p>"
        )
    
    await audit_service.log(
        user_id=current_user.id,
        action="upload_bill",
        resource_type="payment",
        resource_id=payment_id
    )
    
    return {"message": "Cuenta de cobro cargada exitosamente", "file_id": result["id"]}

@app.post("/api/payments/{payment_id}/approve")
async def approve_payment(
    payment_id: str,
    current_user: User = Depends(require_role(UserRole.ACCOUNTANT))
):
    """Approve payment - accountant approves cuenta de cobro"""
    db = await get_database()
    
    payment = await db.payments.find_one({"id": payment_id})
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    if payment["status"] != PaymentStatus.PENDING_APPROVAL:
        raise HTTPException(status_code=400, detail="Payment is not pending approval")
    
    # Update payment to approved
    await db.payments.update_one(
        {"id": payment_id},
        {"$set": {
            "status": PaymentStatus.APPROVED,
            "approved_by": current_user.id,
            "updated_at": datetime.now(timezone.utc)
        }}
    )
    
    # Notify collaborator
    contract = await db.contracts.find_one({"id": payment["contract_id"]})
    collaborator = await db.users.find_one({"id": contract["collaborador_id"]})
    
    await db.notifications.insert_one({
        "user_id": contract["collaborator_id"],
        "title": "Cuenta de Cobro Aprobada",
        "message": f"Su cuenta de cobro por ${payment['amount']} ha sido aprobada",
        "notification_type": "payment_approved",
        "read": False,
        "created_at": datetime.now(timezone.utc)
    })
    
    await email_service.send_email(
        recipient_email=collaborator["email"],
        subject="Cuenta de Cobro Aprobada - Jotuns Club",
        body=f"<h2>Cuenta de Cobro Aprobada</h2><p>Su cuenta de cobro por <strong>${payment['amount']}</strong> ha sido aprobada.</p>"
    )
    
    await audit_service.log(
        user_id=current_user.id,
        action="approve_payment",
        resource_type="payment",
        resource_id=payment_id
    )
    
    return {"message": "Payment approved successfully"}

@app.post("/api/payments/{payment_id}/confirm")
async def confirm_payment(
    payment_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(require_role(UserRole.ACCOUNTANT))
):
    """Confirm payment with voucher"""
    db = await get_database()
    
    payment = await db.payments.find_one({"id": payment_id})
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    # Upload voucher to OneDrive
    file_content = await file.read()
    result = await onedrive_service.upload_file(
        file_content=file_content,
        file_name=f"voucher_{payment_id}_{file.filename}",
        folder_path="SportsAdmin/Vouchers"
    )
    
    if not result:
        raise HTTPException(status_code=500, detail="Failed to upload file")
    
    # Update payment
    await db.payments.update_one(
        {"id": payment_id},
        {"$set": {
            "status": PaymentStatus.PAID,
            "voucher_file_id": result["id"],
            "updated_at": datetime.now(timezone.utc)
        }}
    )
    
    # Notify collaborator
    contract = await db.contracts.find_one({"id": payment["contract_id"]})
    collaborator = await db.users.find_one({"id": contract["collaborator_id"]})
    
    await db.notifications.insert_one({
        "user_id": contract["collaborator_id"],
        "title": "Pago Realizado",
        "message": f"El pago de ${payment['amount']} ha sido procesado. Puede descargar su comprobante.",
        "notification_type": "payment_confirmed",
        "read": False,
        "created_at": datetime.now(timezone.utc)
    })
    
    # Send email
    await email_service.send_email(
        recipient_email=collaborator["email"],
        subject="Pago Procesado - SportsAdmin",
        body=f"<h2>Pago Procesado</h2><p>El pago de <strong>${payment['amount']}</strong> ha sido procesado exitosamente.</p><p>Puede descargar su comprobante en el sistema.</p>"
    )
    
    await audit_service.log(
        user_id=current_user.id,
        action="confirm_payment",
        resource_type="payment",
        resource_id=payment_id
    )
    
    return {"message": "Payment confirmed successfully", "voucher_id": result["id"]}

# ============= DASHBOARD & REPORTS =============

@app.get("/api/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats(current_user: User = Depends(get_current_user)):
    """Get dashboard statistics"""
    db = await get_database()
    
    if current_user.role == UserRole.COLLABORATOR:
        # Stats for collaborator
        total_contracts = await db.contracts.count_documents({"collaborator_id": current_user.id})
        pending_contracts = await db.contracts.count_documents({
            "collaborator_id": current_user.id,
            "status": {"$in": [ContractStatus.PENDING_DOCUMENTS, ContractStatus.APPROVED]}
        })
        active_contracts = await db.contracts.count_documents({
            "collaborator_id": current_user.id,
            "status": ContractStatus.ACTIVE
        })
        
        # Get contracts for payment stats
        contracts = await db.contracts.find({"collaborator_id": current_user.id}, {"_id": 0, "id": 1}).to_list(1000)
        contract_ids = [c["id"] for c in contracts]
        
        pending_payments = await db.payments.count_documents({
            "contract_id": {"$in": contract_ids},
            "status": {"$in": [PaymentStatus.PENDING_BILL, PaymentStatus.PENDING_PAYMENT]}
        })
        
        return DashboardStats(
            total_contracts=total_contracts,
            pending_contracts=pending_contracts,
            active_contracts=active_contracts,
            pending_approvals=0,
            pending_documents=0,
            expiring_documents=0,
            pending_payments=pending_payments,
            total_collaborators=0
        )
    
    # Stats for admin/legal/accountant
    total_contracts = await db.contracts.count_documents({})
    pending_contracts = await db.contracts.count_documents({
        "status": {"$in": [ContractStatus.PENDING_DOCUMENTS, ContractStatus.UNDER_REVIEW]}
    })
    active_contracts = await db.contracts.count_documents({"status": ContractStatus.ACTIVE})
    pending_approvals = await db.contracts.count_documents({"status": ContractStatus.PENDING_APPROVAL})
    pending_documents = await db.documents.count_documents({"status": DocumentStatus.UPLOADED})
    
    # Expiring documents
    threshold_date = datetime.now(timezone.utc) + timedelta(days=15)
    expiring_documents = await db.documents.count_documents({
        "expiry_date": {"$lte": threshold_date, "$gte": datetime.now(timezone.utc)},
        "status": DocumentStatus.APPROVED
    })
    
    pending_payments = await db.payments.count_documents({
        "status": {"$in": [PaymentStatus.PENDING_BILL, PaymentStatus.PENDING_PAYMENT]}
    })
    
    total_collaborators = await db.users.count_documents({"role": UserRole.COLLABORATOR})
    
    return DashboardStats(
        total_contracts=total_contracts,
        pending_contracts=pending_contracts,
        active_contracts=active_contracts,
        pending_approvals=pending_approvals,
        pending_documents=pending_documents,
        expiring_documents=expiring_documents,
        pending_payments=pending_payments,
        total_collaborators=total_collaborators
    )

@app.get("/api/reports/contracts-pending")
async def report_contracts_pending(current_user: User = Depends(require_role(UserRole.ADMIN))):
    """Report: Contracts pending signature"""
    db = await get_database()
    
    contracts = await db.contracts.find({
        "status": {"$in": [ContractStatus.APPROVED, ContractStatus.PENDING_SIGNATURE]}
    }, {"_id": 0}).to_list(1000)
    
    return {"contracts": [Contract(**c) for c in contracts]}

@app.get("/api/reports/contracts-active")
async def report_contracts_active(current_user: User = Depends(require_role(UserRole.ADMIN))):
    """Report: Active contracts"""
    db = await get_database()
    
    contracts = await db.contracts.find({"status": ContractStatus.ACTIVE}, {"_id": 0}).to_list(1000)
    
    return {"contracts": [Contract(**c) for c in contracts]}

@app.get("/api/reports/payments-pending")
async def report_payments_pending(current_user: User = Depends(require_role(UserRole.ACCOUNTANT))):
    """Report: Pending payments"""
    db = await get_database()
    
    payments = await db.payments.find({
        "status": {"$in": [PaymentStatus.PENDING_BILL, PaymentStatus.PENDING_PAYMENT]}
    }, {"_id": 0}).to_list(1000)
    
    return {"payments": [Payment(**p) for p in payments]}

# ============= NOTIFICATIONS =============

@app.get("/api/notifications", response_model=List[Notification])
async def get_notifications(
    limit: int = 50,
    current_user: User = Depends(get_current_user)
):
    """Get user notifications"""
    db = await get_database()
    
    notifications = await db.notifications.find(
        {"user_id": current_user.id},
        {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    
    return [Notification(**n) for n in notifications]

@app.put("/api/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    current_user: User = Depends(get_current_user)
):
    """Mark notification as read"""
    db = await get_database()
    
    result = await db.notifications.update_one(
        {"user_id": current_user.id},
        {"$set": {"read": True}}
    )
    
    return {"message": "Notification marked as read"}

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "SportsAdmin API"}
