import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import '@fontsource/cormorant-garamond/500.css'
import '@fontsource/cormorant-garamond/600.css'
import '@fontsource/cormorant-garamond/700.css'
import '@fontsource/cormorant-garamond/500-italic.css'
import '@fontsource/cinzel/600.css'
import '@fontsource/cinzel/700.css'
import '@fontsource-variable/libre-franklin'
import './index.css'
import './design.css'
import App from './App.tsx'
import { AuthProvider } from './auth.tsx'
import { PageProductProvider } from './pageContext.tsx'
import { ShopProvider } from './shop.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <PageProductProvider>
          <ShopProvider>
            <App />
          </ShopProvider>
        </PageProductProvider>
      </AuthProvider>
    </BrowserRouter>
  </StrictMode>,
)
