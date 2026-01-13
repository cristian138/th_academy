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
from services.storage_service import storage_service
from services.audit_service import audit_service
from typing import List, Optional
from datetime import datetime, timedelta, timezone
import logging
import uuid
import os

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

# Helper to get user from query token (for downloads/exports)
async def get_user_from_token(token: str) -> User:
    payload = auth_service.decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    db = await get_database()
    user_data = await db.users.find_one({"id": payload["sub"]})
    if not user_data or not user_data.get("is_active"):
        raise HTTPException(status_code=401, detail="User not found or inactive")
    
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

@app.delete("/api/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: User = Depends(require_role(UserRole.SUPERADMIN))
):
    """Delete user (superadmin only) - Soft delete by deactivating"""
    db = await get_database()
    
    # Prevent deleting yourself
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="No puede eliminarse a sí mismo")
    
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Check if user has active contracts
    active_contracts = await db.contracts.count_documents({
        "collaborator_id": user_id,
        "status": {"$in": ["active", "pending_documents", "under_review", "pending_approval", "approved"]}
    })
    
    if active_contracts > 0:
        raise HTTPException(
            status_code=400, 
            detail=f"El usuario tiene {active_contracts} contrato(s) activo(s). Finalice los contratos antes de eliminar."
        )
    
    # Soft delete - deactivate user
    await db.users.update_one(
        {"id": user_id},
        {"$set": {"is_active": False, "updated_at": datetime.now(timezone.utc)}}
    )
    
    await audit_service.log(
        user_id=current_user.id,
        action="delete_user",
        resource_type="user",
        resource_id=user_id,
        details={"deleted_user_email": user["email"], "deleted_user_role": user["role"]}
    )
    
    return {"message": "Usuario eliminado exitosamente"}

