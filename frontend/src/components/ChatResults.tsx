import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { fetchPreviewPage, type PreviewProduct, type ProductPreview } from '../api'
import ProductCard from './ProductCard'

// Product Preview results from the chat. They slide down as a panel under the header on whatever page
// the shopper is on (no page change needed), 6 cards at a time, with "Show More" for the next 6.
export default function ChatResults({ preview, onClose, onMinimize }: {
  preview: ProductPreview
  onClose: () => void
  onMinimize: () => void
}) {
  const [items, setItems] = useState<PreviewProduct[]>(preview.products)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const panelRef = useRef<HTMLElement>(null)
  const firstNewRef = useRef<number | null>(null)

  // After "Show More", scroll the panel so the new row is in view.
  useEffect(() => {
    const i = firstNewRef.current
    if (i === null) return
    firstNewRef.current = null
    panelRef.current?.querySelectorAll('.chat-results-item')[i]?.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
  }, [items])

  async function showMore() {
    setLoading(true)
    setError(null)
    try {
      const page = await fetchPreviewPage(preview.query, items.length)
      firstNewRef.current = items.length
      setItems(current => [...current, ...page.products.filter(p => !current.some(c => c.product_id === p.product_id))])
    } catch {
      setError("Couldn't load more products. Please try again.")
    } finally {
      setLoading(false)
    }
  }

  const remaining = preview.total_matches - items.length
  return (
    <section ref={panelRef} className="chat-results" aria-label="Products from your chat" aria-live="polite">
      <div className="container">
        <div className="chat-results-head">
          <div>
            <p className="eyebrow">From your chat</p>
            <h2>
              {items.length < preview.total_matches ? `${items.length} of ${preview.total_matches}` : items.length}{' '}
              matches for &ldquo;{preview.query}&rdquo;
            </h2>
          </div>
          <div className="chat-results-actions">
            <Link to="/products" className="text-link" onClick={onMinimize}>Browse all products &rarr;</Link>
            <button className="chat-results-hide" onClick={onMinimize}>Hide</button>
            <button className="chat-results-close" onClick={onClose} aria-label="Clear chat results">&times;</button>
          </div>
        </div>
        {/* Keyed by query so a new search replays the card animation. */}
        <div className="product-grid chat-results-grid" key={preview.query}>
          {items.map((p, i) => (
            <div
              key={p.product_id}
              className="chat-results-item"
              style={{ animationDelay: `${(i % 6) * 70}ms` }}
              onClick={onMinimize} // opening a product tucks the panel away (it can be reopened)
            >
              <ProductCard product={p} />
            </div>
          ))}
        </div>
        {error && <p className="form-error chat-results-error" role="alert">{error}</p>}
        {remaining > 0 && (
          <div className="chat-results-more">
            <button className="btn btn-primary" onClick={showMore} disabled={loading}>
              {loading ? 'Loading...' : `Show More (${Math.min(remaining, 6)} of ${remaining} more)`}
            </button>
          </div>
        )}
      </div>
    </section>
  )
}

// A small tab to bring the results back after they were hidden.
export function ChatResultsTab({ preview, onOpen }: { preview: ProductPreview; onOpen: () => void }) {
  return (
    <button className="chat-results-tab" onClick={onOpen}>
      Chat results: &ldquo;{preview.query}&rdquo; ({preview.total_matches}) <span aria-hidden="true">▾</span>
    </button>
  )
}
