export const CSRF_COOKIE_NAME = 'csrf_token';

export function getCookie(name) {
  if (typeof document === 'undefined' || !document.cookie) {
    return null;
  }

  const escapedName = name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const match = document.cookie.match(new RegExp(`(?:^|;\\s*)${escapedName}=([^;]*)`));

  return match ? decodeURIComponent(match[1]) : null;
}

export function getCsrfTokenFromCookie() {
  return getCookie(CSRF_COOKIE_NAME);
}