<!-- Modified for Rakko ORM: record upstream licensing, attribution and modification-notice handling. -->

# Distribution license review

Reviewed for Rakko ORM 1.0.0-alpha.3 (`1.0.0a3`), maintained by ropmyung.

Rakko is derived from Tortoise ORM and retains Apache-2.0. The review uses the
[Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0), especially
sections 4 and 6, and the
[upstream license](https://github.com/tortoise/tortoise-orm/blob/develop/LICENSE.txt).

| Requirement | Distribution treatment |
| --- | --- |
| Section 4(a): include the license | The original `LICENSE.txt` is included in source and wheel distributions. |
| Section 4(b): identify modifications in modified files | Modified upstream files carry concise Rakko change notices and summaries; full copyright and license information is maintained in the distribution notice files. |
| Section 4(c): preserve applicable upstream attribution | Original license copyright and existing notices are retained; `CONTRIBUTORS.rst` preserves upstream acknowledgements. |
| Section 4(d): retain applicable upstream NOTICE contents, if supplied | No original NOTICE is present in this checkout. The upstream `develop` root inspected during this review lists `LICENSE.txt` and no NOTICE. Rakko's `NOTICE.txt` is explicitly identified as a new project notice. |
| Section 6: trademark rights are not granted | Separate Rakko branding is used; README and NOTICE describe the fork without implying endorsement. |

Copyright and notice layout
---------------------------

`NOTICE.txt` records Rakko's copyright and upstream attribution. `LICENSE.txt`
retains the original license text, and `CONTRIBUTORS.rst` retains contributor
acknowledgements. Repeated Rakko copyright and SPDX comment blocks are not used
as source-file banners.

Modified upstream files instead carry short notices describing their Rakko
changes. Newly written files may carry a brief addition summary. Empty package
markers do not receive a banner solely because they belong to this project.
Existing upstream notices are preserved; this layout only replaces the repeated
Rakko banners added during release preparation. Section 4(b) does not prescribe
a particular template or require a detailed per-file changelog.

The original license SHA-256 before and after release preparation is:

```text
f79cadf1835446bf346fc990e2986a795f00a10e811b80a4d1a20e7c50844537
```

The checkout has no Git history identifying its exact upstream commit. Current
upstream inspection cannot establish the contents of that original snapshot;
if it is recovered and contains an applicable NOTICE or additional notices,
retain those as well. This report records the available evidence rather than
claiming a complete historical provenance audit.

Dependencies are declared separately and are not vendored into the wheel.
Their own licenses continue to apply when they are installed or redistributed;
Rakko's license does not replace them. New artwork provenance is in `ASSETS.md`.

The Apache warranty disclaimer and limitation of liability remain unchanged.
This is a record of the release's license handling, not a legal opinion or a
claim that upstream sponsors or certifies Rakko ORM.
