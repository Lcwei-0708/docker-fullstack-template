// Centralized management of all environment variables for frontend (Vite/React only).
// Add new variables here.

// Vite
export const ENV = {
  DEBUG: import.meta.env.DEV || false,
  PROJECT_NAME: import.meta.env.VITE_PROJECT_NAME || "Frontend APP",
  PROJECT_VERSION: import.meta.env.VITE_PROJECT_VERSION || "1.0.0",
  PROJECT_DESCRIPTION: import.meta.env.VITE_PROJECT_DESCRIPTION || "Frontend APP",
  SSL_ENABLED: import.meta.env.VITE_SSL_ENABLE === "true" || false,
  // API settings
  API_HOST: import.meta.env.VITE_API_HOST || "localhost",
  API_PORT: import.meta.env.VITE_API_PORT || 5000,
  // SMTP settings
  SMTP_ENABLE: import.meta.env.VITE_SMTP_ENABLE === "true" || false,
  // Registration settings
  REGISTRATION_ENABLE: import.meta.env.VITE_REGISTRATION_ENABLE === "true" || false,
};

export default ENV;
