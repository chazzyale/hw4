import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { fetchProduct, formatPrice } from '../api'
import { useShop } from '../shop'

export default function Cart() {
  const { cart, setQuantity, updateMax, removeFromCart } = useShop()
  const [adjusted, setAdjusted] = useState<string[]>([])

  // Re-check live stock when the cart opens, so quantities never exceed what's actually available.
  const ids = [...new Set(cart.map(i => i.product_id))].join(',')
  useEffect(() => {
    if (!ids) return
    let cancelled = false
    Promise.all(ids.split(',').map(id => fetchProduct(id).catch(() => null))).then(products => {
      if (cancelled) return
      const changed: string[] = []
      for (const p of products) {
        if (!p) continue
        for (const item of cart.filter(i => i.product_id === p.product_id)) {
          const stock = p.inventory.find(s => s.size === item.size)?.quantity ?? 0
          if (stock !== item.max) updateMax(item.product_id, item.size, stock)
          if (item.quantity > stock) changed.push(`${item.name} (${item.size})`)
        }
      }
      setAdjusted(changed)
    })
    return () => {
      cancelled = true
    }
    // Only when the set of products changes, not on every quantity click.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ids])

  const total = cart.reduce((sum, i) => sum + i.price * i.quantity, 0)
  const count = cart.reduce((n, i) => n + i.quantity, 0)

  return (
    <>
      <section className="page-header">
        <div className="container">
          <p className="eyebrow">Your cart</p>
          <h1>Cart</h1>
          <p>{count === 0 ? 'Your cart is empty.' : `${count} ${count === 1 ? 'item' : 'items'} saved for your visit.`}</p>
        </div>
      </section>

      <section className="container cart-page">
        {adjusted.length > 0 && (
          <p className="form-notice" role="status">
            Stock changed, so we updated: {adjusted.join(', ')}.
          </p>
        )}

        {cart.length === 0 ? (
          <div className="empty-card">
            <p>Nothing here yet. Find something to rep your Bulldog pride!</p>
            <Link to="/products" className="btn btn-primary">Shop products</Link>
          </div>
        ) : (
          <div className="cart-layout">
            <ul className="cart-list">
              {cart.map(item => (
                <li key={`${item.product_id}-${item.size}`} className={`cart-item ${item.max === 0 ? 'cart-item-out' : ''}`}>
                  <Link to={`/products/${item.product_id}`} className="cart-thumb">
                    <img src={item.image_url} alt={item.name} />
                  </Link>
                  <div className="cart-info">
                    <Link to={`/products/${item.product_id}`} className="cart-name">{item.name}</Link>
                    <p className="cart-meta">Size {item.size} &middot; {formatPrice(item.price)} each</p>
                    <p className="cart-meta">
                      {item.max === 0 ? 'Now sold out in this size' : `${item.max} available in ${item.size}`}
                    </p>
                  </div>
                  <div className="cart-qty" role="group" aria-label={`Quantity of ${item.name}, size ${item.size}`}>
                    <button
                      aria-label="Decrease quantity"
                      onClick={() => setQuantity(item.product_id, item.size, item.quantity - 1)}
                      disabled={item.quantity <= 1}
                    >
                      &minus;
                    </button>
                    <span aria-live="polite">{item.quantity}</span>
                    <button
                      aria-label="Increase quantity"
                      onClick={() => setQuantity(item.product_id, item.size, item.quantity + 1)}
                      disabled={item.quantity >= item.max}
                      title={item.quantity >= item.max ? 'No more in stock' : undefined}
                    >
                      +
                    </button>
                  </div>
                  <p className="cart-line-total">{formatPrice(item.price * item.quantity)}</p>
                  <button className="cart-remove" onClick={() => removeFromCart(item.product_id, item.size)}>
                    Remove
                  </button>
                </li>
              ))}
            </ul>

            <aside className="cart-summary" aria-label="Cart summary">
              <h2>Summary</h2>
              <p className="cart-summary-row">
                <span>Items</span>
                <span>{count}</span>
              </p>
              <p className="cart-summary-row cart-summary-total">
                <span>Total</span>
                <span>{formatPrice(total)}</span>
              </p>
              <p className="cart-summary-note">
                Online checkout isn&rsquo;t available yet. Bring your list to Campus Customs at 57 Broadway, New
                Haven, and we&rsquo;ll get you sorted.
              </p>
              <Link to="/products" className="btn btn-primary btn-block">Keep shopping</Link>
            </aside>
          </div>
        )}
      </section>
    </>
  )
}
