"""Private commercial evidence. Never part of evaluation or the SDK protocol."""
from __future__ import annotations

from datetime import datetime
from hashlib import sha256
from typing import Literal
from uuid import UUID, uuid4

from openentitlement.model import OpenEntitlementModel
from pydantic import Field, StrictInt, field_validator, model_validator

from . import audit
from .access import Permission
from .audit import AuditAction, AuditChange, TargetKind
from .problems import FieldError, NotFound, RevisionConflict, ValidationFailed
from .workspaces import OpenWorkspace

MAX_PDF = 10 * 1024 * 1024


def invalid(message: str) -> ValidationFailed:
    return ValidationFailed([FieldError("", message)])


class ExternalReference(OpenEntitlementModel):
    system: str = Field(min_length=1, max_length=80)
    reference: str = Field(min_length=1, max_length=500)


    @field_validator("system", "reference")
    @classmethod
    def nonblank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Reference must not be blank")
        return value.strip()


class ContractInput(OpenEntitlementModel):
    title: str = Field(min_length=1, max_length=500)
    reference: str = Field(default="", max_length=500)
    status: Literal["draft", "active", "expired", "terminated"] = "draft"
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    external_references: list[ExternalReference] = Field(default_factory=list, max_length=20)
    reason: str = Field(min_length=1, max_length=2000)

    @field_validator("title", "reference", "reason")
    @classmethod
    def trim(cls, value: str) -> str:
        return value.strip()

    @model_validator(mode="after")
    def valid(self) -> ContractInput:
        if not self.title.strip() or not self.reason.strip():
            raise ValueError("Title and reason must not be blank")
        for date in (self.starts_at, self.ends_at):
            if date is not None and date.tzinfo is None:
                raise ValueError("Dates need a timezone")
        if self.starts_at and self.ends_at and self.starts_at >= self.ends_at:
            raise ValueError("Contract end must follow its start")
        return self


class EvidenceInput(OpenEntitlementModel):
    kind: Literal["override", "grant"]
    entity_id: str
    document_id: UUID | None = None
    page: StrictInt | None = Field(default=None, ge=1, le=9007199254740991)
    note: str = Field(default="", max_length=2000)
    reason: str = Field(min_length=1, max_length=2000)


class ContractDocument(OpenEntitlementModel):
    id: UUID
    filename: str
    size: int
    sha256: str
    uploaded_at: datetime


class ContractHistory(OpenEntitlementModel):
    actor: str
    reason: str
    action: str
    at: datetime


class Contract(ContractInput):
    id: UUID
    workspace_id: UUID
    product_id: UUID
    organization_id: str
    version: int = 1
    documents: list[ContractDocument] = Field(default_factory=list)
    evidence: list[EvidenceInput] = Field(default_factory=list)
    history: list[ContractHistory] = Field(default_factory=list)


