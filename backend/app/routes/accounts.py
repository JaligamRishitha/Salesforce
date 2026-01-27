from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from sqlalchemy.orm import Session
from typing import Optional
import math

from ..database import get_db
from ..auth import get_current_user
from .. import schemas, crud
from ..db_models import User, AccountRequestStatus
from ..logger import log_action
from ..integrations import account_approval_integration

router = APIRouter(prefix="/api/accounts", tags=["accounts"])


def account_to_response(account) -> schemas.AccountResponse:
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
        owner_alias=account.owner.alias if account.owner else None
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

    return schemas.PaginatedResponse(
        items=[account_to_response(a) for a in accounts],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total > 0 else 0
    )


@router.post("", response_model=schemas.AccountCreateResult, status_code=status.HTTP_201_CREATED)
async def create_account(
    account: schemas.AccountCreate,
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Set owner to current user if not specified
    if not account.owner_id:
        account.owner_id = current_user.id

    # Manager/admin flow: create immediately + audit
    if is_manager(current_user):
        db_account = crud.create_account(db, account)

        audit_request = crud.create_account_request(
            db,
            account,
            requested_by=current_user,
            status=AccountRequestStatus.COMPLETED.value,
            auto_approved=True,
        )
        audit_request = crud.complete_account_request_with_account(db, audit_request, db_account, current_user)
        audit_request = account_approval_integration.record_manager_audit(db, audit_request)

        log_action(
            action_type="ACCOUNT_CREATED_MANAGER",
            user=current_user.username,
            details=f"Account '{db_account.name}' created and auto-audited",
            status="success",
        )

        return schemas.AccountCreateResult(
            flow="manager_auto_create",
            account=account_to_response(crud.get_account(db, db_account.id)),
            request=account_request_to_response(audit_request),
        )

    # User flow: create approval request only
    request = crud.create_account_request(db, account, requested_by=current_user)
    request = account_approval_integration.record_user_submission(db, request)

    log_action(
        action_type="ACCOUNT_CREATE_REQUESTED",
        user=current_user.username,
        details=f"Account request '{account.name}' submitted for approval",
        status="pending",
    )

    response.status_code = status.HTTP_202_ACCEPTED
    return schemas.AccountCreateResult(
        flow="user_pending_approval",
        request=account_request_to_response(request),
    )


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

    return account_to_response(account)


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
