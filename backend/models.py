from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    SUPERADMIN = "superadmin"
    ADMIN = "admin"
    LEGAL_REP = "legal_rep"
    ACCOUNTANT = "accountant"
    COLLABORATOR = "collaborator"

class ContractType(str, Enum):
    SERVICE = "service"  # Prestación de servicios
    EVENT = "event"  # Por sesión o evento

class ContractStatus(str, Enum):
    DRAFT = "draft"
    PENDING_DOCUMENTS = "pending_documents"
    UNDER_REVIEW = "under_review"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    PENDING_SIGNATURE = "pending_signature"
    SIGNED = "signed"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class DocumentType(str, Enum):
    CEDULA = "cedula"
    RUT = "rut"
    SOPORTES_LABORALES = "soportes_laborales"
    SOPORTES_EDUCATIVOS = "soportes_educativos"
    CERT_BANCARIA = "cert_bancaria"
    ANTECEDENTES = "antecedentes"
    TARJETA_ENTRENADOR = "tarjeta_entrenador"
    HOJA_VIDA = "hoja_vida"
    PROPUESTA_TRABAJO = "propuesta_trabajo"

class DocumentStatus(str, Enum):
    PENDING = "pending"
    UPLOADED = "uploaded"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"

class PaymentStatus(str, Enum):
    DRAFT = "draft"  # Colaborador está creando la cuenta de cobro
    PENDING_APPROVAL = "pending_approval"  # Cuenta de cobro cargada, esperando aprobación
    APPROVED = "approved"  # Aprobado por contador
    PAID = "paid"  # Pagado con comprobante
    REJECTED = "rejected"  # Rechazado
    CANCELLED = "cancelled"

# User Models
class UserBase(BaseModel):
    email: EmailStr
    name: str
    role: UserRole
    identification: Optional[str] = None
    phone: Optional[str] = None
    is_active: bool = True

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None

class User(UserBase):
    id: str
    created_at: datetime
    updated_at: datetime

class UserLogin(BaseModel):
    email: EmailStr
    password: str

# Contract Models
class ContractBase(BaseModel):
    contract_type: ContractType
    collaborator_id: str
    title: str
    description: str
    start_date: datetime
    end_date: Optional[datetime] = None
    monthly_payment: Optional[float] = None
    payment_per_session: Optional[float] = None
    notes: Optional[str] = None

class ContractCreate(ContractBase):
    pass

class ContractUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    monthly_payment: Optional[float] = None
    payment_per_session: Optional[float] = None
    notes: Optional[str] = None

class Contract(ContractBase):
    id: str
    status: ContractStatus
    created_by: str
    approved_by: Optional[str] = None
    contract_file_id: Optional[str] = None  # Documento del contrato para firmar
    signed_file_id: Optional[str] = None    # Documento firmado por el colaborador
    created_at: datetime
    updated_at: datetime

# Document Models
class DocumentBase(BaseModel):
    document_type: DocumentType
    contract_id: str  # Asociado al contrato, no al usuario
    file_name: str
    expiry_date: Optional[datetime] = None

class DocumentCreate(DocumentBase):
    file_id: str

class DocumentUpdate(BaseModel):
    status: Optional[DocumentStatus] = None
    expiry_date: Optional[datetime] = None
    review_notes: Optional[str] = None

class Document(DocumentBase):
    id: str
    status: DocumentStatus
    file_id: str
    uploaded_by: str  # Usuario que subió el documento
    reviewed_by: Optional[str] = None
    review_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

# Lista de documentos obligatorios para un contrato
REQUIRED_DOCUMENTS = [
    DocumentType.CEDULA,
    DocumentType.RUT,
    DocumentType.CERT_BANCARIA,
    DocumentType.ANTECEDENTES
]

OPTIONAL_DOCUMENTS = [
    DocumentType.CERT_LABORAL,
    DocumentType.CERT_EDUCATIVA,
    DocumentType.LICENCIA
]

# Payment Models
class PaymentBase(BaseModel):
    contract_id: str
    amount: float
    payment_date: datetime
    description: Optional[str] = None

class PaymentCreate(PaymentBase):
    pass

class PaymentUpdate(BaseModel):
    status: Optional[PaymentStatus] = None
    payment_date: Optional[datetime] = None
    voucher_file_id: Optional[str] = None

class Payment(PaymentBase):
    id: str
    status: PaymentStatus
    created_by: str
    bill_file_id: Optional[str] = None
    voucher_file_id: Optional[str] = None
    approved_by: Optional[str] = None
    rejected_by: Optional[str] = None
    rejection_reason: Optional[str] = None
    confirmed_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime

# Audit Log Model
class AuditLog(BaseModel):
    user_id: str
    action: str
    resource_type: str
    resource_id: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime
    ip_address: Optional[str] = None

# Notification Model
class Notification(BaseModel):
    user_id: str
    title: str
    message: str
    notification_type: str
    read: bool = False
    created_at: datetime

# Dashboard Stats
class DashboardStats(BaseModel):
    total_contracts: int
    pending_contracts: int
    active_contracts: int
    pending_approvals: int
    pending_documents: int
    expiring_documents: int
    pending_payments: int
    total_collaborators: int
