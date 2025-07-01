import i18n from 'i18next';
import en from './locales/en.json';
import zhTW from './locales/zh-TW.json';
import { initReactI18next, useTranslation } from 'react-i18next';

const resources = {
  "en": {
    translation: en
  },
  "zh-TW": {
    translation: zhTW
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