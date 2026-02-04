from pydantic import BaseModel
from typing import Optional

class QuotationCreate(BaseModel):
    account_id: int
    title: str
    amount: float
    tax_amount: float = 0

class InvoiceCreate(BaseModel):
    account_id: int
    description: str
    amount: float
    invoice_type: str = "Standard"
    tax_amount: float = 0

class ServiceAccountCreate(BaseModel):
    account_id: int
    warranty_status: str = "Active"
    service_level: str = "Silver"

class WarrantyExtensionCreate(BaseModel):
    service_account_id: int
    extension_start_date: str
    extension_end_date: str
    extension_cost: float = 0

class SLACreate(BaseModel):
    service_account_id: int
    name: str
    response_time_hours: int
    resolution_time_hours: int
    uptime_percentage: float = 99.9
    support_hours: str = "24/7"

class ServiceAppointmentCreate(BaseModel):
    account_id: Optional[int] = None
    case_id: Optional[int] = None
    subject: str
    description: Optional[str] = None
    appointment_type: str = "Field Service"
    scheduled_start: Optional[str] = None
    scheduled_end: Optional[str] = None
    priority: str = "Normal"
    location: Optional[str] = None
    required_skills: Optional[str] = None
    required_parts: Optional[str] = None

class WorkOrderCreate(BaseModel):
    account_id: Optional[int] = None
    case_id: Optional[int] = None
    subject: str
    description: Optional[str] = None
    priority: str = "Medium"
    service_type: str = "Warranty"
    product: Optional[str] = None

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from ..database import get_db
from ..auth import get_current_user
from ..db_models import User, ServiceAccount, ServiceLevelAgreement, Quotation, Invoice, WarrantyExtension, ServiceAppointment, SchedulingRequest, WorkOrder
from ..logger import log_action

router = APIRouter(prefix="/api/service", tags=["service"])

