import { useEffect, useState } from 'react'
import { Link, Route, Routes, useLocation } from 'react-router-dom'
import NavBar from './components/NavBar'
import Footer from './components/Footer'
import ChatPanel from './components/ChatPanel'
import ChatResults, { ChatResultsTab } from './components/ChatResults'
import RecentPicks from './components/RecentPicks'
import { CartCheer, PageTransition } from './components/motion'
import type { ProductPreview } from './api'
import { useAuth } from './auth'
import Home from './pages/Home'
import Products from './pages/Products'
import ProductDetail from './pages/ProductDetail'
import About from './pages/About'
import Login from './pages/Login'
import Register from './pages/Register'
import Cart from './pages/Cart'
import { ForgotPassword, ResetPassword } from './pages/PasswordReset'

function ScrollToTop() {
  const { pathname } = useLocation()
  useEffect(() => {
    window.scrollTo(0, 0)
  }, [pathname])
  return null
}

export default function App() {
  const { user } = useAuth()
  const [preview, setPreview] = useState<ProductPreview | null>(null)
  const [previewOpen, setPreviewOpen] = useState(false)
  // New chat results open the panel right away, on whatever page the shopper is on.
  const showPreview = (p: ProductPreview | null) => {
    setPreview(p)
    setPreviewOpen(p !== null)
  }
  return (
    <>
      <ScrollToTop />
      <PageTransition />
      <CartCheer />
      <NavBar />
      {preview && previewOpen && (
        <ChatResults
          key={`${preview.query}-${preview.total_matches}`}
          preview={preview}
          onClose={() => showPreview(null)}
          onMinimize={() => setPreviewOpen(false)}
        />
      )}
      {preview && !previewOpen && <ChatResultsTab preview={preview} onOpen={() => setPreviewOpen(true)} />}
      <main>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/products" element={<Products />} />
          <Route path="/products/:productId" element={<ProductDetail />} />
          <Route path="/about" element={<About />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/cart" element={<Cart />} />
          <Route path="/forgot-password" element={<ForgotPassword />} />
          <Route path="/reset-password" element={<ResetPassword />} />
          <Route
            path="*"
            element={
              <section className="container page-message">
                <h1>Page not found</h1>
                <Link to="/" className="btn btn-primary">Back to home</Link>
              </section>
            }
          />
        </Routes>
      </main>
      <Footer />
      <RecentPicks />
      {/* Keyed by user so logging in or out starts a fresh conversation. */}
      <ChatPanel key={user?.id ?? 'guest'} onPreview={showPreview} />
    </>
  )
}
