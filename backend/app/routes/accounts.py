from fastapi import APIRouter, Depends, HTTPException, status, Query, Response, Header
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
from datetime import datetime
import math
import os

from ..database import get_db
from ..auth import get_current_user
from .. import schemas, crud
from ..db_models import User, AccountRequestStatus, AccountCreationRequest, MulesoftRequest
from ..logger import log_action
from ..integrations import account_approval_integration

router = APIRouter(prefix="/api/accounts", tags=["accounts"])


def account_to_response(account, request: Optional[AccountCreationRequest] = None) -> schemas.AccountResponse:
    return schemas.AccountResponse(
        id=account.id,
        name=account.name,
        phone=account.phone,
        website=account.website,
        industry=account.industry,
        description=account.description,
        billing_address=account.billing_address,
        owner_id=account.owner_id,
        created_at=account.created_at,
        updated_at=account.updated_at,
        owner_alias=account.owner.alias if account.owner else None,
        request_id=request.id if request else None,
        request_status=request.status if request else None,
        servicenow_ticket_id=request.servicenow_ticket_id if request else None,
        integration_status=request.integration_status if request else None,
        correlation_id=request.correlation_id if request else None,
    )


def account_request_to_response(request) -> schemas.AccountRequestResponse:
    return schemas.AccountRequestResponse(
        id=request.id,
        name=request.name,
        status=request.status,
        auto_approved=request.auto_approved,
        correlation_id=request.correlation_id,
        requested_by_id=request.requested_by_id,
        approved_by_id=request.approved_by_id,
        servicenow_ticket_id=request.servicenow_ticket_id,
        servicenow_status=request.servicenow_status,
        mulesoft_transaction_id=request.mulesoft_transaction_id,
        integration_status=request.integration_status,
        error_message=request.error_message,
        created_account_id=request.created_account_id,
        created_at=request.created_at,
        updated_at=request.updated_at,
    )


def is_manager(user: User) -> bool:
    return user.role in {"admin", "manager"}


def verify_mulesoft_secret(secret: Optional[str]) -> None:
    expected = os.getenv("MULESOFT_SHARED_SECRET", "mulesoft-salesforce-shared-secret-2024")
    if secret != expected:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid MuleSoft secret")


def latest_requests_by_account_id(
    db: Session,
    account_ids: list[int],
) -> dict[int, AccountCreationRequest]:
    if not account_ids:
        return {}
    requests = (
        db.query(AccountCreationRequest)
        .filter(AccountCreationRequest.created_account_id.in_(account_ids))
        .order_by(AccountCreationRequest.created_at.desc())
        .all()
    )
    latest: dict[int, AccountCreationRequest] = {}
    for req in requests:
        acct_id = req.created_account_id
        if acct_id and acct_id not in latest:
            latest[acct_id] = req
    return latest