# Service Accounts
@router.get("/accounts")
async def list_service_accounts(
    skip: int = 0,
    limit: int = 25,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    accounts = db.query(ServiceAccount).offset(skip).limit(limit).all()
    total = db.query(ServiceAccount).count()
    return {"items": accounts, "total": total}

@router.post("/accounts")
async def create_service_account(
    data: ServiceAccountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service_account = ServiceAccount(
        account_id=data.account_id,
        warranty_status=data.warranty_status,
        service_level=data.service_level,
        owner_id=current_user.id,
        created_at=datetime.now()
    )
    db.add(service_account)
    db.commit()
    db.refresh(service_account)
    
    log_action(
        action_type="CREATE_SERVICE_ACCOUNT",
        user=current_user.username,
        details=f"Service account created for account {data.account_id}",
        status="success"
    )
    
    return service_account

@router.get("/accounts/{account_id}")
async def get_service_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    account = db.query(ServiceAccount).filter(ServiceAccount.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Service account not found")
    return account

@router.put("/accounts/{account_id}")
async def update_service_account(
    account_id: int,
    warranty_status: Optional[str] = None,
    service_level: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    account = db.query(ServiceAccount).filter(ServiceAccount.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Service account not found")
    
    if warranty_status:
        account.warranty_status = warranty_status
    if service_level:
        account.service_level = service_level
    
    db.commit()
    db.refresh(account)
    
    log_action(
        action_type="UPDATE_SERVICE_ACCOUNT",
        user=current_user.username,
        details=f"Service account {account_id} updated",
        status="success"
    )
    
    return account

# Quotations
@router.get("/quotations")
async def list_quotations(
    skip: int = 0,
    limit: int = 25,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    quotations = db.query(Quotation).offset(skip).limit(limit).all()
    total = db.query(Quotation).count()
    return {"items": quotations, "total": total}

@router.post("/quotations")
async def create_quotation(
    data: QuotationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        quotation = Quotation(
            quotation_number=f"QT-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            account_id=data.account_id,
            title=data.title,
            amount=data.amount,
            tax_amount=data.tax_amount,
            total_amount=data.amount + data.tax_amount,
            status="Draft",
            owner_id=current_user.id,
            created_at=datetime.now()
        )
        db.add(quotation)
        db.commit()
        db.refresh(quotation)
        
        log_action(
            action_type="CREATE_QUOTATION",
            user=current_user.username,
            details=f"Quotation {quotation.quotation_number} created for £{data.amount}",
            status="success"
        )
        
        return quotation
    except Exception as e:
        db.rollback()
        print(f"Error creating quotation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/quotations/{quotation_id}")
async def get_quotation(
    quotation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    quotation = db.query(Quotation).filter(Quotation.id == quotation_id).first()
    if not quotation:
        raise HTTPException(status_code=404, detail="Quotation not found")
    return quotation

@router.put("/quotations/{quotation_id}")
async def update_quotation(
    quotation_id: int,
    status: Optional[str] = None,
    amount: Optional[float] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    quotation = db.query(Quotation).filter(Quotation.id == quotation_id).first()
    if not quotation:
        raise HTTPException(status_code=404, detail="Quotation not found")
    
    if status:
        quotation.status = status
    if amount:
        quotation.amount = amount
        quotation.total_amount = amount + quotation.tax_amount
    
    db.commit()
    db.refresh(quotation)
    
    log_action(
        action_type="UPDATE_QUOTATION",
        user=current_user.username,
        details=f"Quotation {quotation.quotation_number} updated",
        status="success"
    )
    
    return quotation

# Invoices
@router.get("/invoices")
async def list_invoices(
    skip: int = 0,
    limit: int = 25,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    invoices = db.query(Invoice).offset(skip).limit(limit).all()
    total = db.query(Invoice).count()
    return {"items": invoices, "total": total}

@router.post("/invoices")
async def create_invoice(
    data: InvoiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        invoice = Invoice(
            invoice_number=f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            account_id=data.account_id,
            description=data.description,
            amount=data.amount,
            tax_amount=data.tax_amount,
            total_amount=data.amount + data.tax_amount,
            invoice_type=data.invoice_type,
            status="Draft",
            invoice_date=datetime.now(),
            owner_id=current_user.id,
            created_at=datetime.now()
        )
        db.add(invoice)
        db.commit()
        db.refresh(invoice)
        
        log_action(
            action_type="CREATE_INVOICE",
            user=current_user.username,
            details=f"Invoice {invoice.invoice_number} created ({data.invoice_type}) for £{data.amount}",
            status="success"
        )
        
        return invoice
    except Exception as e:
        db.rollback()
        print(f"Error creating invoice: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/invoices/{invoice_id}")
async def get_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice

@router.put("/invoices/{invoice_id}")
async def update_invoice(
    invoice_id: int,
    status: Optional[str] = None,
    amount: Optional[float] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    if status:
        invoice.status = status
        if status == "Paid":
            invoice.paid_date = datetime.now()
    if amount:
        invoice.amount = amount
        invoice.total_amount = amount + invoice.tax_amount
    
    db.commit()
    db.refresh(invoice)
    
    log_action(
        action_type="UPDATE_INVOICE",
        user=current_user.username,
        details=f"Invoice {invoice.invoice_number} updated to {status}",
        status="success"
    )
    
    return invoice

# Warranty Extensions
@router.get("/warranty-extensions")
async def list_warranty_extensions(
    skip: int = 0,
    limit: int = 25,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    extensions = db.query(WarrantyExtension).offset(skip).limit(limit).all()
    total = db.query(WarrantyExtension).count()
    return {"items": extensions, "total": total}

@router.post("/warranty-extensions")
async def create_warranty_extension(
    data: WarrantyExtensionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    extension = WarrantyExtension(
        service_account_id=data.service_account_id,
        extension_start_date=datetime.fromisoformat(data.extension_start_date),
        extension_end_date=datetime.fromisoformat(data.extension_end_date),
        extension_cost=data.extension_cost,
        status="Active",
        owner_id=current_user.id,
        created_at=datetime.now()
    )
    db.add(extension)
    db.commit()
    db.refresh(extension)
    
    log_action(
        action_type="CREATE_WARRANTY_EXTENSION",
        user=current_user.username,
        details=f"Warranty extension created for service account {data.service_account_id}",
        status="success"
    )
    
    return extension

@router.get("/slas")
async def list_slas(
    skip: int = 0,
    limit: int = 25,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        slas = db.query(ServiceLevelAgreement).offset(skip).limit(limit).all()
        total = db.query(ServiceLevelAgreement).count()
        return {"items": slas, "total": total}
    except Exception as e:
        print(f"Error listing SLAs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/slas")
async def create_sla(
    data: SLACreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    sla = ServiceLevelAgreement(
        service_account_id=data.service_account_id,
        name=data.name,
        response_time_hours=data.response_time_hours,
        resolution_time_hours=data.resolution_time_hours,
        uptime_percentage=data.uptime_percentage,
        support_hours=data.support_hours,
        created_at=datetime.now()
    )
    db.add(sla)
    db.commit()
    db.refresh(sla)
    
    log_action(
        action_type="CREATE_SLA",
        user=current_user.username,
        details=f"SLA '{data.name}' created for service account {data.service_account_id}",
        status="success"
    )

    return sla


# ============================================
# SCENARIO 2: Service Appointments & Scheduling
# ============================================

@router.get("/appointments")
async def list_service_appointments(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all service appointments"""
    appointments = db.query(ServiceAppointment).offset(skip).limit(limit).all()
    return appointments


@router.post("/appointments", status_code=status.HTTP_201_CREATED)
async def create_service_appointment(
    data: ServiceAppointmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new service appointment"""
    import uuid

    # Generate appointment number
    appointment_number = f"APT-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"

    # Create appointment
    appointment = ServiceAppointment(
        appointment_number=appointment_number,
        account_id=data.account_id,
        case_id=data.case_id,
        subject=data.subject,
        description=data.description,
        appointment_type=data.appointment_type,
        scheduled_start=datetime.fromisoformat(data.scheduled_start) if data.scheduled_start else None,
        scheduled_end=datetime.fromisoformat(data.scheduled_end) if data.scheduled_end else None,
        priority=data.priority,
        location=data.location,
        required_skills=data.required_skills,
        required_parts=data.required_parts,
        status="Scheduled",
        owner_id=current_user.id,
        created_at=datetime.now()
    )

    db.add(appointment)
    db.commit()
    db.refresh(appointment)

    # Create scheduling request for MuleSoft
    correlation_id = str(uuid.uuid4())
    scheduling_request = SchedulingRequest(
        appointment_id=appointment.id,
        appointment_number=appointment.appointment_number,
        request_type="SCHEDULE",
        status="PENDING",
        correlation_id=correlation_id,
        requested_by_id=current_user.id,
        created_at=datetime.now()
    )

    db.add(scheduling_request)
    db.commit()
    db.refresh(scheduling_request)

    log_action(
        action_type="CREATE_SERVICE_APPOINTMENT",
        user=current_user.username,
        details=f"Service appointment {appointment.appointment_number} created",
        status="success"
    )

    return {
        "appointment": appointment,
        "scheduling_request": scheduling_request,
        "message": "Service appointment created and sent to MuleSoft for scheduling"
    }


@router.get("/scheduling-requests")
async def list_scheduling_requests(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all scheduling requests (for Scenario 2 tab)"""
    query = db.query(SchedulingRequest)

    if status_filter:
        query = query.filter(SchedulingRequest.status == status_filter)

    requests = query.order_by(SchedulingRequest.created_at.desc()).offset(skip).limit(limit).all()
    return requests


@router.post("/scheduling-requests/{request_id}/approve")
async def approve_scheduling_request(
    request_id: int,
    technician_id: int = Query(...),
    technician_name: str = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Manually approve a scheduling request (simulates MuleSoft callback)"""

    scheduling_request = db.query(SchedulingRequest).filter(SchedulingRequest.id == request_id).first()
    if not scheduling_request:
        raise HTTPException(status_code=404, detail="Scheduling request not found")

    # Update scheduling request
    scheduling_request.status = "SUCCESS"
    scheduling_request.assigned_technician_id = technician_id
    scheduling_request.technician_name = technician_name
    scheduling_request.parts_available = True
    scheduling_request.mulesoft_transaction_id = f"MULE-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    scheduling_request.sap_hr_response = f"Technician {technician_name} assigned"
    scheduling_request.sap_inventory_response = "All parts available"
    scheduling_request.updated_at = datetime.now()

    # Update appointment with technician
    if scheduling_request.appointment_id:
        appointment = db.query(ServiceAppointment).filter(ServiceAppointment.id == scheduling_request.appointment_id).first()
        if appointment:
            appointment.assigned_technician_id = technician_id
            appointment.technician_name = technician_name
            appointment.status = "Assigned"
            appointment.updated_at = datetime.now()

    db.commit()
    db.refresh(scheduling_request)

    log_action(
        action_type="APPROVE_SCHEDULING",
        user=current_user.username,
        details=f"Scheduling request {request_id} approved, technician {technician_name} assigned",
        status="success"
    )

    return {
        "message": "Scheduling request approved successfully",
        "scheduling_request": scheduling_request
    }


# ============================================
# SCENARIO 3: Work Orders
# ============================================

@router.get("/workorders")
@router.get("/work-orders")  # Alias with hyphen for frontend
async def list_work_orders(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all work orders"""
    work_orders = db.query(WorkOrder).offset(skip).limit(limit).all()
    return work_orders


@router.post("/workorders", status_code=status.HTTP_201_CREATED)
@router.post("/work-orders", status_code=status.HTTP_201_CREATED)  # Alias with hyphen for frontend
async def create_work_order(
    data: WorkOrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new work order"""
    import uuid
    import random

    # Generate work order number
    work_order_number = f"WO-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
    correlation_id = str(uuid.uuid4())

    # Create work order with PENDING status (awaiting MuleSoft/SAP approval)
    work_order = WorkOrder(
        work_order_number=work_order_number,
        account_id=data.account_id,
        case_id=data.case_id,
        subject=data.subject,
        description=data.description,
        priority=data.priority,
        service_type=data.service_type,
        product=data.product,
        status="PENDING",  # Start as PENDING, will be updated by callback
        integration_status="SENT_TO_MULESOFT",
        entitlement_verified=False,  # Will be verified by MuleSoft/SAP
        mulesoft_transaction_id=f"MULE-WO-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        correlation_id=correlation_id,
        requested_by_id=current_user.id,
        owner_id=current_user.id,
        created_at=datetime.now()
    )

    db.add(work_order)
    db.commit()
    db.refresh(work_order)

    log_action(
        action_type="CREATE_WORK_ORDER",
        user=current_user.username,
        details=f"Work order {work_order.work_order_number} created and sent to MuleSoft for entitlement verification",
        status="success"
    )

    return {
        "work_order": work_order,
        "message": "Work order created and sent to MuleSoft for entitlement verification"
    }


@router.get("/workorder-requests")
async def list_work_order_requests(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all work order requests (for Scenario 3 tab)"""
    query = db.query(WorkOrder)

    if status_filter:
        query = query.filter(WorkOrder.status == status_filter)

    work_orders = query.order_by(WorkOrder.created_at.desc()).offset(skip).limit(limit).all()
    return work_orders


@router.post("/workorder-requests/{request_id}/approve")
@router.post("/work-order-requests/{request_id}/approve")  # Alias
async def approve_work_order_request(
    request_id: int,
    entitlement_verified: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Manually approve a work order request (simulates MuleSoft/SAP callback)"""
    import random

    work_order = db.query(WorkOrder).filter(WorkOrder.id == request_id).first()
    if not work_order:
        raise HTTPException(status_code=404, detail="Work order not found")

    # Update work order based on entitlement verification
    if entitlement_verified:
        work_order.status = "SUCCESS"
        work_order.entitlement_verified = True
        work_order.entitlement_type = work_order.service_type
        work_order.sap_order_id = f"SO-{datetime.now().strftime('%Y%m%d')}-{random.randint(10000, 99999)}"
        work_order.sap_notification_id = f"NOT-{datetime.now().strftime('%Y%m%d')}-{random.randint(10000, 99999)}"
        work_order.integration_status = "APPROVED"
        work_order.error_message = None
    else:
        work_order.status = "ENTITLEMENT_FAILED"
        work_order.entitlement_verified = False
        work_order.integration_status = "REJECTED"
        work_order.error_message = "Entitlement verification failed - service type not covered or expired"

    work_order.updated_at = datetime.now()

    db.commit()
    db.refresh(work_order)

    log_action(
        action_type="APPROVE_WORK_ORDER" if entitlement_verified else "REJECT_WORK_ORDER",
        user=current_user.username,
        details=f"Work order {work_order.work_order_number} {'approved' if entitlement_verified else 'rejected'} - Entitlement: {'Verified' if entitlement_verified else 'Failed'}",
        status="success" if entitlement_verified else "warning"
    )

    return {
        "message": f"Work order {'approved' if entitlement_verified else 'rejected'} successfully",
        "work_order": work_order
    }
