import i18n from 'i18next';
import { initReactI18next, useTranslation } from 'react-i18next';
import en from './locales/en.json';

const resources = {
  "en": {
    translation: en
  }
};

i18n.use(initReactI18next).init({
  resources,
  lng: localStorage.getItem("app-language", "en"), // default language
  fallbackLng: "en", // fallback language if the selected language is not available
  interpolation: {
    escapeValue: false // do not escape values (React already does)
  }
});

export default i18n;