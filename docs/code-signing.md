# Code signing policy

## Current status

SignPath Foundation application preparation is in progress. The project has not been accepted by SignPath Foundation, and current Windows releases are not signed by SignPath. No signed release or approval is claimed here.

We intend to request free code signing provided by [SignPath.io](https://signpath.io), with a certificate from [SignPath Foundation](https://signpath.org). These credits will be updated to confirmed status only after acceptance and verification of an actual signed release.

## Responsibilities

Repository owner and maintainer: [Datastore24Kirill](https://github.com/Datastore24Kirill).
The owner reviews changes and approves releases. SignPath approver and reviewer roles must be configured and verified before signing is enabled. Required multi-factor authentication must be verified by the owner; its status has not been independently audited.

## Release checks

Only this project's executable and installer built from an identified source commit in GitHub Actions are candidates for signing. Upstream DLLs retain their own signatures/licenses and are not presented as this project's code. Tests and installer checks must pass before an authorized human approves a signing request. Signing must complete before publishing the release; the final downloadable artifacts must have verified signatures and checksums.

The signing service's credential must be kept in protected CI secrets, never in source control. An unsigned fallback must not be labelled signed.

See the [privacy policy](privacy.md) and [dependency notices](../desktop/THIRD_PARTY.md). Eligibility, artifact layout and roles remain subject to SignPath's review.
