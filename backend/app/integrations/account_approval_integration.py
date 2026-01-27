"""
Account approval integration stubs.

These functions model the MuleSoft -> ServiceNow workflow without making
network calls (suitable for local/dev Docker usage).
"""
from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy.orm import Session

from .. import crud
from ..db_models import AccountCreationRequest


def _new_external_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


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
) -> AccountCreationRequest:
    """
    User flow:
    - Salesforce does not create the account yet
    - MuleSoft creates a ServiceNow ticket and starts approval
    """
    return crud.update_account_request_integration(
        db,
        request,
        servicenow_ticket_id=_new_external_id("SNOW"),
        servicenow_status="PENDING_APPROVAL",
        mulesoft_transaction_id=_new_external_id("MULE"),
        integration_status="AWAITING_APPROVAL",
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

