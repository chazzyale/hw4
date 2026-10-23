import { useEffect, useRef, useState } from 'react'
import { Link, NavLink } from 'react-router-dom'
import { useAuth } from '../auth'
import { useShop } from '../shop'

const MAIN_LINKS = [
  { to: '/', label: 'Home', end: true },
  { to: '/products', label: 'Products', end: false },
  { to: '/about', label: 'About Us', end: false },
]

export default function NavBar() {
  const [open, setOpen] = useState(false)
  const { user, ready, logout } = useAuth()
  const { cartCount } = useShop()
  const close = () => setOpen(false)
  const headerRef = useRef<HTMLElement>(null)

  // Publish the header's real height so section-by-section scrolling lands exactly below it.
  useEffect(() => {
    const el = headerRef.current
    if (!el) return
    const publish = () => document.documentElement.style.setProperty('--header-h', `${el.offsetHeight}px`)
    const ro = new ResizeObserver(publish)
    ro.observe(el)
    publish()
    return () => ro.disconnect()
  }, [])

  return (
    <header className="site-header" ref={headerRef}>
      <div className="topbar">57 Broadway, New Haven, CT &middot; Serving Bulldogs since 1975</div>
      <nav className="navbar container" aria-label="Main">
        <Link to="/" className="brand" onClick={close}>
          <span className="brand-mark" aria-hidden="true">C</span>
          <span className="brand-text">
            Campus Customs
            <small>Yale Apparel &amp; Gifts</small>
          </span>
        </Link>

        <button
          className="nav-toggle"
          aria-expanded={open}
          aria-controls="nav-links"
          onClick={() => setOpen(o => !o)}
        >
          Menu
        </button>

        <div id="nav-links" className={`nav-links ${open ? 'open' : ''}`}>
          {MAIN_LINKS.map(l => (
            <NavLink key={l.to} to={l.to} end={l.end} onClick={close}>
              {l.label}
            </NavLink>
          ))}
          <span className="nav-divider" aria-hidden="true" />
          {!ready ? null : user ? (
            <>
              <span className="nav-greeting">Hi, {user.first_name}</span>
              <button
                className="nav-logout"
                onClick={() => {
                  logout()
                  close()
                }}
              >
                Log out
              </button>
            </>
          ) : (
            <>
              <NavLink to="/login" onClick={close}>Log in</NavLink>
              <NavLink to="/register" className="nav-cta" onClick={close}>Create account</NavLink>
            </>
          )}
        </div>

        {/* Cart icon: to the right of the Menu button (and of the links on wide screens). */}
        <NavLink
          to="/cart"
          className="nav-cart"
          onClick={close}
          aria-label={`View cart, ${cartCount} ${cartCount === 1 ? 'item' : 'items'}`}
        >
          <svg viewBox="0 0 24 24" width="24" height="24" aria-hidden="true">
            <path
              d="M3 4h2.2l2.1 10.4a1.5 1.5 0 0 0 1.5 1.2h8.4a1.5 1.5 0 0 0 1.5-1.1L20.5 8H6.1"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.8"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
            <circle cx="9.5" cy="19.5" r="1.4" fill="currentColor" />
            <circle cx="17" cy="19.5" r="1.4" fill="currentColor" />
          </svg>
          {cartCount > 0 && <span className="nav-cart-count">{cartCount > 99 ? '99+' : cartCount}</span>}
        </NavLink>
      </nav>
    </header>
  )
}
