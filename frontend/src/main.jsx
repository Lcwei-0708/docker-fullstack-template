import './index.css'
import i18n from './i18n'
import { StrictMode } from 'react'
import AppRouter from './router/AppRouter'
import { createRoot } from 'react-dom/client'
import { I18nextProvider } from 'react-i18next'
import { BrowserRouter } from 'react-router-dom'
import { ThemeProvider } from './contexts/themeContext'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <ThemeProvider>
        <I18nextProvider i18n={i18n}>
          <BrowserRouter>
            <AppRouter />
          </BrowserRouter>
        </I18nextProvider>
    </ThemeProvider>
  </StrictMode>
)