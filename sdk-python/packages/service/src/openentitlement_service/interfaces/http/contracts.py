"""Session-authenticated private contract interface."""
from urllib.parse import quote, unquote
from uuid import UUID

from fastapi import APIRouter, Request, Response, HTTPException
from pydantic import Field

from ...services.contracts import Contract, ContractInput, ContractService, EvidenceInput, MAX_PDF
from ...services.problems import NotFound
from .dependencies import WorkspaceAccess

router = APIRouter(prefix="/api/workspaces/{workspace_id}/products/{product_id}/organizations/{organization_id}/contracts", tags=["contracts"])
service = ContractService()


class ContractUpdate(ContractInput):
    version: int = Field(ge=1, strict=True)


@router.get("")
async def list_contracts(product_id: UUID, organization_id: str, workspace: WorkspaceAccess) -> list[Contract]:
    return await service.list(workspace, product_id, organization_id)


@router.post("", status_code=201)
async def create(product_id: UUID, organization_id: str, body: ContractInput, workspace: WorkspaceAccess) -> Contract:
    return await service.create(workspace, product_id, organization_id, body)


@router.get("/{id}")
async def get(product_id: UUID, organization_id: str, id: UUID, workspace: WorkspaceAccess) -> Contract:
    return await service.get(workspace, product_id, organization_id, id)


@router.patch("/{id}")
async def update(product_id: UUID, organization_id: str, id: UUID, body: ContractUpdate, workspace: WorkspaceAccess) -> Contract:
    contract = await service.get(workspace, product_id, organization_id, id)
    return await service.update(workspace, contract, body, body.version)


@router.post("/{id}/evidence")
async def evidence(product_id: UUID, organization_id: str, id: UUID, body: EvidenceInput, workspace: WorkspaceAccess) -> Contract:
    contract = await service.get(workspace, product_id, organization_id, id)
    return await service.evidence(workspace, contract, body)


@router.post("/{id}/documents")
async def upload(request: Request, product_id: UUID, organization_id: str, id: UUID, workspace: WorkspaceAccess, filename: str) -> Contract:
    contract = await service.get(workspace, product_id, organization_id, id)
    if request.headers.get("content-type", "").split(";")[0] != "application/pdf":
        raise HTTPException(415, "Upload must be application/pdf")
    content = bytearray()
    async for chunk in request.stream():
        if len(content) + len(chunk) > MAX_PDF:
            raise HTTPException(413, "PDF exceeds 10 MiB")
        content.extend(chunk)
    return await service.upload(workspace, contract, bytes(content), filename, unquote(request.headers.get("x-oe-reason", "")))


@router.get("/{id}/documents/{document_id}")
async def download(product_id: UUID, organization_id: str, id: UUID, document_id: UUID, workspace: WorkspaceAccess) -> Response:
    contract = await service.get(workspace, product_id, organization_id, id)
    doc = next((d for d in contract.documents if d.id == document_id), None)
    content = await workspace.repos.contracts.document(id, document_id) if doc else None
    if doc is None or content is None:
        raise NotFound("PDF does not exist")
    return Response(content, media_type="application/pdf", headers={
        "Content-Disposition": "attachment; filename=contract.pdf; filename*=UTF-8''" + quote(doc.filename, safe=""),
        "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff",
        "Content-Security-Policy": "sandbox; default-src 'none'"})
