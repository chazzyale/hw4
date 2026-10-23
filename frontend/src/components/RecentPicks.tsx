import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { formatPrice } from '../api'
import { useShop } from '../shop'

// "Your Recent Picks": the 5 most recently viewed product pages, in a small row stuck to the bottom of the screen.
export default function RecentPicks() {
  const { recent } = useShop()
  const [collapsed, setCollapsed] = useState(false)
  const visible = recent.length > 0

  // Leave room at the bottom of the page (and lift the chat button) while the row is showing.
  useEffect(() => {
    document.body.classList.toggle('has-recent', visible && !collapsed)
    document.body.classList.toggle('has-recent-collapsed', visible && collapsed)
    return () => document.body.classList.remove('has-recent', 'has-recent-collapsed')
  }, [visible, collapsed])

  if (!visible) return null

  return (
    <aside className={`recent-picks ${collapsed ? 'collapsed' : ''}`} aria-label="Your Recent Picks">
      <div className="container recent-inner">
        <button className="recent-title" onClick={() => setCollapsed(c => !c)} aria-expanded={!collapsed}>
          Your Recent Picks <span aria-hidden="true">{collapsed ? '▴' : '▾'}</span>
        </button>
        {!collapsed && (
          <ol className="recent-list">
            {recent.map(p => (
              <li key={p.product_id}>
                <Link to={`/products/${p.product_id}`} className="recent-item" title={p.name}>
                  <img src={p.image_url} alt="" />
                  <span className="recent-text">
                    <span className="recent-name">{p.name}</span>
                    <span className="recent-price">{formatPrice(p.price)}</span>
                  </span>
                </Link>
              </li>
            ))}
          </ol>
        )}
      </div>
    </aside>
  )
}
