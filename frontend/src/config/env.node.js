// Centralized management of all environment variables for frontend (Vite/React only).
// Add new variables here.

// Node
export const ENV_NODE = {
  NODE_ENV: process.env.NODE_ENV || 'development', // Node environment (development/production/test)
  TIMEZONE: process.env.TIMEZONE || 'UTC', // Timezone setting (e.g. Asia/Taipei)
  SITE_URL: process.env.SITE_URL || 'http://localhost:3000', // Website base URL (e.g. http://localhost:3000)
};

export default ENV_NODE;