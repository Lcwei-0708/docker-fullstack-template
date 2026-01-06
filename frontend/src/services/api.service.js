import axios from 'axios';
import ENV from '@/config/env.config';
import { handleApiError, setErrorHandler } from './error.service';
import { toast } from 'sonner';

const getApiBaseUrl = () => {
  const protocol = ENV.SSL_ENABLED ? 'https' : 'http';
  return `${protocol}://${ENV.API_HOST}:${ENV.API_PORT}/api`;
};

const apiClient = axios.create({
  baseURL: getApiBaseUrl(),
  timeout: 15000,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

let getTokenFunction = null;
let logoutFunction = null;
let getTokenFunctionFromContext = null;
let isGettingToken = false;

export const setTokenGetter = (getToken, logout, getTokenFromContext = null) => {
  getTokenFunction = getToken;
  logoutFunction = logout;
  getTokenFunctionFromContext = getTokenFromContext;
};

export { setErrorHandler };

apiClient.interceptors.request.use(
  async (config) => {
    // Skip token if noToken is true
    if (config.noToken) {
      if (!config.headers || !config.headers.Authorization) {
        delete config.headers?.Authorization;
      }
      return config;
    }

    if (config.headers && config.headers.Authorization) {
      return config;
    }

    if (!getTokenFunction) {
      return config;
    }

    try {
      const latestToken = getTokenFunction();
      
      if (latestToken) {
        config.headers.Authorization = `Bearer ${latestToken}`;
      } else {
        delete config.headers.Authorization;
      }
    } catch (error) {
      delete config.headers.Authorization;
    }
    
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

apiClient.interceptors.response.use(
  (response) => {
    const config = response.config;
    const showSuccessToast = config?.showSuccessToast;
    const messageMap = config?.messageMap;
    const successMessage = config?.successMessage || (messageMap && messageMap.success);
    
    // 202 indicates password reset is required
    if (response.status === 202) {
      // Don't show success toast for 202, as it requires special handling
      if (response.data) {
        const responseData = response.data.data !== undefined ? response.data.data : response.data;
        return { ...responseData, _statusCode: 202 };
      }
      return { _statusCode: 202 };
    }
    
    if (successMessage && showSuccessToast === true) {
      toast.success(successMessage);
    }
    
    if (response.data && response.data.data !== undefined) {
      return response.data.data;
    }
    return response.data;
  },
  async (error) => {
    const originalRequest = error.config;
    const retryOn401 = originalRequest.retryOn401 !== false; // Default to true for backward compatibility

    if (error.response?.status === 401 && !originalRequest._retry && !originalRequest.noToken && !isGettingToken && retryOn401) {
      const errorMessage = error.response?.data?.message || '';
      const isPasswordError = errorMessage.includes('Current password is incorrect') || 
                             errorMessage.includes('password is incorrect') ||
                             errorMessage.toLowerCase().includes('incorrect password');
      
      if (isPasswordError) {
        // Password error: set custom status and skip token refresh
        error.customStatus = 'incorrect';
      } else {
        // Token expired: try to refresh
        originalRequest._retry = true;
        isGettingToken = true;

        try {
          if (getTokenFunctionFromContext) {
            const tokenResult = await getTokenFunctionFromContext(false, true);
            
            if (tokenResult?.success && tokenResult?.token) {
              originalRequest.headers.Authorization = `Bearer ${tokenResult.token}`;
              const result = await apiClient(originalRequest);
              isGettingToken = false;
              return result;
            }
          }
          
          if (logoutFunction) {
            // Clear local state only (skip API call to avoid loop)
            logoutFunction(true);
            error.config = error.config || {};
            error.config.showErrorToast = false;
          }
        } catch (tokenError) {
          if (logoutFunction) {
            logoutFunction(true);
            error.config = error.config || {};
            error.config.showErrorToast = false;
          }
        } finally {
          isGettingToken = false;
        }
      }
    }

    handleApiError(error, logoutFunction);
    return Promise.reject(error);
  }
);

/**
 * Wrap API call with status tracking
 * Returns a Promise that resolves with { data, status, error } or rejects with error
 */
const wrapApiCall = (apiCall) => {
  return apiCall
    .then(data => ({
      data,
      status: 'success',
      error: null,
    }))
    .catch(error => {
      return {
        data: null,
        status: 'error',
        error: {
          message: error.response?.data?.message || error.message || 'Request failed',
          status: error.response?.status,
          code: error.code,
        },
      };
    });
};

export const apiService = {
  /**
   * @param {string} url - API endpoint
   * @param {object} params - Query parameters
   * @param {object} config - Axios config
   * @param {boolean} config.noToken - Skip authentication token (default: false)
   * @param {boolean} config.retryOn401 - Retry request with new token on 401 error (default: true)
   * @param {boolean} config.showErrorToast - Show error toast (default: false)
   * @param {boolean} config.showSuccessToast - Show success toast (default: false)
   * @param {string} config.customMessage - Custom error message
   * @param {boolean} config.returnStatus - Return status object instead of just data (default: false)
   * @returns {Promise} - Returns data by default, or { data, status, error } if returnStatus is true
   */
  get: (url, params = {}, config = {}) => {
    const { returnStatus, ...restConfig } = config;
    const apiCall = apiClient.get(url, { params, ...restConfig });
    return returnStatus ? wrapApiCall(apiCall) : apiCall;
  },

  /**
   * @param {string} url - API endpoint
   * @param {object} data - Request body data
   * @param {object} config - Axios config
   * @param {boolean} config.noToken - Skip authentication token (default: false)
   * @param {boolean} config.retryOn401 - Retry request with new token on 401 error (default: true)
   * @param {boolean} config.showErrorToast - Show error toast (default: false)
   * @param {boolean} config.showSuccessToast - Show success toast (default: false)
   * @param {string} config.customMessage - Custom error message
   * @param {boolean} config.returnStatus - Return status object instead of just data (default: false)
   * @returns {Promise} - Returns data by default, or { data, status, error } if returnStatus is true
   */
  post: (url, data = {}, config = {}) => {
    const { returnStatus, ...restConfig } = config;
    const apiCall = apiClient.post(url, data, restConfig);
    return returnStatus ? wrapApiCall(apiCall) : apiCall;
  },

  /**
   * @param {string} url - API endpoint
   * @param {object} data - Request body data
   * @param {object} config - Axios config
   * @param {boolean} config.noToken - Skip authentication token (default: false)
   * @param {boolean} config.retryOn401 - Retry request with new token on 401 error (default: true)
   * @param {boolean} config.showErrorToast - Show error toast (default: false)
   * @param {boolean} config.showSuccessToast - Show success toast (default: false)
   * @param {string} config.customMessage - Custom error message
   * @param {boolean} config.returnStatus - Return status object instead of just data (default: false)
   * @returns {Promise} - Returns data by default, or { data, status, error } if returnStatus is true
   */
  put: (url, data = {}, config = {}) => {
    const { returnStatus, ...restConfig } = config;
    const apiCall = apiClient.put(url, data, restConfig);
    return returnStatus ? wrapApiCall(apiCall) : apiCall;
  },

  /**
   * @param {string} url - API endpoint
   * @param {object} config - Axios config
   * @param {boolean} config.noToken - Skip authentication token (default: false)
   * @param {boolean} config.retryOn401 - Retry request with new token on 401 error (default: true)
   * @param {boolean} config.showErrorToast - Show error toast (default: false)
   * @param {boolean} config.showSuccessToast - Show success toast (default: false)
   * @param {string} config.customMessage - Custom error message
   * @param {boolean} config.returnStatus - Return status object instead of just data (default: false)
   * @returns {Promise} - Returns data by default, or { data, status, error } if returnStatus is true
   */
  delete: (url, config = {}) => {
    const { returnStatus, ...restConfig } = config;
    const apiCall = apiClient.delete(url, restConfig);
    return returnStatus ? wrapApiCall(apiCall) : apiCall;
  },

  /**
   * @param {string} url - API endpoint
   * @param {FormData} formData - Form data to upload
   */
  upload: (url, formData) => {
    return apiClient.post(url, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },
};

export default apiService;