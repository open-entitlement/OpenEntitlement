"""Contract parity through HTTP; shared memory/Postgres transaction contract."""
import asyncio
from uuid import uuid4

import pytest
from test_http_tiers import _client
from test_http_organizations import _offer

pytestmark = pytest.mark.anyio
PDF = b"%PDF-1.7\nprivate contract\n%%EOF"


async def test_contract_http_storage_and_evidence(store):
    async with _client(store) as (client, product):
        await _offer(client, product)
        organizations = product.split('/products/')[0] + '/organizations'
        product_id = product.rsplit('/', 1)[1]
        created = await client.post(organizations, json={"id": "acme", "name": "Acme", "assignment": {
            "productId": product_id, "variantId": "pro_standard", "terms": {"seats": 80}}, "reason": "Agreement"})
        assert created.status_code == 201
        path = product + '/organizations/acme/contracts'
        body = {"title": "Agreement", "reason": "Signed"}
        response = await client.post(path, json=body, headers={"x-oe-actor": "forged"})
        assert response.status_code == 201, response.text
        contract = response.json()
        assert contract['history'][0]['actor'] != 'forged'
        detail = path + '/' + contract['id']
        assert (await client.get(path)).json()[0]['id'] == contract['id']
        # Another Workspace, Product and Organization cannot address this record.
        for foreign in (detail.replace(product_id, str(uuid4())), detail.replace('/acme/', '/foreign/'),
                        detail.replace(product.split('/')[3], str(uuid4()))):
            assert (await client.get(foreign)).status_code == 404
        assert (await client.post(detail + '/documents?filename=bad.pdf', content=b'not pdf', headers={
            'content-type': 'application/pdf', 'x-oe-reason': 'Evidence'})).status_code == 400
        assert (await client.post(detail + '/documents?filename=bad.pdf', content=PDF, headers={
            'content-type': 'text/plain'})).status_code == 415
        async def upload(n):
            return await client.post(detail + f'/documents?filename={n}.pdf', content=PDF, headers={
                'content-type': 'application/pdf', 'x-oe-reason': 'Evidence'})
        results = await asyncio.gather(upload(1), upload(2))
        assert [r.status_code for r in results] == [200, 200], [r.text for r in results]
        current = (await client.get(detail)).json()
        assert len(current['documents']) == 2 and len(current['history']) == 3
        assert 'private contract' not in str(current)
        doc = current['documents'][0]['id']
        downloaded = await client.get(detail + '/documents/' + doc)
        assert downloaded.content == PDF and downloaded.headers['cache-control'] == 'no-store'
        assert 'attachment' in downloaded.headers['content-disposition']
        evidence = {'kind': 'override', 'entityId': 'terms:seats', 'documentId': doc, 'page': 1, 'reason': 'Clause'}
        for bad in ({'page': 0}, {'page': True}, {'documentId': str(uuid4())}, {'entityId': 'terms:foreign'}):
            assert (await client.post(detail + '/evidence', json=evidence | bad)).status_code == 400
        assert (await client.post(detail + '/evidence', json=evidence)).status_code == 200
        stale = await client.patch(detail, json=body | {'version': 1})
        assert stale.status_code == 409
        now = (await client.get(detail)).json()
        changed = await client.patch(detail, json=body | {'title':'Renewed', 'status':'active',
            'version':now['version'], 'startsAt':'2026-01-01T00:00:00Z', 'endsAt':'2027-01-01T00:00:00Z',
            'externalReferences':[{'system':'CRM','reference':'deal-42'}]})
        assert changed.status_code == 200, changed.text
        assert changed.json()['title'] == 'Renewed'
        assert len(changed.json()['documents']) == 2
        # A failed write cannot leave a PDF or history behind.
        before = (await client.get(detail)).json()
        failed = await client.post(detail + '/documents?filename=lost.pdf', content=PDF, headers={
            'content-type': 'application/pdf', 'x-oe-reason': ' '})
        assert failed.status_code == 400
        assert (await client.get(detail)).json() == before
        oversized = await client.post(detail + '/documents?filename=large.pdf', content=b'X' * (10485760 + 1), headers={
            'content-type': 'application/pdf', 'x-oe-reason': 'Evidence'})
        assert oversized.status_code == 413
        client.cookies.clear()
        assert (await client.get(detail + '/documents/' + doc)).status_code == 401


async def test_contract_permissions_and_atomicity(store):
    from test_organization_service import Scene
    from openentitlement_service.services.contracts import ContractInput, ContractService
    from openentitlement_service.services.problems import NotFound, PermissionDenied
    scene = await Scene(store).setup()
    await scene.create()
    service = ContractService()
    async with scene.open('owner') as ws:
        contract = await service.create(ws, scene.analytics, 'acme', ContractInput(title='Private', reason='Signed'))
    for who, exception in [('user', PermissionDenied), ('storage_manager', NotFound), ('member', NotFound)]:
        with pytest.raises(exception):
            async with scene.open(who) as ws:
                await service.get(ws, scene.analytics, 'acme', contract.id)
    with pytest.raises(RuntimeError):
        async with scene.open('manager') as ws:
            current = await service.get(ws, scene.analytics, 'acme', contract.id)
            await service.upload(ws, current, PDF, 'rollback.pdf', 'Test transaction')
            raise RuntimeError('Rollback after successful storage and audit')
    async with scene.open('owner') as ws:
        current = await service.get(ws, scene.analytics, 'acme', contract.id)
        assert current.documents == [] and len(current.history) == 1
        entries = await ws.repos.audit.list(managed=None, limit=200)
        contract_entries = [e for _, e in entries if e.target_id == str(contract.id)]
        assert len(contract_entries) == 1
        assert contract_entries[0].actor_email == 'owner@acme.test'


async def test_document_limit_and_grant_ownership(store):
    from test_organization_service import Scene
    from openentitlement_service.services.contracts import ContractInput, ContractService, EvidenceInput
    from openentitlement_service.services.organizations import ApplicationUserInput
    from openentitlement_service.services.problems import ValidationFailed
    scene = await Scene(store).setup()
    await scene.create()
    service = ContractService()
    async with scene.open('owner') as ws:
        await scene.organizations.save_user(ws, 'acme', scene.analytics, 'idp|alice',
            ApplicationUserInput(name='Alice', grants={'seats': 5}), version=0, reason='Allowance')
        contract = await service.create(ws, scene.analytics, 'acme', ContractInput(title='Terms', reason='Signed'))
        for i in range(20):
            contract = await service.upload(ws, contract, PDF, f'{i}.pdf', 'Appendix')
        with pytest.raises(ValidationFailed):
            await service.upload(ws, contract, PDF, 'overflow.pdf', 'Appendix')
        contract = await service.evidence(ws, contract, EvidenceInput(kind='grant', entity_id='grant:idp|alice:seats', reason='Allowance'))
        with pytest.raises(ValidationFailed):
            await service.evidence(ws, contract, EvidenceInput(kind='grant', entity_id='grant:foreign:seats', reason='Foreign'))
        assert len(contract.documents) == 20
