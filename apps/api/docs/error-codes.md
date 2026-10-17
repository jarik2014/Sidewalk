# Error codes

Every error response carries a stable `code`. Branch on it, never on `message`:
messages are for humans and may be reworded or localised at any time, codes are
part of the API contract.

```json
{ "code": "email_taken", "message": "A user with this email already exists", "field": "email" }
```

Validation failures additionally return `errors`, one entry per invalid field:

```json
{ "code": "validation_error", "message": "Validation error", "errors": [ { "field": "email", "message": "value is not a valid email address" } ] }
```

## Codes raised by `AppError` subclasses

| Code | Status | Raised when |
| --- | --- | --- |
| `validation_error` | 422 | request payload does not satisfy the schema |
| `invalid_transition` | 422 | a case status change is not allowed from the current state |
| `unauthorized` | 401 | authentication is missing or not acceptable |
| `invalid_credentials` | 401 | email/password pair is wrong |
| `account_inactive` | 401 | the account exists but is deactivated |
| `token_invalid` | 401 | access token is malformed or not signed by us |
| `token_expired` | 401 | access token is well formed but past its lifetime — refresh it |
| `forbidden` | 403 | authenticated, but not allowed to perform the action |
| `not_found` | 404 | the addressed resource does not exist |
| `user_not_found` | 404 | the addressed user does not exist |
| `conflict` | 409 | the request conflicts with current state |
| `email_taken` | 409 | registration with an email that already exists (`field: email`) |
| `rate_limited` | 429 | too many requests from this client |
| `internal_error` | 500 | unexpected failure; details are in server logs, never in the body |

Fallback codes for errors raised by Starlette/FastAPI itself: `unauthorized`,
`forbidden`, `not_found`, `method_not_allowed`, `rate_limited`, and
`http_error` for anything else.

## Adding a code

1. Give the `AppError` subclass a class-level `code`, or pass `code=` at the
   raise site when the same exception type means different things
   (`ConflictError(..., code="email_taken")`).
2. Add the code to the table above.
3. Add a mapping entry in the web and mobile clients (`error-codes.ts`) so the
   UI has a localised message for it.
