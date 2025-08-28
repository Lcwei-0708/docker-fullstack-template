import ENV from './env.config';

// API configuration and URL builders
export const API_CONFIG = {
  // Base configuration
  HOST: ENV.API_HOST,
  PORT: ENV.API_PORT,
  SSL_ENABLED: ENV.SSL_ENABLED,
  // Protocol determined by SSL_ENABLE
  PROTOCOL: ENV.SSL_ENABLED ? 'https' : 'http',
};

// API URL builders
export class ApiUrlBuilder {
  constructor() {
    this.config = API_CONFIG;
  }

  // Get base API URL
  getBaseUrl() {
    return `${this.config.PROTOCOL}://${this.config.HOST}:${this.config.PORT}/api`;
  }

  // Build API endpoint URL
  buildEndpoint(endpoint = '') {
    const baseUrl = this.getBaseUrl();
    const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
    return `${baseUrl}${cleanEndpoint}`;
  }

  // Build full API URL with query parameters
  buildUrl(endpoint = '', queryParams = {}) {
    const url = this.buildEndpoint(endpoint);
    
    if (Object.keys(queryParams).length === 0) {
      return url;
    }
    
    const queryString = new URLSearchParams(queryParams).toString();
    return `${url}?${queryString}`;
  }
}

// Create default instance
export const apiUrl = new ApiUrlBuilder();

// Convenience functions
export const getApiUrl = (endpoint) => apiUrl.buildEndpoint(endpoint);
export const getApiUrlWithParams = (endpoint, params) => apiUrl.buildUrl(endpoint, params);

export default API_CONFIG; 