class ContractService:
    async def scope(self, ws: OpenWorkspace, product: UUID, organization: str) -> None:
        # Confidential commercial records use the same authority as Product administration.
        ws.actor.require(Permission.EDIT_PRODUCT, product)
        await ws.repos.catalog.lock(product)
        if await ws.repos.products.get(product) is None or await ws.repos.organizations.get(organization) is None:
            raise NotFound("Product or Organization does not exist.")

    async def list(self, ws: OpenWorkspace, product: UUID, organization: str) -> list[Contract]:
        await self.scope(ws, product, organization)
        return list(await ws.repos.contracts.list(product, organization))

    async def get(self, ws: OpenWorkspace, product: UUID, organization: str, id: UUID) -> Contract:
        await self.scope(ws, product, organization)
        found = await ws.repos.contracts.get(id)
        if found is None or found.product_id != product or found.organization_id != organization:
            raise NotFound("Contract does not exist.")
        return found

    async def _save(self, ws: OpenWorkspace, contract: Contract, action: str, reason: str, expected: int) -> Contract:
        if not reason.strip() or len(reason) > 2000:
            raise invalid("A reason of at most 2000 characters is required.")
        before = await ws.repos.contracts.get(contract.id)
        contract.history.append(ContractHistory(actor=ws.actor.account.email, reason=reason, action=action, at=ws.now))
        from .repositories import StaleVersion
        try:
            await ws.repos.contracts.save(contract, expected_version=expected)
        except StaleVersion as exc:
            raise RevisionConflict(kind="Contract", id=str(contract.id)) from exc
        await audit.record(ws, action=AuditAction.CREATED if expected == 0 else AuditAction.CHANGED,
                           target_kind=TargetKind.CONTRACT, target_id=str(contract.id), target_name=contract.title,
                           product_id=contract.product_id, reason=reason,
                           changes=audit.diff(before.model_dump(mode="json") if before else None,
                                              contract.model_dump(mode="json"), ignore={"history", "reason"})
                           or [AuditChange(field="operation", after=action)])
        return contract

    async def create(self, ws: OpenWorkspace, product: UUID, organization: str, body: ContractInput) -> Contract:
        await self.scope(ws, product, organization)
        contract = Contract(**body.model_dump(), id=uuid4(), workspace_id=ws.actor.workspace_id,
                            product_id=product, organization_id=organization)
        return await self._save(ws, contract, "create_contract", body.reason, 0)

    async def update(self, ws: OpenWorkspace, contract: Contract, body: ContractInput, version: int) -> Contract:
        contract = await self.get(ws, contract.product_id, contract.organization_id, contract.id)
        updated = Contract.model_validate({**contract.model_dump(), **body.model_dump(exclude={"version"}), "version": contract.version + 1})
        return await self._save(ws, updated, "update_contract", body.reason, version)

    async def upload(self, ws: OpenWorkspace, contract: Contract, content: bytes, filename: str, reason: str) -> Contract:
        contract = await self.get(ws, contract.product_id, contract.organization_id, contract.id)
        if len(content) > MAX_PDF:
            raise invalid("PDF exceeds 10 MiB")
        if not content.startswith(b"%PDF-") or b"%%EOF" not in content[-1024:]:
            raise invalid("Missing PDF header or end marker")
        if not filename.strip() or len(filename) > 160 or not filename.lower().endswith(".pdf"):
            raise invalid("Use a PDF filename of at most 160 characters")
        if len(contract.documents) >= 20:
            raise invalid("Maximum 20 PDFs per contract")
        filename = "".join("_" if ord(c) < 32 or ord(c) == 127 or c in "/\\" else c for c in filename)
        doc = ContractDocument(id=uuid4(), filename=filename, size=len(content), sha256=sha256(content).hexdigest(), uploaded_at=ws.now)
        expected = contract.version
        contract.documents.append(doc)
        contract = contract.model_copy(update={"version": contract.version + 1})
        await ws.repos.contracts.put_document(contract.id, doc.id, content)
        return await self._save(ws, contract, "attach_pdf", reason, expected)

    async def evidence(self, ws: OpenWorkspace, contract: Contract, body: EvidenceInput) -> Contract:
        contract = await self.get(ws, contract.product_id, contract.organization_id, contract.id)
        assignment = await ws.repos.organizations.assignment(contract.product_id, contract.organization_id)
        # Explicit service-value identities avoid inventing SDK override/grant IDs.
        sources = {"terms:" + key for key in assignment.terms} if assignment else set()
        grants = {"grant:" + user.subject_id + ":" + key
                  for user in await ws.repos.organizations.users(contract.product_id)
                  if user.organization_id == contract.organization_id for key in user.grants}
        if body.entity_id not in (sources if body.kind == "override" else grants):
            raise invalid("Entitlement source does not belong to this Product and Organization")
        if body.document_id and not any(d.id == body.document_id for d in contract.documents):
            raise invalid("PDF does not belong to this contract")
        if body.page is not None and body.document_id is None:
            raise invalid("A page must reference a PDF")
        expected = contract.version
        contract.evidence.append(body)
        contract = contract.model_copy(update={"version": contract.version + 1})
        return await self._save(ws, contract, "link_evidence", body.reason, expected)
