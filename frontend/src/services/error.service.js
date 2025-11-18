import i18n from '@/i18n';
import { debugError, debugWarn } from '@/lib/utils';
import { toast } from 'sonner';

const getCurrentLanguage = () => {
  return i18n.language || i18n.resolvedLanguage || localStorage.getItem("app-language") || 'en';
};

const getErrorMessage = (key) => {
  const currentLanguage = getCurrentLanguage();
  const errorData = i18n.t(`errors.${key}`, { 
    returnObjects: true,
    lng: currentLanguage
  });
  
  if (typeof errorData === 'object' && errorData && errorData.message) {
    return errorData.message;
  }
  
  if (typeof errorData === 'string') {
    return errorData;
  }
  
  return i18n.t('errors.unknown.message', { 
    defaultValue: 'An error occurred',
    lng: currentLanguage
  });
};

const getErrorTitle = (key) => {
  const errorData = i18n.t(`errors.${key}`, { returnObjects: true });
  
  if (typeof errorData === 'object' && errorData.title) {
    return errorData.title;
  }
  
  return 'Error';
};

const getErrorData = (key) => {
  const errorData = i18n.t(`errors.${key}`, { returnObjects: true });
  
  if (typeof errorData === 'object' && errorData.title && errorData.message) {
    return errorData;
  }
  
  return {
    title: 'Error',
    message: typeof errorData === 'string' ? errorData : 'An error occurred'
  };
};

let showErrorFunction = null;

export const setErrorHandler = (showError) => {
  showErrorFunction = showError;
};

export const showError = (message) => {
  if (showErrorFunction) {
    showErrorFunction(message);
  } else {
    debugWarn('No error handler set. Error message:', message);
  }
};

export const handleApiError = (error, logoutFunction) => {
  // Determine status: custom status > HTTP status > unknown
  let status;
  if (error.customStatus) {
    status = error.customStatus;
  } else if (error.response) {
    status = error.response.status;
  } else {
    status = 'unknown';
  }
  
  const method = error.config?.method?.toUpperCase();
  const url = error.config?.url;
  const showErrorToast = error.config?.showErrorToast === true;
  
  const getCustomMessage = (defaultKey) => {
    const messageMap = error.config?.messageMap;
    if (messageMap && messageMap[status]) {
      return messageMap[status];
    }
    
    const errorMessage = error.config?.errorMessage;
    if (errorMessage) {
      if (typeof errorMessage === 'object' && errorMessage[status]) {
        return errorMessage[status];
      }
      if (typeof errorMessage === 'string') {
        return errorMessage;
      }
    }
    
    const customMessage = error.config?.customMessage;
    if (customMessage) return customMessage;
    
    const errorMessageMap = error.config?.errorMessageMap;
    if (errorMessageMap && errorMessageMap[status]) {
      return errorMessageMap[status];
    }
    
    const backendMessage = error.response?.data?.message;
    if (backendMessage) return backendMessage;
    
    return getErrorMessage(defaultKey);
  };
  
  const logError = (message) => {
    debugError(message);
  };
  
  const displayToast = (type, message) => {
    if (showErrorToast) {
      toast[type](message);
    }
  };
  
  // Handle specific status codes
  switch (status) {
    case 400:
      logError('400 - Bad Request');
      displayToast('error', getCustomMessage('400'));
      break;
      
    case 401:
      logError('401 - Unauthorized');
      displayToast('error', getCustomMessage('401'));
      break;
      
    case 403:
      logError('403 - Permission denied');
      displayToast('error', getCustomMessage('403'));
      break;
      
    case 404:
      logError('404 - Not Found');
      displayToast('error', getCustomMessage('404'));
      break;
      
    case 409:
      logError('409 - Conflict');
      displayToast('error', getCustomMessage('409'));
      break;
      
    case 422:
      logError('422 - Validation Error');
      displayToast('error', getCustomMessage('422'));
      break;
      
    case 429:
      debugWarn('429 - Too many requests');
      displayToast('warning', getCustomMessage('429'));
      break;
      
    case 500:
      logError('500 Internal Server Error');
      displayToast('error', getCustomMessage('500'));
      break;
    
    case 'incorrect':
      logError('Incorrect data error');
      displayToast('error', getCustomMessage('incorrect'));
      break;
    
    default:
      const errorMessage = error.message || '';
      if (errorMessage.includes('CORS') || errorMessage.includes('blocked by CORS')) {
        logError(`CORS Error: ${errorMessage}`);
      } else {
        logError(`Unknown error: ${status} - ${errorMessage || 'Unexpected error occurred'}`);
      }
      displayToast('error', getCustomMessage('unknown'));
  }
};

export { getErrorMessage, getErrorTitle, getErrorData };

export default {
  setErrorHandler,
  handleApiError,
  showError,
  getErrorMessage,
  getErrorTitle,
  getErrorData
};