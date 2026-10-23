import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from 'react'
import { fetchProducts, fetchSavedCart, saveCart, type SavedCart } from './api'
import { useAuth } from './auth'

// Shopper-side state kept in the browser (localStorage), so it survives page reloads:
// - the cart (Add to Cart / View Cart; there is deliberately no checkout).
//   Logged in: the cart is also saved to the shopper's account (cart_items table) and follows them across
//   devices and sessions. Guests: the cart stays in this browser, and is merged into the account at login.
// - "Your Recent Picks": the 5 most recently viewed product pages

export type CartItem = {
  product_id: string
  name: string
  size: string
  price: number
  image_url: string
  quantity: number
  max: number // units in stock for this size; the cart never holds more
}

export type RecentPick = { product_id: string; name: string; image_url: string; price: number }

const CART_KEY = 'cc_cart'
const CART_OWNER_KEY = 'cc_cart_owner' // user id whose account cart is cached here, or absent for a guest cart
const RECENT_KEY = 'cc_recent_picks'
const SAVE_DELAY_MS = 400 // wait for a burst of +/- clicks before saving to the account
export const RECENT_LIMIT = 5

function load<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(key)
    return raw ? (JSON.parse(raw) as T) : fallback
  } catch {
    return fallback
  }
}

const clamp = (n: number, max: number) => Math.max(0, Math.min(n, max))

type ShopState = {
  cart: CartItem[]
  cartCount: number
  addToCart: (item: Omit<CartItem, 'quantity'>, quantity?: number) => void
  setQuantity: (product_id: string, size: string, quantity: number) => void
  updateMax: (product_id: string, size: string, max: number) => void
  removeFromCart: (product_id: string, size: string) => void
  inCart: (product_id: string, size: string) => number
  recent: RecentPick[]
  addRecent: (pick: RecentPick) => void
}

const ShopContext = createContext<ShopState | null>(null)

const toLines = (items: CartItem[]) => items.map(({ product_id, size, quantity }) => ({ product_id, size, quantity }))

