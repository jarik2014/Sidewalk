/**
 * Human-readable messages for the API's stable error codes (#1164).
 *
 * The API returns `{ code, message }`. `message` is a developer-facing English
 * string that may change or be localised server-side at any time, so the web
 * client maps `code` to its own copy and only falls back to `message` for codes
 * it does not know yet.
 */

export const ERROR_MESSAGES: Record<string, string> = {
  validation_error: 'Please check the highlighted fields and try again.',
  invalid_transition: 'This action is not allowed in the current state of the case.',
  unauthorized: 'Please sign in to continue.',
  invalid_credentials: 'That email and password combination is not correct.',
  account_inactive: 'This account has been deactivated.',
  token_invalid: 'Your session is no longer valid. Please sign in again.',
  token_expired: 'Your session has expired. Please sign in again.',
  forbidden: 'You do not have permission to do that.',
  not_found: 'We could not find what you were looking for.',
  user_not_found: 'We could not find that user.',
  conflict: 'That conflicts with something that already exists.',
  email_taken: 'An account with this email already exists.',
  rate_limited: 'Too many requests. Please wait a moment and try again.',
  internal_error: 'Something went wrong on our side. Please try again.',
  method_not_allowed: 'That request is not supported.',
  http_error: 'The request could not be completed.',
};

export interface ApiErrorPayload {
  code?: string;
  message?: string;
  field?: string;
  errors?: Array<{ field: string; message: string }>;
}

/** Best-effort message for an API error body, preferring the code mapping. */
export function messageForError(payload: ApiErrorPayload | undefined, fallback?: string): string {
  if (!payload) return fallback ?? ERROR_MESSAGES.http_error;
  const mapped = payload.code ? ERROR_MESSAGES[payload.code] : undefined;
  if (mapped) return mapped;
  if (payload.message) return payload.message;
  return fallback ?? ERROR_MESSAGES.http_error;
}
