# G8 engineering-preview verification

`verify_preview.py` binds a mutable engineering-preview `.mcaddon` to an exact
source commit/tree and build manifest. It checks outer and nested ZIP integrity,
nested pack hashes, the manifest-declared shipped entrypoint, JSON parsing, and
PNG signatures/chunk CRCs.

Its PASS state is deliberately
`ENGINEERING_PREVIEW_EXACT_ARCHIVE_PASS_NOT_CANDIDATE_NOT_QUALIFIED`. It is not
an immutable freeze, Bedrock Dedicated Server or restart result, client test,
console test, Marketplace review, or release claim. Dormant and unratified
gameplay remains outside its proof scope.