export function ShopProvider({ children }: { children: ReactNode }) {
  const { user, ready } = useAuth()
  const [cart, setCart] = useState<CartItem[]>(() => load(CART_KEY, []))
  const [recent, setRecent] = useState<RecentPick[]>(() => load(RECENT_KEY, []))
  // Which account the cart is synced with (null = guest). Changes made before syncing aren't saved.
  const [syncedUser, setSyncedUser] = useState<number | null>(null)
  const fromServer = useRef(false) // the latest cart change came from the server: don't save it back
  const pendingSave = useRef<number | null>(null)

  useEffect(() => localStorage.setItem(CART_KEY, JSON.stringify(cart)), [cart])
  useEffect(() => localStorage.setItem(RECENT_KEY, JSON.stringify(recent)), [recent])

  const applyServerCart = useCallback((saved: SavedCart) => {
    fromServer.current = true
    setCart(saved.items)
  }, [])

  // Log in (or reload while logged in): load the account cart. A guest cart in this browser is merged
  // into it; a cached copy of this account's cart is simply replaced by the saved one.
  // Log out: clear the cart from this browser (it stays saved in the account).
  useEffect(() => {
    if (!ready) return
    if (!user) {
      if (localStorage.getItem(CART_OWNER_KEY)) {
        localStorage.removeItem(CART_OWNER_KEY)
        fromServer.current = true
        // Reacting to logout (auth state lives outside this provider), so this has to happen in an effect.
        // eslint-disable-next-line react/set-state-in-effect
        setCart([])
      }
      setSyncedUser(null)
      return
    }
    if (syncedUser === user.id) return
    let cancelled = false
    const owner = localStorage.getItem(CART_OWNER_KEY)
    const guestLines = owner ? [] : toLines(load<CartItem[]>(CART_KEY, []))
    fetchSavedCart()
      .then(saved => (guestLines.length ? saveCart([...toLines(saved.items), ...guestLines]) : saved))
      .then(saved => {
        if (cancelled) return
        localStorage.setItem(CART_OWNER_KEY, String(user.id))
        applyServerCart(saved)
        setSyncedUser(user.id)
      })
      .catch(() => {}) // keep the local cart if the server can't be reached
    return () => {
      cancelled = true
    }
  }, [user, ready, syncedUser, applyServerCart])

  // Logged in: save every cart change to the account (debounced).
  useEffect(() => {
    if (fromServer.current) {
      fromServer.current = false
      return
    }
    if (!user || syncedUser !== user.id) return
    if (pendingSave.current) window.clearTimeout(pendingSave.current)
    pendingSave.current = window.setTimeout(() => {
      pendingSave.current = null
      saveCart(toLines(cart)).catch(() => {})
    }, SAVE_DELAY_MS)
  }, [cart, user, syncedUser])

  // Refresh product photos (and names/prices) saved in this browser, so Recent Picks and a guest cart
  // pick up re-processed images instead of old cached ones.
  useEffect(() => {
    fetchProducts()
      .then(products => {
        const byId = new Map(products.map(p => [p.product_id, p]))
        const fresh = <T extends { product_id: string; image_url: string }>(item: T): T => {
          const p = byId.get(item.product_id)
          return p && p.image_url !== item.image_url ? { ...item, image_url: p.image_url } : item
        }
        setRecent(r => (r.some(i => fresh(i) !== i) ? r.map(fresh) : r))
        setCart(c => (c.some(i => fresh(i) !== i) ? c.map(fresh) : c))
      })
      .catch(() => {})
  }, [])

  // Coming back to this tab (e.g. after editing the cart on another device): pick up the latest saved cart.
  useEffect(() => {
    if (!user || syncedUser !== user.id) return
    const refresh = () => {
      if (document.visibilityState !== 'visible' || pendingSave.current) return
      fetchSavedCart().then(applyServerCart).catch(() => {})
    }
    window.addEventListener('focus', refresh)
    document.addEventListener('visibilitychange', refresh)
    return () => {
      window.removeEventListener('focus', refresh)
      document.removeEventListener('visibilitychange', refresh)
    }
  }, [user, syncedUser, applyServerCart])

  const same = (i: CartItem, product_id: string, size: string) => i.product_id === product_id && i.size === size

  const addToCart = useCallback((item: Omit<CartItem, 'quantity'>, quantity = 1) => {
    setCart(c => {
      const existing = c.find(i => same(i, item.product_id, item.size))
      if (existing) {
        return c.map(i => (i === existing ? { ...i, max: item.max, quantity: clamp(i.quantity + quantity, item.max) } : i))
      }
      return [...c, { ...item, quantity: clamp(quantity, item.max) }].filter(i => i.quantity > 0)
    })
  }, [])

  const setQuantity = useCallback((product_id: string, size: string, quantity: number) => {
    setCart(c => c.map(i => (same(i, product_id, size) ? { ...i, quantity: clamp(quantity, i.max) } : i)).filter(i => i.quantity > 0))
  }, [])

  // Called when the cart page re-checks live stock: lower quantities that are now above what's in stock.
  const updateMax = useCallback((product_id: string, size: string, max: number) => {
    setCart(c => c.map(i => (same(i, product_id, size) ? { ...i, max, quantity: clamp(i.quantity, max) } : i)))
  }, [])

  const removeFromCart = useCallback((product_id: string, size: string) => {
    setCart(c => c.filter(i => !same(i, product_id, size)))
  }, [])

  const addRecent = useCallback((pick: RecentPick) => {
    setRecent(r => [pick, ...r.filter(p => p.product_id !== pick.product_id)].slice(0, RECENT_LIMIT))
  }, [])

  const value = useMemo<ShopState>(
    () => ({
      cart,
      cartCount: cart.reduce((n, i) => n + i.quantity, 0),
      addToCart,
      setQuantity,
      updateMax,
      removeFromCart,
      inCart: (product_id, size) => cart.find(i => same(i, product_id, size))?.quantity ?? 0,
      recent,
      addRecent,
    }),
    [cart, recent, addToCart, setQuantity, updateMax, removeFromCart, addRecent],
  )

  return <ShopContext.Provider value={value}>{children}</ShopContext.Provider>
}

// eslint-disable-next-line react-refresh/only-export-components
export function useShop(): ShopState {
  const ctx = useContext(ShopContext)
  if (!ctx) throw new Error('useShop must be used inside ShopProvider')
  return ctx
}
