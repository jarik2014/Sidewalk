/**
 * Human-readable messages for the API's stable error codes (#1164), mobile side.
 *
 * Kept in sync with `apps/web/src/lib/error-codes.ts`: the API's `code` is the
 * contract, its English `message` is only a fallback for unknown codes.
 */

export const ERROR_MESSAGES: Record<string, string> = {
  validation_error: 'Check the highlighted fields and try again.',
  invalid_transition: 'This action is not allowed right now.',
  unauthorized: 'Sign in to continue.',
  invalid_credentials: 'Email or password is incorrect.',
  account_inactive: 'This account is deactivated.',
  token_invalid: 'Session is no longer valid. Sign in again.',
  token_expired: 'Session expired. Sign in again.',
  forbidden: 'You do not have permission for this.',
  not_found: 'Not found.',
  user_not_found: 'User not found.',
  conflict: 'That already exists.',
  email_taken: 'This email is already registered.',
  rate_limited: 'Too many attempts. Try again shortly.',
  internal_error: 'Something went wrong. Please try again.',
  method_not_allowed: 'Unsupported request.',
  http_error: 'Request failed.',
};

export interface ApiErrorPayload {
  code?: string;
  message?: string;
  field?: string;
}

export function messageForError(payload: ApiErrorPayload | undefined, fallback?: string): string {
  if (!payload) return fallback ?? ERROR_MESSAGES.http_error;
  const mapped = payload.code ? ERROR_MESSAGES[payload.code] : undefined;
  if (mapped) return mapped;
  return payload.message ?? fallback ?? ERROR_MESSAGES.http_error;
}
