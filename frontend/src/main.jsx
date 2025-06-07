import { StrictMode } from 'react'
import i18n from './i18n'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { I18nextProvider } from 'react-i18next'
import './index.css'
import AppRouter from './router/AppRouter'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <I18nextProvider i18n={i18n}>
      <BrowserRouter>
        <AppRouter />
      </BrowserRouter>
    </I18nextProvider>
  </StrictMode>,
)