---
title: Quickstart
description: Run the Python service, create a Product and evaluate it with the SDK.
---

You need Git, Node 24 and uv. The Python service hosts the React console.
This local demo uses ephemeral memory and a loopback development identity provider.

## Start from a fresh clone

```sh
git clone https://github.com/open-entitlement/OpenEntitlement.git
cd OpenEntitlement
npm ci --prefix sdk-js
npm ci --prefix console
uv sync --locked --project sdk-python
npm run build --prefix console
OE_APP_URL=http://localhost:18789 npm run dev:issuer --prefix console
```

Leave the issuer running. In another terminal, from the checkout:

```sh
OE_IN_MEMORY=true PORT=18789 OE_APP_URL=http://localhost:18789 \
 OE_OIDC_ISSUER=http://localhost:18790 OE_OIDC_LOCAL_HTTP=true \
 OE_PLATFORM_ADMIN_SUBJECT=local-admin uv run --project sdk-python --locked openentitlement-service
```

Open http://localhost:18789/app/ and sign in as `local-admin` with password `local`.
Create a Workspace named **Acme product**; its first Product has key `acme_product`.
Define an integer Privilege `seats` with default 5. Create a Tier named **Pro**,
set its seats to 25, and assign its standard variant to an Organization with ID `acme`.
In Settings → API keys, create a key and copy its secret once.

## Evaluate the Product

From `sdk-js/`, set `OE_API_KEY` in your local shell to the secret, then run:

```sh
node --conditions=source --input-type=module <<'JS'
import {Catalog, RemoteProvider, createClient} from '@openentitlement/core';
const catalog=Catalog.fromJSON({features:[{code:'limits',name:'Limits',privileges:[{key:'seats',valueType:'integer',default:0}]}]});
const client=createClient({catalog,provider:new RemoteProvider({baseUrl:'http://localhost:18789',product:'acme_product',token:process.env.OE_API_KEY})});
console.log(await client.getLimit('seats',{organizationId:'acme'}));
JS
```

```text title="Expected output"
25
```

Product keys are mandatory; a key cannot evaluate another
Product. The application still authorizes its callers and owns usage measurement.
The compatibility Feature wrapper above describes the SDK Catalog; the console
uses Privilege Catalog authoring.

Memory is lost at shutdown. For persistence and your own OIDC provider see
[self-hosting](../self-hosting/). Older images use different paths and credentials;
pin an older release if you need that interface.