@app.post("/api/users", status_code=status.HTTP_201_CREATED)
async def create_user(
    user_create: UserCreate,
    current_user: User = Depends(require_role(UserRole.ADMIN))
):
    """Create a new user (admin can create all except superadmin, superadmin can create all)"""
    db = await get_database()
    
    # Only superadmin can create another superadmin
    if user_create.role == UserRole.SUPERADMIN and current_user.role != UserRole.SUPERADMIN:
        raise HTTPException(
            status_code=403, 
            detail="Solo un superadministrador puede crear otros superadministradores"
        )
    
    # Check if email exists
    existing = await db.users.find_one({"email": user_create.email})
    if existing:
        raise HTTPException(status_code=400, detail="El correo electrónico ya está registrado")
    
    user_dict = {
        "id": str(uuid.uuid4()),
        "email": user_create.email,
        "name": user_create.name,
        "role": user_create.role,
        "hashed_password": auth_service.hash_password(user_create.password),
        "phone": user_create.phone,
        "identification": user_create.identification,
        "is_active": True,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }
    
    await db.users.insert_one(user_dict)
    
    # Send welcome email (non-blocking)
    try:
        email_body = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin:0;padding:0;background-color:#f4f4f4;font-family:Arial,Helvetica,sans-serif;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color:#f4f4f4;">
        <tr>
            <td align="center" style="padding:20px 0;">
                <table role="presentation" width="600" cellspacing="0" cellpadding="0" border="0" style="background-color:#ffffff;border-radius:8px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.1);">
                    <!-- Header -->
                    <tr>
                        <td style="background-color:#002d54;padding:30px 40px;text-align:center;">
                            <h1 style="color:#ffffff;margin:0;font-size:24px;font-weight:bold;">Sistema de Talento Humano</h1>
                            <p style="color:#a0c4e8;margin:8px 0 0 0;font-size:14px;">Academia Jotuns Club SAS</p>
                        </td>
                    </tr>
                    <!-- Content -->
                    <tr>
                        <td style="padding:40px;">
                            <h2 style="color:#002d54;margin:0 0 20px 0;font-size:22px;">¡Bienvenido(a) {user_create.name}!</h2>
                            <p style="color:#333333;font-size:16px;line-height:1.6;margin:0 0 25px 0;">
                                Se ha creado su cuenta en el Sistema de Talento Humano de la Academia Jotuns Club.
                            </p>
                            
                            <!-- Credentials Box -->
                            <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color:#f8f9fa;border:2px solid #002d54;border-radius:8px;margin:25px 0;">
                                <tr>
                                    <td style="padding:25px;">
                                        <h3 style="color:#002d54;margin:0 0 20px 0;font-size:18px;">🔐 Sus credenciales de acceso:</h3>
                                        <table role="presentation" cellspacing="0" cellpadding="8" border="0">
                                            <tr>
                                                <td style="color:#666666;font-size:14px;font-weight:bold;padding-right:15px;">URL:</td>
                                                <td><a href="https://th.academiajotuns.com" style="color:#002d54;font-size:14px;font-weight:bold;text-decoration:none;">https://th.academiajotuns.com</a></td>
                                            </tr>
                                            <tr>
                                                <td style="color:#666666;font-size:14px;font-weight:bold;padding-right:15px;">Correo:</td>
                                                <td style="color:#333333;font-size:14px;">{user_create.email}</td>
                                            </tr>
                                            <tr>
                                                <td style="color:#666666;font-size:14px;font-weight:bold;padding-right:15px;">Contraseña:</td>
                                                <td style="color:#333333;font-size:14px;font-family:monospace;background-color:#ffffff;padding:5px 10px;border-radius:4px;">{user_create.password}</td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                            </table>
                            
                            <!-- Button -->
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" style="margin:30px 0;">
                                <tr>
                                    <td style="background-color:#002d54;border-radius:6px;">
                                        <a href="https://th.academiajotuns.com" style="display:inline-block;padding:15px 35px;color:#ffffff;text-decoration:none;font-size:16px;font-weight:bold;">Ingresar al Sistema</a>
                                    </td>
                                </tr>
                            </table>
                            
                            <!-- Warning -->
                            <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color:#fff3cd;border-left:4px solid #ffc107;border-radius:4px;margin:25px 0;">
                                <tr>
                                    <td style="padding:15px 20px;">
                                        <p style="color:#856404;font-size:14px;margin:0;">
                                            <strong>⚠️ Importante:</strong> Por seguridad, le recomendamos cambiar su contraseña después del primer inicio de sesión.
                                        </p>
                                    </td>
                                </tr>
                            </table>
                            
                            <p style="color:#666666;font-size:14px;line-height:1.6;margin:25px 0 0 0;">
                                Saludos cordiales,<br>
                                <strong style="color:#002d54;">Sistema de Talento Humano</strong><br>
                                Academia Jotuns Club SAS
                            </p>
                        </td>
                    </tr>
                    <!-- Footer -->
                    <tr>
                        <td style="background-color:#002d54;padding:20px 40px;text-align:center;">
                            <p style="color:#a0c4e8;font-size:12px;margin:0;">
                                © 2026 Academia Jotuns Club SAS - Todos los derechos reservados
                            </p>
                            <p style="color:#6a9bc3;font-size:11px;margin:10px 0 0 0;">
                                Este correo fue enviado automáticamente, por favor no responda a este mensaje.
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>'''
        
        email_sent = await email_service.send_email(
            recipient_email=user_create.email,
            subject="🎉 Bienvenido al Sistema de Talento Humano - Academia Jotuns Club",
            body=email_body
        )
        if email_sent:
            print(f"✓ Welcome email sent to {user_create.email}")
        else:
            print(f"⚠ Welcome email NOT sent to {user_create.email}")
    except Exception as e:
        print(f"✗ Error sending welcome email to {user_create.email}: {e}")
    
    await audit_service.log(
        user_id=current_user.id,
        action="create_user",
        resource_type="user",
        resource_id=user_dict["id"],
        details={"email": user_create.email, "role": user_create.role}
    )
    
    # Return user without password and _id (MongoDB adds _id to the dict)
    return {
        "id": user_dict["id"],
        "email": user_dict["email"],
        "name": user_dict["name"],
        "role": user_dict["role"],
        "phone": user_dict.get("phone"),
        "identification": user_dict.get("identification"),
        "is_active": user_dict["is_active"],
        "created_at": user_dict["created_at"].isoformat(),
        "updated_at": user_dict["updated_at"].isoformat()
    }

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
        raise HTTPException(status_code=404, detail="Colaborador no encontrado")
    
    # Create contract with initial status pending_documents
    # (documents are now associated with the contract, not the user)
    contract_dict = contract_create.model_dump()
    contract_dict.update({
        "id": str(uuid.uuid4()),
        "status": ContractStatus.PENDING_DOCUMENTS,
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
        details={"collaborator_id": contract_create.collaborator_id, "title": contract_create.title}
    )
    
    # Send notification to collaborator
    await db.notifications.insert_one({
        "user_id": contract_create.collaborator_id,
        "title": "Nuevo Contrato Creado",
        "message": f"Se ha creado un nuevo contrato: {contract_create.title}. Por favor cargue los documentos requeridos.",
        "notification_type": "contract_created",
        "read": False,
        "created_at": datetime.now(timezone.utc)
    })
    
    # Send email with styled template
    email_content = f'''
    <p style="color:#333333;font-size:16px;line-height:1.6;margin:0 0 25px 0;">
        Estimado(a) <strong>{collaborator.get('name', 'Colaborador')}</strong>,
    </p>
    <p style="color:#333333;font-size:16px;line-height:1.6;margin:0 0 25px 0;">
        Se ha creado un nuevo contrato para usted: <strong>{contract_create.title}</strong>
    </p>
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color:#fff7ed;border-left:4px solid #f97316;border-radius:4px;margin:25px 0;">
        <tr>
            <td style="padding:15px 20px;">
                <p style="color:#9a3412;font-size:14px;margin:0;">
                    <strong>Acción requerida:</strong> Por favor ingrese al sistema y cargue los documentos requeridos para completar su proceso de contratación.
                </p>
            </td>
        </tr>
    </table>
    '''
    email_body = build_styled_email(
        title="Nuevo Contrato Creado",
        content=email_content,
        button_text="Ir al Sistema",
        button_url="https://th.academiajotuns.com"
    )
    await email_service.send_email(
        recipient_email=collaborator["email"],
        subject="📋 Nuevo Contrato Creado - Academia Jotuns Club",
        body=email_body
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
            "title": "Contrato Pendiente de Aprobación",
            "message": f"El contrato {contract['title']} requiere su aprobación",
            "notification_type": "contract_pending_approval",
            "read": False,
            "created_at": datetime.now(timezone.utc)
        })
        
        # Send styled email
        email_content = f'''
        <p style="color:#333333;font-size:16px;line-height:1.6;margin:0 0 25px 0;">
            Estimado(a) <strong>{legal_rep.get('name', 'Representante Legal')}</strong>,
        </p>
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color:#fef3c7;border-left:4px solid #f59e0b;border-radius:4px;margin:25px 0;">
            <tr>
                <td style="padding:15px 20px;">
                    <p style="color:#92400e;font-size:14px;margin:0;">
                        <strong>Acción requerida:</strong> El contrato <strong>{contract['title']}</strong> ha completado la revisión de documentos y requiere su aprobación final.
                    </p>
                </td>
            </tr>
        </table>
        <p style="color:#333333;font-size:16px;line-height:1.6;margin:0 0 25px 0;">
            Por favor ingrese al sistema para revisar y aprobar el contrato.
        </p>
        '''
        email_body = build_styled_email(
            title="Contrato Pendiente de Aprobación",
            content=email_content,
            button_text="Revisar Contrato",
            button_url="https://th.academiajotuns.com"
        )
        await email_service.send_email(
            recipient_email=legal_rep["email"],
            subject="📝 Contrato Pendiente de Aprobación - Academia Jotuns Club",
            body=email_body
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
    file: UploadFile = File(...),
    current_user: User = Depends(require_role(UserRole.LEGAL_REP))
):
    """Approve contract and upload the contract document for signing"""
    db = await get_database()
    
    contract = await db.contracts.find_one({"id": contract_id})
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    
    if contract["status"] != ContractStatus.PENDING_APPROVAL:
        raise HTTPException(status_code=400, detail="Contract is not pending approval")
    
    # Upload contract document
    file_content = await file.read()
    result = await storage_service.upload_file(
        file_content=file_content,
        file_name=f"contract_original_{contract_id}_{file.filename}",
        folder_path="SportsAdmin/Contracts"
    )
    
    if not result:
        raise HTTPException(status_code=500, detail="Failed to upload contract document")
    
    # Update status
    await db.contracts.update_one(
        {"id": contract_id},
        {"$set": {
            "status": ContractStatus.APPROVED,
            "approved_by": current_user.id,
            "contract_file_id": result["id"],
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
    
    # Send styled email
    email_content = f'''
    <p style="color:#333333;font-size:16px;line-height:1.6;margin:0 0 25px 0;">
        Estimado(a) <strong>{collaborator.get('name', 'Colaborador')}</strong>,
    </p>
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color:#ecfdf5;border-left:4px solid #10b981;border-radius:4px;margin:25px 0;">
        <tr>
            <td style="padding:15px 20px;">
                <p style="color:#065f46;font-size:16px;margin:0;font-weight:bold;">
                    ✓ Su contrato "{contract['title']}" ha sido aprobado
                </p>
            </td>
        </tr>
    </table>
    <p style="color:#333333;font-size:16px;line-height:1.6;margin:0 0 25px 0;">
        Para completar el proceso de contratación, por favor siga estos pasos:
    </p>
    <ol style="color:#333333;font-size:16px;line-height:1.8;margin:0 0 25px 0;padding-left:20px;">
        <li>Ingrese al sistema</li>
        <li>Descargue el documento del contrato</li>
        <li>Imprima, firme y escanee el documento</li>
        <li>Cargue el documento firmado en el sistema</li>
    </ol>
    '''
    email_body = build_styled_email(
        title="¡Contrato Aprobado!",
        content=email_content,
        button_text="Ir a Firmar Contrato",
        button_url="https://th.academiajotuns.com"
    )
    await email_service.send_email(
        recipient_email=collaborator["email"],
        subject="✓ Contrato Aprobado - Academia Jotuns Club",
        body=email_body
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
    result = await storage_service.upload_file(
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

# Documentos obligatorios y opcionales
REQUIRED_DOCUMENTS = [
    DocumentType.CEDULA,
    DocumentType.RUT,
    DocumentType.CERT_BANCARIA,
    DocumentType.ANTECEDENTES,
    DocumentType.HOJA_VIDA,
    DocumentType.PROPUESTA_TRABAJO
]

OPTIONAL_DOCUMENTS = [
    DocumentType.SOPORTES_LABORALES,
    DocumentType.SOPORTES_EDUCATIVOS,
    DocumentType.TARJETA_ENTRENADOR
]

DOCUMENT_LABELS = {
    "cedula": "Cédula de Ciudadanía",
    "rut": "RUT",
    "soportes_laborales": "Soportes Laborales",
    "soportes_educativos": "Soportes Educativos",
    "cert_bancaria": "Certificación Bancaria",
    "antecedentes": "Antecedentes",
    "tarjeta_entrenador": "Tarjeta de Entrenador Deportivo / Registro Provisional",
    "hoja_vida": "Hoja de Vida",
    "propuesta_trabajo": "Propuesta de Trabajo"
}

@app.get("/api/contracts/{contract_id}/documents")
async def get_contract_documents(
    contract_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get all documents for a contract with status info"""
    db = await get_database()
    
    # Verify contract exists and user has access
    contract = await db.contracts.find_one({"id": contract_id})
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    
    if current_user.role == UserRole.COLLABORATOR and contract["collaborator_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get uploaded documents for this contract
    documents = await db.documents.find({"contract_id": contract_id}, {"_id": 0}).to_list(100)
    doc_map = {doc["document_type"]: doc for doc in documents}
    
    # Build response with all required and optional documents
    result = {
        "contract_id": contract_id,
        "required_documents": [],
        "optional_documents": [],
        "all_required_approved": True,
        "can_approve_contract": False
    }
    
    for doc_type in REQUIRED_DOCUMENTS:
        doc_info = {
            "type": doc_type.value,
            "label": DOCUMENT_LABELS.get(doc_type.value, doc_type.value),
            "required": True,
            "uploaded": False,
            "status": None,
            "document": None
        }
        if doc_type.value in doc_map:
            doc = doc_map[doc_type.value]
            doc_info["uploaded"] = True
            doc_info["status"] = doc["status"]
            doc_info["document"] = doc
            if doc["status"] != "approved":
                result["all_required_approved"] = False
        else:
            result["all_required_approved"] = False
        result["required_documents"].append(doc_info)
    
    for doc_type in OPTIONAL_DOCUMENTS:
        doc_info = {
            "type": doc_type.value,
            "label": DOCUMENT_LABELS.get(doc_type.value, doc_type.value),
            "required": False,
            "uploaded": False,
            "status": None,
            "document": None
        }
        if doc_type.value in doc_map:
            doc = doc_map[doc_type.value]
            doc_info["uploaded"] = True
            doc_info["status"] = doc["status"]
            doc_info["document"] = doc
        result["optional_documents"].append(doc_info)
    
    # Can approve contract if all required documents are approved
    result["can_approve_contract"] = result["all_required_approved"]
    
    return result

@app.post("/api/contracts/{contract_id}/documents", status_code=status.HTTP_201_CREATED)
async def upload_contract_document(
    contract_id: str,
    document_type: DocumentType,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Upload a document for a specific contract"""
    db = await get_database()
    
    # Verify contract exists
    contract = await db.contracts.find_one({"id": contract_id})
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    
    # Verify user is the collaborator of this contract
    if current_user.role == UserRole.COLLABORATOR and contract["collaborator_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Check if document already exists for this contract
    existing_doc = await db.documents.find_one({
        "contract_id": contract_id,
        "document_type": document_type
    })
    
    # Upload file
    file_content = await file.read()
    result = await storage_service.upload_file(
        file_content=file_content,
        file_name=f"doc_{contract_id}_{document_type.value}_{file.filename}",
        folder_path="SportsAdmin/Documents"
    )
    
    if not result:
        raise HTTPException(status_code=500, detail="Failed to upload file")
    
    if existing_doc:
        # Update existing document
        await db.documents.update_one(
            {"id": existing_doc["id"]},
            {"$set": {
                "file_name": file.filename,
                "file_id": result["id"],
                "status": DocumentStatus.UPLOADED,
                "review_notes": None,
                "reviewed_by": None,
                "updated_at": datetime.now(timezone.utc)
            }}
        )
        doc_id = existing_doc["id"]
    else:
        # Create new document
        doc_dict = {
            "id": str(uuid.uuid4()),
            "document_type": document_type,
            "contract_id": contract_id,
            "file_name": file.filename,
            "file_id": result["id"],
            "status": DocumentStatus.UPLOADED,
            "uploaded_by": current_user.id,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        await db.documents.insert_one(doc_dict)
        doc_id = doc_dict["id"]
    
    # Update contract status if it was pending_documents
    if contract["status"] == ContractStatus.PENDING_DOCUMENTS:
        # Check if all required documents are now uploaded
        docs = await db.documents.find({"contract_id": contract_id}, {"_id": 0}).to_list(100)
        uploaded_types = {doc["document_type"] for doc in docs}
        required_types = {dt.value for dt in REQUIRED_DOCUMENTS}
        
        if required_types.issubset(uploaded_types):
            await db.contracts.update_one(
                {"id": contract_id},
                {"$set": {"status": ContractStatus.UNDER_REVIEW, "updated_at": datetime.now(timezone.utc)}}
            )
    
    # Notify admins
    admins = await db.users.find({"role": UserRole.ADMIN}).to_list(100)
    for admin in admins:
        await db.notifications.insert_one({
            "user_id": admin["id"],
            "title": "Documento Cargado",
            "message": f"Documento {DOCUMENT_LABELS.get(document_type.value, document_type.value)} cargado para contrato: {contract['title']}",
            "notification_type": "document_uploaded",
            "read": False,
            "created_at": datetime.now(timezone.utc)
        })
    
    await audit_service.log(
        user_id=current_user.id,
        action="upload_contract_document",
        resource_type="document",
        resource_id=doc_id,
        details={"contract_id": contract_id, "document_type": document_type.value}
    )
    
    return {"message": "Document uploaded successfully", "document_id": doc_id}

def build_styled_email(title: str, content: str, button_text: str = None, button_url: str = None) -> str:
    """Build a professionally styled HTML email template"""
    button_html = ""
    if button_text and button_url:
        button_html = f'''
        <table role="presentation" cellspacing="0" cellpadding="0" border="0" style="margin:30px 0;">
            <tr>
                <td style="background-color:#002d54;border-radius:6px;">
                    <a href="{button_url}" style="display:inline-block;padding:15px 35px;color:#ffffff;text-decoration:none;font-size:16px;font-weight:bold;">{button_text}</a>
                </td>
            </tr>
        </table>
        '''
    
    return f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin:0;padding:0;background-color:#f4f4f4;font-family:Arial,Helvetica,sans-serif;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color:#f4f4f4;">
        <tr>
            <td align="center" style="padding:20px 0;">
                <table role="presentation" width="600" cellspacing="0" cellpadding="0" border="0" style="background-color:#ffffff;border-radius:8px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.1);">
                    <!-- Header -->
                    <tr>
                        <td style="background-color:#002d54;padding:30px 40px;text-align:center;">
                            <h1 style="color:#ffffff;margin:0;font-size:24px;font-weight:bold;">Sistema de Talento Humano</h1>
                            <p style="color:#a0c4e8;margin:8px 0 0 0;font-size:14px;">Academia Jotuns Club SAS</p>
                        </td>
                    </tr>
                    <!-- Content -->
                    <tr>
                        <td style="padding:40px;">
                            <h2 style="color:#002d54;margin:0 0 20px 0;font-size:22px;">{title}</h2>
                            {content}
                            {button_html}
                            <p style="color:#666666;font-size:14px;line-height:1.6;margin:25px 0 0 0;">
                                Saludos cordiales,<br>
                                <strong style="color:#002d54;">Sistema de Talento Humano</strong><br>
                                Academia Jotuns Club SAS
                            </p>
                        </td>
                    </tr>
                    <!-- Footer -->
                    <tr>
                        <td style="background-color:#002d54;padding:20px 40px;text-align:center;">
                            <p style="color:#a0c4e8;font-size:12px;margin:0;">
                                © 2026 Academia Jotuns Club SAS - Todos los derechos reservados
                            </p>
                            <p style="color:#6a9bc3;font-size:11px;margin:10px 0 0 0;">
                                Este correo fue enviado automáticamente, por favor no responda a este mensaje.
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>'''

