import { useEffect, useRef, useState, type ElementType, type ReactNode } from 'react'
import { useLocation } from 'react-router-dom'
import HandsomeDan, { type DanPose } from './HandsomeDan'

// eslint-disable-next-line react-refresh/only-export-components
export const prefersReducedMotion = () =>
  typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches

// Calls onEnter the first time the element scrolls into view.
// eslint-disable-next-line react-refresh/only-export-components
export function useInView<T extends Element>(threshold = 0.2): [React.RefObject<T | null>, boolean] {
  const ref = useRef<T>(null)
  const [seen, setSeen] = useState(false)
  useEffect(() => {
    const el = ref.current
    if (!el || seen) return
    // "In view" = that share of the element is visible, or it fills most of the screen
    // (sections taller than a phone screen can never be 55% visible at once).
    const io = new IntersectionObserver(
      entries => {
        const e = entries[0]
        if (e.isIntersecting && (e.intersectionRatio >= threshold || e.intersectionRect.height >= window.innerHeight * 0.6)) {
          setSeen(true)
          io.disconnect()
        }
      },
      { threshold: [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1] },
    )
    io.observe(el)
    return () => io.disconnect()
  }, [seen, threshold])
  return [ref, seen]
}

// Content that slides and fades in as it scrolls into view. Children with data-reveal-item stagger in.
export function Reveal({ as: Tag = 'div', className = '', children, ...rest }: {
  as?: ElementType
  className?: string
  children: ReactNode
  [key: string]: unknown
}) {
  const [ref, seen] = useInView<HTMLElement>(0.15)
  return (
    <Tag ref={ref} className={`reveal ${seen ? 'is-revealed' : ''} ${className}`} {...rest}>
      {children}
    </Tag>
  )
}

// --- Spirit cheers: a quick pop-up when you land on a homepage section ---

export type Cheer = { text: string; pose?: DanPose }

export function SectionCheer({ cheer, show }: { cheer: Cheer; show: boolean }) {
  const [visible, setVisible] = useState(false)
  useEffect(() => {
    if (!show || prefersReducedMotion()) return
    const start = window.setTimeout(() => setVisible(true), 250)
    const end = window.setTimeout(() => setVisible(false), 1650)
    return () => {
      window.clearTimeout(start)
      window.clearTimeout(end)
    }
  }, [show])
  if (!visible) return null
  return (
    <div className="section-cheer" aria-hidden="true">
      {cheer.pose && <HandsomeDan pose={cheer.pose} className="section-cheer-dan" />}
      <span className="section-cheer-text">{cheer.text}</span>
    </div>
  )
}

// --- Page transition: Handsome Dan overlays the screen briefly when a new page loads ---

const ANTICS: { pose: DanPose; caption: string }[] = [
  { pose: 'chomp', caption: 'Handsome Dan is chewing on a Harvard pennant…' },
  { pose: 'cap', caption: 'Handsome Dan is cramming for finals…' },
  { pose: 'cheer', caption: 'Bulldog! Bulldog! Bow, wow, wow!' },
  { pose: 'wag', caption: 'Fetching your page… good boy!' },
]
const TRANSITION_MS = 1100

export function PageTransition() {
  const { pathname } = useLocation()
  const [active, setActive] = useState<{ key: string; i: number } | null>(null)
  const first = useRef(true)

  useEffect(() => {
    const quick = prefersReducedMotion()
    const i = Math.floor(Math.random() * ANTICS.length)
    // A new screen every time the page (path) changes, including the first load.
    // eslint-disable-next-line react/set-state-in-effect
    setActive({ key: `${pathname}-${Date.now()}`, i })
    const t = window.setTimeout(() => setActive(null), quick ? 300 : first.current ? 1300 : TRANSITION_MS)
    first.current = false
    return () => window.clearTimeout(t)
  }, [pathname])

  if (!active) return null
  const antic = ANTICS[active.i]
  return (
    <div key={active.key} className="page-transition" role="status" aria-live="polite" onClick={() => setActive(null)}>
      <div className="page-transition-inner">
        <HandsomeDan pose={antic.pose} className="page-transition-dan" />
        <p className="page-transition-caption">{antic.caption}</p>
      </div>
    </div>
  )
}

// --- Add-to-cart cheer: Handsome Dan pops up with encouragement ---

const ENCOURAGEMENT = [
  'Great Choice!',
  'Looks Good!',
  "I'd Chew That!",
  'Boola Boola!',
  'Bulldog approved!',
  'Woof! Excellent pick!',
]
const CART_EVENT = 'cc:added-to-cart'

// eslint-disable-next-line react-refresh/only-export-components
export const celebrateAddToCart = () => window.dispatchEvent(new Event(CART_EVENT))

export function CartCheer() {
  const [message, setMessage] = useState<{ text: string; id: number } | null>(null)
  useEffect(() => {
    let timer = 0
    const onAdd = () => {
      window.clearTimeout(timer)
      setMessage({ text: ENCOURAGEMENT[Math.floor(Math.random() * ENCOURAGEMENT.length)], id: Date.now() })
      timer = window.setTimeout(() => setMessage(null), 2400)
    }
    window.addEventListener(CART_EVENT, onAdd)
    return () => {
      window.removeEventListener(CART_EVENT, onAdd)
      window.clearTimeout(timer)
    }
  }, [])
  if (!message) return null
  return (
    <div key={message.id} className="cart-cheer" role="status" aria-live="polite">
      <div className="cart-cheer-bubble">{message.text}</div>
      <HandsomeDan pose="wag" className="cart-cheer-dan" />
    </div>
  )
}