@router.get("", response_model=schemas.PaginatedResponse)
async def list_accounts(
    q: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    owner_id: Optional[int] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    skip = (page - 1) * page_size
    accounts, total = crud.get_accounts(
        db,
        skip=skip,
        limit=page_size,
        search=q,
        owner_id=owner_id,
        sort_by=sort_by,
        sort_order=sort_order
    )

    request_map = latest_requests_by_account_id(db, [a.id for a in accounts])
    
    # Get pending account requests (not yet created in accounts table)
    pending_requests = db.query(AccountCreationRequest).filter(
        AccountCreationRequest.created_account_id.is_(None),
        AccountCreationRequest.status.in_([AccountRequestStatus.PENDING.value, "PENDING_MULESOFT"])
    ).order_by(AccountCreationRequest.created_at.desc()).all()
    
    # Convert pending requests to account-like responses
    pending_items = []
    for req in pending_requests:
        pending_items.append(schemas.AccountResponse(
            id=req.id,
            name=req.name,
            phone=None,
            website=None,
            industry=None,
            description=None,
            billing_address=None,
            owner_id=req.requested_by_id,
            created_at=req.created_at,
            updated_at=req.updated_at,
            owner_alias=req.requested_by.alias if req.requested_by else None,
            request_id=req.id,
            request_status=req.status,
            servicenow_ticket_id=req.servicenow_ticket_id,
            integration_status=req.integration_status,
            correlation_id=req.correlation_id,
        ))

    # Combine created accounts and pending requests
    all_items = [account_to_response(a, request_map.get(a.id)) for a in accounts] + pending_items
    
    # Sort by created_at
    all_items.sort(key=lambda x: x.created_at, reverse=(sort_order == "desc"))
    
    # Apply pagination
    paginated_items = all_items[skip:skip + page_size]

    return schemas.PaginatedResponse(
        items=paginated_items,
        total=len(all_items),
        page=page,
        page_size=page_size,
        pages=math.ceil(len(all_items) / page_size) if len(all_items) > 0 else 0
    )


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_account(
    account: schemas.AccountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not account.owner_id:
        account.owner_id = current_user.id

    # Create MuleSoft request
    mulesoft_req = MulesoftRequest(
        account_id=None,
        request_type="create",
        status="pending",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    db.add(mulesoft_req)
    db.commit()
    db.refresh(mulesoft_req)

    # Your MCP integration will handle sending to MuleSoft
    # and updating status to "approved" when done

    return {
        "mulesoft_request": {
            "id": mulesoft_req.id,
            "status": mulesoft_req.status,
            "created_at": mulesoft_req.created_at
        }
    }


@router.get("/requests", response_model=schemas.PaginatedResponse)
async def list_account_requests(
    status_filter: Optional[AccountRequestStatus] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    skip = (page - 1) * page_size
    requested_by_id = None if is_manager(current_user) else current_user.id
    items, total = crud.list_account_requests(
        db,
        status=status_filter.value if status_filter else None,
        requested_by_id=requested_by_id,
        skip=skip,
        limit=page_size,
    )

    return schemas.PaginatedResponse(
        items=[account_request_to_response(r) for r in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total > 0 else 0,
    )


@router.post("/requests/{request_id}/approve", response_model=schemas.AccountCreateResult)
async def approve_account_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not is_manager(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Manager approval required")

    request = crud.get_account_request(db, request_id)
    if not request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account request not found")
    if request.status != AccountRequestStatus.PENDING.value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Request is not pending")

    request = account_approval_integration.record_approval_outcome(db, request, approved=True)

    try:
        payload = request.requested_payload or {}
        account_data = schemas.AccountCreate(**payload)
        if not account_data.owner_id:
            account_data.owner_id = request.requested_by_id

        db_account = crud.create_account(db, account_data)
        request = crud.complete_account_request_with_account(db, request, db_account, current_user)
        request = crud.update_account_request_integration(
            db,
            request,
            servicenow_status="COMPLETED",
            integration_status="COMPLETED",
        )
    except Exception as exc:
        request = crud.fail_account_request(db, request, str(exc))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Account creation failed")

    log_action(
        action_type="ACCOUNT_REQUEST_APPROVED",
        user=current_user.username,
        details=f"Approved account request {request.id} -> account {request.created_account_id}",
        status="success",
    )

    return schemas.AccountCreateResult(
        flow="approved_and_created",
        account=account_to_response(crud.get_account(db, db_account.id)),
        request=account_request_to_response(request),
    )


@router.post("/requests/{request_id}/mulesoft-accept", response_model=schemas.AccountCreateResult)
async def mulesoft_accept_account_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Simulates MuleSoft accepting the request and calling back into Salesforce.
    In real integration, MuleSoft would invoke this after downstream approval.
    """
    if not is_manager(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Manager access required")

    request = crud.get_account_request(db, request_id)
    if not request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account request not found")
    if request.status != AccountRequestStatus.PENDING.value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Request is not pending")

    try:
        payload = request.requested_payload or {}
        account_data = schemas.AccountCreate(**payload)
        if not account_data.owner_id:
            account_data.owner_id = request.requested_by_id

        db_account = crud.create_account(db, account_data)
        request = crud.complete_account_request_with_account(db, request, db_account, current_user)
        request = crud.update_account_request_integration(
            db,
            request,
            servicenow_status="COMPLETED",
            integration_status="COMPLETED",
        )
    except Exception:
        request = crud.fail_account_request(db, request, "MuleSoft acceptance failed")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Account creation failed")

    log_action(
        action_type="ACCOUNT_REQUEST_ACCEPTED_BY_MULESOFT",
        user=current_user.username,
        details=f"MuleSoft accepted request {request.id} -> account {request.created_account_id}",
        status="success",
    )

    return schemas.AccountCreateResult(
        flow="mulesoft_accepted_and_created",
        account=account_to_response(crud.get_account(db, db_account.id)),
        request=account_request_to_response(request),
    )


@router.post("/requests/{request_id}/mulesoft-callback", response_model=schemas.AccountCreateResult)
async def mulesoft_callback_account_request(
    request_id: int,
    payload: schemas.MuleSoftAccountCallback,
    x_mulesoft_secret: Optional[str] = Header(None, alias="X-MuleSoft-Secret"),
    db: Session = Depends(get_db),
):
    """
    Endpoint intended for MuleSoft to call after orchestration/approval.
    Secured via shared secret header.
    """
    verify_mulesoft_secret(x_mulesoft_secret)

    request = crud.get_account_request(db, request_id)
    if not request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account request not found")
    if request.status != AccountRequestStatus.PENDING.value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Request is not pending")

    if not payload.accepted:
        request = crud.reject_account_request(db, request, request.requested_by, reason=payload.message or payload.status)
        request = crud.update_account_request_integration(
            db,
            request,
            integration_status="REJECTED_BY_MULESOFT",
            servicenow_status=payload.status or "REJECTED",
            error_message=payload.message,
        )
        log_action(
            action_type="ACCOUNT_REQUEST_REJECTED_BY_MULESOFT",
            user="mulesoft",
            details=f"Request {request.id} rejected by MuleSoft",
            status="error",
        )
        return schemas.AccountCreateResult(flow="mulesoft_rejected", request=account_request_to_response(request))

    try:
        payload_data = request.requested_payload or {}
        account_data = schemas.AccountCreate(**payload_data)
        if not account_data.owner_id:
            account_data.owner_id = request.requested_by_id

        db_account = crud.create_account(db, account_data)
        request = crud.complete_account_request_with_account(db, request, db_account, request.requested_by)
        request = crud.update_account_request_integration(
            db,
            request,
            servicenow_status=payload.status or "COMPLETED",
            integration_status="COMPLETED",
            error_message=payload.message,
        )
    except Exception:
        request = crud.fail_account_request(db, request, "MuleSoft callback failed")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Account creation failed")

    log_action(
        action_type="ACCOUNT_REQUEST_ACCEPTED_BY_MULESOFT",
        user="mulesoft",
        details=f"MuleSoft callback accepted request {request.id} -> account {request.created_account_id}",
        status="success",
    )

    return schemas.AccountCreateResult(
        flow="mulesoft_callback_created",
        account=account_to_response(crud.get_account(db, db_account.id)),
        request=account_request_to_response(request),
    )


class MuleSoftStatusUpdate(BaseModel):
    integration_status: Optional[str] = None
    servicenow_status: Optional[str] = None
    servicenow_ticket_id: Optional[str] = None
    mulesoft_transaction_id: Optional[str] = None
    error_message: Optional[str] = None
    status: Optional[str] = None


@router.put("/requests/{request_id}", response_model=schemas.AccountRequestResponse)
async def update_account_request_status(
    request_id: int,
    payload: MuleSoftStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update account request integration status.
    Used by MuleSoft to update validation/approval status.
    """
    request = crud.get_account_request(db, request_id)
    if not request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account request not found")

    # Update integration fields
    request = crud.update_account_request_integration(
        db,
        request,
        integration_status=payload.integration_status,
        servicenow_status=payload.servicenow_status,
        servicenow_ticket_id=payload.servicenow_ticket_id,
        mulesoft_transaction_id=payload.mulesoft_transaction_id,
        error_message=payload.error_message,
    )

    # Update main status if provided
    if payload.status:
        request.status = payload.status
        db.commit()
        db.refresh(request)

    log_action(
        action_type="ACCOUNT_REQUEST_STATUS_UPDATED",
        user=current_user.username,
        details=f"Updated request {request_id} - integration_status: {payload.integration_status}",
        status="success",
    )

    return account_request_to_response(request)


@router.post("/requests/{request_id}/reject", response_model=schemas.AccountRequestResponse)
async def reject_account_request(
    request_id: int,
    reason: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not is_manager(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Manager approval required")

    request = crud.get_account_request(db, request_id)
    if not request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account request not found")
    if request.status != AccountRequestStatus.PENDING.value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Request is not pending")

    request = account_approval_integration.record_approval_outcome(db, request, approved=False, error_message=reason)
    request = crud.reject_account_request(db, request, current_user, reason=reason)

    log_action(
        action_type="ACCOUNT_REQUEST_REJECTED",
        user=current_user.username,
        details=f"Rejected account request {request.id}",
        status="error",
    )

    return account_request_to_response(request)


@router.get("/{account_id}", response_model=schemas.AccountResponse)
async def get_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    account = crud.get_account(db, account_id)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )

    # Track recent record
    crud.add_recent_record(db, current_user.id, "account", account.id, account.name)

    request_map = latest_requests_by_account_id(db, [account.id])
    return account_to_response(account, request_map.get(account.id))


@router.put("/{account_id}", response_model=schemas.AccountResponse)
async def update_account(
    account_id: int,
    account: schemas.AccountUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_account = crud.update_account(db, account_id, account)
    if not db_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    return account_to_response(crud.get_account(db, account_id))


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    success = crud.delete_account(db, account_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )


@router.put("/{account_id}/change-owner", response_model=schemas.AccountResponse)
async def change_account_owner(
    account_id: int,
    owner_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    account = crud.update_account(db, account_id, schemas.AccountUpdate(owner_id=owner_id))
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    return account_to_response(crud.get_account(db, account_id))
