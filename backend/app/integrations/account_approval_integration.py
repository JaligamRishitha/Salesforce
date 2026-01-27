"""
Account approval integration stubs.

These functions model the MuleSoft -> ServiceNow workflow without making
network calls (suitable for local/dev Docker usage).
"""
from __future__ import annotations

import os
import uuid
from typing import Optional

import httpx
from sqlalchemy.orm import Session

from .. import crud
from ..db_models import AccountCreationRequest, User

MULESOFT_BASE_URL = os.getenv("MULESOFT_BASE_URL", "http://149.102.158.71:4799")
MULESOFT_ACCOUNT_REQUEST_PATH = os.getenv("MULESOFT_ACCOUNT_REQUEST_PATH", "/")
MULESOFT_TIMEOUT_SECONDS = float(os.getenv("MULESOFT_TIMEOUT_SECONDS", "10"))


def _new_external_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


def _build_mulesoft_payload(request: AccountCreationRequest, requested_by: User) -> dict:
    client_data = dict(request.requested_payload or {})
    # Provide a few canonical keys expected by downstream systems.
    client_data.setdefault("name", request.name)
    client_data.setdefault("billingAddress", client_data.get("billing_address"))

    return {
        "sourceSystem": "Salesforce",
        "requestType": "NEW_CLIENT",
        "requestedBy": (requested_by.role or "user").upper(),
        "requestedById": str(requested_by.id),
        "correlationId": request.correlation_id,
        "clientData": client_data,
    }


def _mulesoft_url() -> str:
    base = (MULESOFT_BASE_URL or "").rstrip("/")
    path = MULESOFT_ACCOUNT_REQUEST_PATH or "/"
    if not path.startswith("/"):
        path = f"/{path}"
    return f"{base}{path}"


def _send_request_to_mulesoft(request: AccountCreationRequest, requested_by: User) -> tuple[bool, Optional[str], Optional[str]]:
    url = _mulesoft_url()
    payload = _build_mulesoft_payload(request, requested_by)

    try:
        with httpx.Client(timeout=MULESOFT_TIMEOUT_SECONDS) as client:
            response = client.post(url, json=payload)
        if response.is_success:
            data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
            tx_id = data.get("transactionId") or data.get("mulesoftTransactionId")
            return True, tx_id, None
        return False, None, f"MuleSoft error {response.status_code}"
    except Exception as exc:  # Network errors, timeouts, DNS, etc.
        return False, None, str(exc)


def record_manager_audit(
    db: Session,
    request: AccountCreationRequest,
) -> AccountCreationRequest:
    """
    Manager/admin flow:
    - account already created in Salesforce
    - create an audit ticket that is auto-closed
    """
    return crud.update_account_request_integration(
        db,
        request,
        servicenow_ticket_id=_new_external_id("SNOW"),
        servicenow_status="APPROVED_AUTO_CLOSED",
        mulesoft_transaction_id=_new_external_id("MULE"),
        integration_status="COMPLETED",
    )


def record_user_submission(
    db: Session,
    request: AccountCreationRequest,
    requested_by: User,
) -> AccountCreationRequest:
    """
    User flow:
    - Salesforce does not create the account yet
    - MuleSoft creates a ServiceNow ticket and starts approval
    """
    request = crud.update_account_request_integration(
        db,
        request,
        servicenow_ticket_id=_new_external_id("SNOW"),
        servicenow_status="REQUESTED",
        mulesoft_transaction_id=_new_external_id("MULE"),
        integration_status="PENDING_MULESOFT",
    )

    success, tx_id, error_message = _send_request_to_mulesoft(request, requested_by)
    if success:
        return crud.update_account_request_integration(
            db,
            request,
            mulesoft_transaction_id=tx_id or request.mulesoft_transaction_id,
            integration_status="REQUESTED",
        )

    return crud.update_account_request_integration(
        db,
        request,
        integration_status="FAILED",
        error_message=error_message or "Failed to reach MuleSoft",
    )


def record_approval_outcome(
    db: Session,
    request: AccountCreationRequest,
    *,
    approved: bool,
    error_message: Optional[str] = None,
) -> AccountCreationRequest:
    if approved:
        return crud.update_account_request_integration(
            db,
            request,
            servicenow_status="APPROVED",
            integration_status="APPROVED",
        )

    return crud.update_account_request_integration(
        db,
        request,
        servicenow_status="REJECTED",
        integration_status="REJECTED",
        error_message=error_message,
    )
