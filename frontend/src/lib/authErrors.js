export const CSRF_INVALID_MSG = "Invalid or expired CSRF token";
export const SESSION_INVALID_MSG = "Invalid or expired session";

export function getApiErrorMessage(error) {
  return error?.response?.data?.message ?? error?.message ?? "";
}

export function isCsrfInvalidError(error) {
  return getApiErrorMessage(error) === CSRF_INVALID_MSG;
}

export function isSessionInvalidError(error) {
  return getApiErrorMessage(error) === SESSION_INVALID_MSG;
}
