# Service container releases

The root Dockerfile builds the Python service and React console. The publication
workflow tests startup, migrations, console delivery and the authentication boundary
before publishing. `edge` follows main; service-v tags publish versioned images.
Previously published images retain their original runtime and contract.

Use the [self-hosting guide](../../website/src/content/docs/docs/self-hosting.md)
and [service settings](../../sdk-python/packages/service/README.md). Releases need
all required checks and the conductor's whole-integration review; this document
does not authorize publication or deployment.
