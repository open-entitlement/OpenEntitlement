# Contracts and private PDF evidence

The Python service preview provides contracts in the Organization page for the selected Product. Workspace Owners and that Product’s Managers can read and manage these confidential contracts and evidence.

The API base is `/api/workspaces/{workspace_id}/products/{product_id}/organizations/{organization_id}/contracts`. List and create at the base; read or update metadata at `/{id}`. Upload a private PDF at `/{id}/documents`, download it at `/{id}/documents/{document_id}`, and link evidence at `/{id}/evidence`.

PDFs are limited to 10 MiB and checked for PDF header/end markers. Evidence must reference a document belonging to the same contract and uses positive safe page numbers; the service does not extract text or verify the document’s actual page count. Documents remain private and writes record the authenticated actor.

Contract status and dates are documentary. Evidence can refer to Organization terms or personal Grants in the same Product and Organization; it does not change evaluation, charge payments, or add PDF concepts to OEREP. External billing integration remains separate.