@app.put("/api/documents/{document_id}/review")
async def review_document(
    document_id: str,
    document_update: DocumentUpdate,
    current_user: User = Depends(require_role(UserRole.ADMIN))
):
    """Review and approve/reject a document"""
    db = await get_database()
    
    document = await db.documents.find_one({"id": document_id})
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    update_data = document_update.model_dump(exclude_unset=True)
    update_data["reviewed_by"] = current_user.id
    update_data["updated_at"] = datetime.now(timezone.utc)
    
    await db.documents.update_one(
        {"id": document_id},
        {"$set": update_data}
    )
    
    # Get contract and collaborator to notify
    contract = await db.contracts.find_one({"id": document["contract_id"]})
    if contract:
        collaborator = await db.users.find_one({"id": contract["collaborator_id"]})
        doc_label = DOCUMENT_LABELS.get(document['document_type'], document['document_type'])
        new_status = update_data.get('status', 'revisado')
        
        # Create notification (always)
        if new_status == 'approved':
            notification_msg = f"Su documento '{doc_label}' ha sido APROBADO."
        elif new_status == 'rejected':
            review_notes = update_data.get('review_notes', 'Sin observaciones')
            notification_msg = f"Su documento '{doc_label}' ha sido RECHAZADO. Observación: {review_notes}. Por favor corrija y vuelva a cargar el documento."
        else:
            notification_msg = f"Su documento '{doc_label}' ha sido revisado."
        
        await db.notifications.insert_one({
            "user_id": contract["collaborator_id"],
            "title": "Documento Revisado",
            "message": notification_msg,
            "notification_type": "document_reviewed",
            "read": False,
            "created_at": datetime.now(timezone.utc)
        })
        
        # Send email ONLY when document is REJECTED (not for individual approvals)
        if collaborator and collaborator.get("email") and new_status == 'rejected':
            review_notes = update_data.get('review_notes', 'Sin observaciones específicas')
            email_content = f'''
            <p style="color:#333333;font-size:16px;line-height:1.6;margin:0 0 25px 0;">
                Estimado(a) <strong>{collaborator.get('name', 'Colaborador')}</strong>,
            </p>
            <p style="color:#333333;font-size:16px;line-height:1.6;margin:0 0 25px 0;">
                Le informamos que su documento <strong>{doc_label}</strong> del contrato <strong>{contract['title']}</strong> ha sido <span style="color:#dc2626;font-weight:bold;">RECHAZADO</span>.
            </p>
            <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color:#fef2f2;border-left:4px solid #dc2626;border-radius:4px;margin:25px 0;">
                <tr>
                    <td style="padding:15px 20px;">
                        <p style="color:#991b1b;font-size:14px;margin:0;">
                            <strong>Motivo del rechazo:</strong><br>
                            {review_notes}
                        </p>
                    </td>
                </tr>
            </table>
            <p style="color:#333333;font-size:16px;line-height:1.6;margin:0 0 25px 0;">
                Por favor ingrese al sistema, corrija el documento según las observaciones indicadas y vuelva a cargarlo.
            </p>
            '''
            email_body = build_styled_email(
                title="Documento Rechazado - Acción Requerida",
                content=email_content,
                button_text="Ir al Sistema",
                button_url="https://th.academiajotuns.com"
            )
            await email_service.send_email(
                recipient_email=collaborator["email"],
                subject=f"⚠️ Documento Rechazado - {doc_label}",
                body=email_body
            )
        
        # Check if all required documents are now approved
        if new_status == "approved":
            docs = await db.documents.find({"contract_id": contract["id"]}, {"_id": 0}).to_list(100)
            required_types = {dt.value for dt in REQUIRED_DOCUMENTS}
            approved_required = sum(1 for doc in docs if doc["document_type"] in required_types and doc["status"] == "approved")
            
            if approved_required >= len(required_types):
                # All required docs approved, move to pending_approval
                if contract["status"] == ContractStatus.UNDER_REVIEW:
                    await db.contracts.update_one(
                        {"id": contract["id"]},
                        {"$set": {"status": ContractStatus.PENDING_APPROVAL, "updated_at": datetime.now(timezone.utc)}}
                    )
                    
                    # Send email ONLY when ALL required documents are approved
                    if collaborator and collaborator.get("email"):
                        email_content = f'''
                        <p style="color:#333333;font-size:16px;line-height:1.6;margin:0 0 25px 0;">
                            Estimado(a) <strong>{collaborator.get('name', 'Colaborador')}</strong>,
                        </p>
                        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color:#ecfdf5;border-left:4px solid #10b981;border-radius:4px;margin:25px 0;">
                            <tr>
                                <td style="padding:15px 20px;">
                                    <p style="color:#065f46;font-size:16px;margin:0;font-weight:bold;">
                                        ✓ Todos sus documentos obligatorios han sido aprobados
                                    </p>
                                </td>
                            </tr>
                        </table>
                        <p style="color:#333333;font-size:16px;line-height:1.6;margin:0 0 25px 0;">
                            Le informamos que todos los documentos requeridos para el contrato <strong>{contract['title']}</strong> han sido revisados y aprobados exitosamente.
                        </p>
                        <p style="color:#333333;font-size:16px;line-height:1.6;margin:0 0 25px 0;">
                            Su contrato ahora está <strong>pendiente de aprobación final</strong> por parte del Representante Legal. Le notificaremos cuando el proceso esté completo.
                        </p>
                        '''
                        email_body = build_styled_email(
                            title="¡Documentos Completos!",
                            content=email_content,
                            button_text="Ver Estado del Contrato",
                            button_url="https://th.academiajotuns.com"
                        )
                        await email_service.send_email(
                            recipient_email=collaborator["email"],
                            subject=f"✓ Documentos Completos - Contrato {contract['title']}",
                            body=email_body
                        )
    
    await audit_service.log(
        user_id=current_user.id,
        action="review_document",
        resource_type="document",
        resource_id=document_id,
        details={"status": update_data.get("status"), "review_notes": update_data.get("review_notes")}
    )
    
    updated_doc = await db.documents.find_one({"id": document_id}, {"_id": 0})
    return updated_doc

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
    
    return documents

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
    result = await storage_service.upload_file(
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
        
        # Send styled email
        email_content = f'''
        <p style="color:#333333;font-size:16px;line-height:1.6;margin:0 0 25px 0;">
            Estimado(a) <strong>{accountant.get('name', 'Contador')}</strong>,
        </p>
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color:#fef3c7;border-left:4px solid #f59e0b;border-radius:4px;margin:25px 0;">
            <tr>
                <td style="padding:15px 20px;">
                    <p style="color:#92400e;font-size:14px;margin:0;">
                        <strong>Nueva cuenta de cobro:</strong> Se ha recibido una cuenta de cobro por <strong>${payment['amount']:,.0f} COP</strong> que requiere su revisión y aprobación.
                    </p>
                </td>
            </tr>
        </table>
        <p style="color:#333333;font-size:16px;line-height:1.6;margin:0 0 25px 0;">
            Por favor ingrese al sistema para revisar y aprobar o rechazar la cuenta de cobro.
        </p>
        '''
        email_body = build_styled_email(
            title="Nueva Cuenta de Cobro Pendiente",
            content=email_content,
            button_text="Revisar Cuenta de Cobro",
            button_url="https://th.academiajotuns.com"
        )
        await email_service.send_email(
            recipient_email=accountant["email"],
            subject="💰 Nueva Cuenta de Cobro - Academia Jotuns Club",
            body=email_body
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
    collaborator = await db.users.find_one({"id": contract["collaborator_id"]})
    
    await db.notifications.insert_one({
        "user_id": contract["collaborator_id"],
        "title": "Cuenta de Cobro Aprobada",
        "message": f"Su cuenta de cobro por ${payment['amount']} ha sido aprobada",
        "notification_type": "payment_approved",
        "read": False,
        "created_at": datetime.now(timezone.utc)
    })
    
    # Send styled email
    email_content = f'''
    <p style="color:#333333;font-size:16px;line-height:1.6;margin:0 0 25px 0;">
        Estimado(a) <strong>{collaborator.get('name', 'Colaborador')}</strong>,
    </p>
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color:#ecfdf5;border-left:4px solid #10b981;border-radius:4px;margin:25px 0;">
        <tr>
            <td style="padding:15px 20px;">
                <p style="color:#065f46;font-size:16px;margin:0;font-weight:bold;">
                    ✓ Su cuenta de cobro por ${payment['amount']:,.0f} COP ha sido aprobada
                </p>
            </td>
        </tr>
    </table>
    <p style="color:#333333;font-size:16px;line-height:1.6;margin:0 0 25px 0;">
        Su pago está siendo procesado. Le notificaremos cuando el pago se haya completado y el comprobante esté disponible.
    </p>
    '''
    email_body = build_styled_email(
        title="Cuenta de Cobro Aprobada",
        content=email_content,
        button_text="Ver Estado del Pago",
        button_url="https://th.academiajotuns.com"
    )
    await email_service.send_email(
        recipient_email=collaborator["email"],
        subject="✓ Cuenta de Cobro Aprobada - Academia Jotuns Club",
        body=email_body
    )
    
    await audit_service.log(
        user_id=current_user.id,
        action="approve_payment",
        resource_type="payment",
        resource_id=payment_id
    )
    
    return {"message": "Payment approved successfully"}

@app.post("/api/payments/{payment_id}/reject")
async def reject_payment(
    payment_id: str,
    rejection_reason: str,
    current_user: User = Depends(require_role(UserRole.ACCOUNTANT))
):
    """Reject payment - accountant rejects cuenta de cobro with reason"""
    db = await get_database()
    
    payment = await db.payments.find_one({"id": payment_id})
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    if payment["status"] != PaymentStatus.PENDING_APPROVAL:
        raise HTTPException(status_code=400, detail="Payment is not pending approval")
    
    # Update payment to rejected with reason
    await db.payments.update_one(
        {"id": payment_id},
        {"$set": {
            "status": PaymentStatus.REJECTED,
            "rejection_reason": rejection_reason,
            "rejected_by": current_user.id,
            "updated_at": datetime.now(timezone.utc)
        }}
    )
    
    # Notify collaborator
    contract = await db.contracts.find_one({"id": payment["contract_id"]})
    collaborator = await db.users.find_one({"id": contract["collaborator_id"]})
    
    await db.notifications.insert_one({
        "user_id": contract["collaborator_id"],
        "title": "Cuenta de Cobro Rechazada",
        "message": f"Su cuenta de cobro por ${payment['amount']} fue rechazada. Motivo: {rejection_reason}",
        "notification_type": "payment_rejected",
        "read": False,
        "created_at": datetime.now(timezone.utc)
    })
    
    await email_service.send_email(
        recipient_email=collaborator["email"],
        subject="Cuenta de Cobro Rechazada - Jotuns Club",
        body=f"<h2>Cuenta de Cobro Rechazada</h2><p>Su cuenta de cobro por <strong>${payment['amount']}</strong> fue rechazada.</p><p><strong>Motivo:</strong> {rejection_reason}</p><p>Por favor corrija y vuelva a cargar la cuenta de cobro.</p>"
    )
    
    await audit_service.log(
        user_id=current_user.id,
        action="reject_payment",
        resource_type="payment",
        resource_id=payment_id,
        details={"reason": rejection_reason}
    )
    
    return {"message": "Payment rejected successfully"}

@app.post("/api/payments/{payment_id}/confirm")
async def confirm_payment(
    payment_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(require_role(UserRole.ACCOUNTANT))
):
    """Confirm payment with voucher (comprobante de pago)"""
    db = await get_database()
    
    payment = await db.payments.find_one({"id": payment_id})
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    if payment["status"] != PaymentStatus.APPROVED:
        raise HTTPException(status_code=400, detail="Payment must be approved first")
    
    # Upload voucher to OneDrive
    file_content = await file.read()
    result = await storage_service.upload_file(
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
            "confirmed_by": current_user.id,
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
        subject="Pago Procesado - Jotuns Club",
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
            "status": {"$in": [PaymentStatus.DRAFT, PaymentStatus.PENDING_APPROVAL, PaymentStatus.APPROVED]}
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
        "status": {"$in": [PaymentStatus.DRAFT, PaymentStatus.PENDING_APPROVAL, PaymentStatus.APPROVED]}
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
        "status": {"$in": [PaymentStatus.DRAFT, PaymentStatus.PENDING_APPROVAL, PaymentStatus.APPROVED]}
    }, {"_id": 0}).to_list(1000)
    
    return {"payments": [Payment(**p) for p in payments]}

# ============= EXPORT REPORTS =============

@app.get("/api/reports/export/contracts")
async def export_contracts_excel(
    token: str,
    status: Optional[str] = None
):
    """Export contracts report to Excel"""
    from fastapi.responses import StreamingResponse
    import xlsxwriter
    import io
    
    # Verify token and role
    current_user = await get_user_from_token(token)
    if not auth_service.has_permission(current_user.role, UserRole.ADMIN):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    db = await get_database()
    
    query = {}
    if status:
        query["status"] = status
    
    contracts = await db.contracts.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    
    # Get collaborator names
    collaborator_ids = list(set([c.get("collaborator_id") for c in contracts if c.get("collaborator_id")]))
    collaborators = await db.users.find({"id": {"$in": collaborator_ids}}, {"_id": 0, "id": 1, "name": 1}).to_list(1000)
    collab_map = {c["id"]: c["name"] for c in collaborators}
    
    # Create Excel file in memory
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    worksheet = workbook.add_worksheet('Contratos')
    
    # Styles
    header_format = workbook.add_format({'bold': True, 'bg_color': '#002d54', 'font_color': 'white', 'border': 1})
    cell_format = workbook.add_format({'border': 1})
    date_format = workbook.add_format({'border': 1, 'num_format': 'dd/mm/yyyy'})
    money_format = workbook.add_format({'border': 1, 'num_format': '$#,##0'})
    
    # Headers
    headers = ['ID', 'Título', 'Colaborador', 'Tipo', 'Estado', 'Fecha Inicio', 'Fecha Fin', 'Pago Mensual', 'Pago por Sesión', 'Creado']
    for col, header in enumerate(headers):
        worksheet.write(0, col, header, header_format)
    
    # Data
    status_labels = {
        'draft': 'Borrador', 'pending_documents': 'Pendiente Docs', 'under_review': 'En Revisión',
        'pending_approval': 'Pendiente Aprobación', 'approved': 'Aprobado', 'pending_signature': 'Pendiente Firma',
        'signed': 'Firmado', 'active': 'Activo', 'completed': 'Completado', 'cancelled': 'Cancelado'
    }
    type_labels = {'service': 'Prestación de Servicios', 'event': 'Por Evento'}
    
    for row, contract in enumerate(contracts, start=1):
        worksheet.write(row, 0, contract.get("id", "")[:8], cell_format)
        worksheet.write(row, 1, contract.get("title", ""), cell_format)
        worksheet.write(row, 2, collab_map.get(contract.get("collaborator_id"), "N/A"), cell_format)
        worksheet.write(row, 3, type_labels.get(contract.get("contract_type"), ""), cell_format)
        worksheet.write(row, 4, status_labels.get(contract.get("status"), contract.get("status", "")), cell_format)
        
        start_date = contract.get("start_date")
        if start_date:
            worksheet.write_datetime(row, 5, start_date if hasattr(start_date, 'date') else datetime.fromisoformat(str(start_date).replace('Z', '+00:00')), date_format)
        else:
            worksheet.write(row, 5, "", cell_format)
        
        end_date = contract.get("end_date")
        if end_date:
            worksheet.write_datetime(row, 6, end_date if hasattr(end_date, 'date') else datetime.fromisoformat(str(end_date).replace('Z', '+00:00')), date_format)
        else:
            worksheet.write(row, 6, "", cell_format)
        
        worksheet.write(row, 7, contract.get("monthly_payment") or 0, money_format)
        worksheet.write(row, 8, contract.get("payment_per_session") or 0, money_format)
        
        created_at = contract.get("created_at")
        if created_at:
            worksheet.write_datetime(row, 9, created_at if hasattr(created_at, 'date') else datetime.fromisoformat(str(created_at).replace('Z', '+00:00')), date_format)
        else:
            worksheet.write(row, 9, "", cell_format)
    
    # Adjust column widths
    worksheet.set_column(0, 0, 10)
    worksheet.set_column(1, 1, 30)
    worksheet.set_column(2, 2, 25)
    worksheet.set_column(3, 4, 20)
    worksheet.set_column(5, 6, 12)
    worksheet.set_column(7, 8, 15)
    worksheet.set_column(9, 9, 12)
    
    workbook.close()
    output.seek(0)
    
    filename = f"contratos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    
    return StreamingResponse(
        output,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'}
    )

@app.get("/api/reports/export/payments")
async def export_payments_excel(
    token: str,
    status: Optional[str] = None
):
    """Export payments report to Excel"""
    from fastapi.responses import StreamingResponse
    import xlsxwriter
    import io
    
    # Verify token and role
    current_user = await get_user_from_token(token)
    if not auth_service.has_permission(current_user.role, UserRole.ACCOUNTANT):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    db = await get_database()
    
    query = {}
    if status:
        query["status"] = status
    
    payments = await db.payments.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    
    # Get contract info
    contract_ids = list(set([p.get("contract_id") for p in payments if p.get("contract_id")]))
    contracts = await db.contracts.find({"id": {"$in": contract_ids}}, {"_id": 0, "id": 1, "title": 1, "collaborator_id": 1}).to_list(1000)
    contract_map = {c["id"]: c for c in contracts}
    
    # Get collaborator names
    collaborator_ids = list(set([c.get("collaborator_id") for c in contracts if c.get("collaborator_id")]))
    collaborators = await db.users.find({"id": {"$in": collaborator_ids}}, {"_id": 0, "id": 1, "name": 1}).to_list(1000)
    collab_map = {c["id"]: c["name"] for c in collaborators}
    
    # Create Excel file
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    worksheet = workbook.add_worksheet('Pagos')
    
    # Styles
    header_format = workbook.add_format({'bold': True, 'bg_color': '#002d54', 'font_color': 'white', 'border': 1})
    cell_format = workbook.add_format({'border': 1})
    date_format = workbook.add_format({'border': 1, 'num_format': 'dd/mm/yyyy'})
    money_format = workbook.add_format({'border': 1, 'num_format': '$#,##0'})
    
    # Headers
    headers = ['ID', 'Contrato', 'Colaborador', 'Monto', 'Estado', 'Descripción', 'Fecha Pago', 'Motivo Rechazo', 'Creado']
    for col, header in enumerate(headers):
        worksheet.write(0, col, header, header_format)
    
    # Data
    status_labels = {
        'draft': 'Borrador', 'pending_approval': 'Pendiente Aprobación', 
        'approved': 'Aprobado', 'paid': 'Pagado', 'rejected': 'Rechazado', 'cancelled': 'Cancelado'
    }
    
    for row, payment in enumerate(payments, start=1):
        contract = contract_map.get(payment.get("contract_id"), {})
        collaborator_name = collab_map.get(contract.get("collaborator_id"), "N/A")
        
        worksheet.write(row, 0, payment.get("id", "")[:8], cell_format)
        worksheet.write(row, 1, contract.get("title", "N/A"), cell_format)
        worksheet.write(row, 2, collaborator_name, cell_format)
        worksheet.write(row, 3, payment.get("amount", 0), money_format)
        worksheet.write(row, 4, status_labels.get(payment.get("status"), payment.get("status", "")), cell_format)
        worksheet.write(row, 5, payment.get("description", ""), cell_format)
        
        payment_date = payment.get("payment_date")
        if payment_date:
            worksheet.write_datetime(row, 6, payment_date if hasattr(payment_date, 'date') else datetime.fromisoformat(str(payment_date).replace('Z', '+00:00')), date_format)
        else:
            worksheet.write(row, 6, "", cell_format)
        
        worksheet.write(row, 7, payment.get("rejection_reason", ""), cell_format)
        
        created_at = payment.get("created_at")
        if created_at:
            worksheet.write_datetime(row, 8, created_at if hasattr(created_at, 'date') else datetime.fromisoformat(str(created_at).replace('Z', '+00:00')), date_format)
        else:
            worksheet.write(row, 8, "", cell_format)
    
    # Adjust column widths
    worksheet.set_column(0, 0, 10)
    worksheet.set_column(1, 1, 30)
    worksheet.set_column(2, 2, 25)
    worksheet.set_column(3, 3, 15)
    worksheet.set_column(4, 4, 20)
    worksheet.set_column(5, 5, 30)
    worksheet.set_column(6, 6, 12)
    worksheet.set_column(7, 7, 30)
    worksheet.set_column(8, 8, 12)
    
    workbook.close()
    output.seek(0)
    
    filename = f"pagos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    
    return StreamingResponse(
        output,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'}
    )

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

@app.get("/api/files/download/{file_id}")
async def download_file(file_id: str, token: Optional[str] = None, current_user: User = Depends(get_current_user)):
    """Download file from storage"""
    from fastapi.responses import FileResponse
    
    file_path = await storage_service.get_file_path(file_id)
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=file_path,
        filename=os.path.basename(file_path),
        media_type='application/octet-stream'
    )

@app.get("/api/files/view/{file_id}")
async def view_file(file_id: str, token: str):
    """View/download file using token in query parameter (for opening in new tab)"""
    from fastapi.responses import FileResponse
    
    # Verify token
    payload = auth_service.decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    db = await get_database()
    user_data = await db.users.find_one({"id": payload["sub"]})
    if not user_data or not user_data.get("is_active"):
        raise HTTPException(status_code=401, detail="User not found or inactive")
    
    file_path = await storage_service.get_file_path(file_id)
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    # Determine media type based on extension
    ext = os.path.splitext(file_path)[1].lower()
    media_types = {
        '.pdf': 'application/pdf',
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
    }
    media_type = media_types.get(ext, 'application/octet-stream')
    
    return FileResponse(
        path=file_path,
        filename=os.path.basename(file_path),
        media_type=media_type
    )
