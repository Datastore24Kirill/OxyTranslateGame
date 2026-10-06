# Code signing policy

## Current status

The SignPath Foundation application was submitted on 2026-10-05. On 2026-10-06, the maintainer received a rejection: the project does not yet have sufficient public adoption, independent references and sustained community engagement for the Foundation program. Current Windows releases remain unsigned. No certificate, approval or partnership is claimed.

The Foundation invited a future application after broader recognition. We will continue public development, documentation, downloadable releases and support for genuine users. A paid subscription has not been purchased or configured. Signing credits will be added only after acceptance and verification of an actual signed release.

## Responsibilities

Repository owner and maintainer: [Datastore24Kirill](https://github.com/Datastore24Kirill).
The owner reviews changes and approves releases. SignPath approver and reviewer roles must be configured and verified before signing is enabled. The owner confirmed GitHub two-factor authentication on 2026-10-05; its status has not been independently audited.

## Release checks

Only this project's executable and installer built from an identified source commit in GitHub Actions are candidates for signing. Upstream DLLs retain their own signatures/licenses and are not presented as this project's code. Tests and installer checks must pass before an authorized human approves a signing request. Signing must complete before publishing the release; the final downloadable artifacts must have verified signatures and checksums.

The signing service's credential must be kept in protected CI secrets, never in source control. An unsigned fallback must not be labelled signed.

See the [privacy policy](privacy.md) and [dependency notices](../desktop/THIRD_PARTY.md). Any future application requires a new review; no acceptance timeline is promised.
