// Centralized management of all environment variables for frontend (Vite/React only).
// Add new variables here.

// Vite
export const ENV = {
    DEBUG: process.env.NODE_ENV === 'development' || false,
    PROJECT_NAME: import.meta.env.VITE_PROJECT_NAME || 'Frontend APP',
    PROJECT_VERSION: import.meta.env.VITE_PROJECT_VERSION || '1.0.0',
    PROJECT_DESCRIPTION: import.meta.env.VITE_PROJECT_DESCRIPTION || 'Frontend APP',
};

export default ENV;