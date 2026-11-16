# Cloud prepaid billing research

Public primary-source review, 2026-11-16. This note supports [ADR-0012](../../ADR-0012.md); it is not an implementation specification or vendor selection. No private cost estimates or customer information are included.

| Primary source | Evidence and relevance |
|---|---|
| [Plan your billing architecture](https://docs.metronome.com/guides/implement-metronome/planning-your-billing-architecture) | Treats value units, event sources, commercial models, reporting and operational recovery as distinct decisions. Prepayment reduces exposure but still needs controls. |
| [Pay-as-you-go](https://docs.metronome.com/guides/pricing-packaging/billing-model-guides/pay-as-you-go) | Describes usage charged in arrears. OpenEntitlement uses PAYG to mean usage pricing, but explicitly selects prepaid funding instead of this guide's arrears model. |
| [Hybrid business models](https://docs.metronome.com/guides/pricing-packaging/billing-model-guides/hybrid-business-models) | Combines recurring charges with usage and credit policies. These are alternatives, not evidence that a subscription, expiring allowance or seat price is selected for Cloud. |
| [Prepaid credits](https://docs.metronome.com/guides/pricing-packaging/billing-model-guides/prepaid-credits) | Covers funding, payments and balance notifications. Useful adapter research; vendor notifications alone do not establish a strict concurrent spending bound. |
| [Enterprise commit](https://docs.metronome.com/guides/pricing-packaging/billing-model-guides/enterprise-commit) | Describes negotiated commitments, discounts and schedules. None is required by Cloud's prepaid PAYG choice or by an Organization's display-only Minimum commitment. |

The inference for OpenEntitlement is to keep Cloud request measurement and monetary accounting outside entitlement resolution, behind explicit adapters. A vendor's Products, contracts and credits need deliberate mappings; they do not replace the OpenEntitlement domain model. Integration feasibility and conformance have not been demonstrated by reading these guides.

Metering/billing costs belong in the sustainable price calculation alongside hosting and payment costs. No numeric vendor rate is assumed here: obtain current terms and measure billable event volume before quoting Cloud prices. Public vendor pricing can change and is not a customer price promise.
