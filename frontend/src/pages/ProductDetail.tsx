import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { CATEGORY_LABELS, fetchProduct, formatPrice, type Product } from '../api'
import { usePageProduct } from '../pageContext'
import { useShop } from '../shop'
import { celebrateAddToCart } from '../components/motion'

const LOW_STOCK = 5

export default function ProductDetailRoute() {
  const { productId = '' } = useParams()
  // Keying by id gives each product a fresh page state when navigating between products.
  return <ProductDetail key={productId} productId={productId} />
}

function ProductDetail({ productId }: { productId: string }) {
  const [product, setProduct] = useState<Product | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [selected, setSelected] = useState<string | null>(null)

  const { setProduct: setPageProduct } = usePageProduct()
  const { addToCart, inCart, addRecent } = useShop()
  const [added, setAdded] = useState<string | null>(null)

  useEffect(() => {
    fetchProduct(productId).then(setProduct).catch(e => setError(e.message))
  }, [productId])

  // Tell the chat which product is on screen (its name and image_file_path), and clear it on leaving.
  useEffect(() => {
    if (!product) return
    setPageProduct({ name: product.name, image_file_path: product.image_url.replace(/\?.*$/, '').replace(/^\/media\//, '') })
    return () => setPageProduct(null)
  }, [product, setPageProduct])

  // "Your Recent Picks": remember this product page as the most recent view.
  useEffect(() => {
    if (product) {
      addRecent({ product_id: product.product_id, name: product.name, image_url: product.image_url, price: product.price })
    }
  }, [product, addRecent])

  if (error) {
    return (
      <section className="container page-message">
        <h1>{error === 'Not found' ? 'Product not found' : "Couldn't load this product"}</h1>
        <Link to="/products" className="btn btn-primary">Back to products</Link>
      </section>
    )
  }
  if (!product) return <p className="container page-message muted">Loading...</p>

  const selectedStock = product.inventory.find(s => s.size === selected)

  return (
    <section className="container product-detail">
      <nav className="breadcrumb" aria-label="Breadcrumb">
        <Link to="/products">Products</Link>
        <span aria-hidden="true">/</span>
        <Link to={`/products?category=${product.category}`}>{CATEGORY_LABELS[product.category]}</Link>
        <span aria-hidden="true">/</span>
        <span>{product.name}</span>
      </nav>

      <div className="detail-grid">
        <div className="detail-image">
          <img src={product.image_url} alt={product.name} />
        </div>

        <div className="detail-info">
          <p className="eyebrow">{product.garment_type}</p>
          <h1>{product.name}</h1>
          <p className="detail-price">{formatPrice(product.price)}</p>
          <p className="detail-desc">{product.description}</p>

          <dl className="detail-meta">
            <dt>Colors</dt>
            <dd>{product.colors.join(', ')}</dd>
          </dl>

          <h2 className="detail-subhead">Sizes &amp; availability</h2>
          <div className="size-grid">
            {product.inventory.map(s => {
              const out = s.quantity === 0
              return (
                <button
                  key={s.size}
                  className={`size-btn ${selected === s.size ? 'selected' : ''} ${out ? 'unavailable' : ''}`}
                  aria-pressed={selected === s.size}
                  title={out ? `${s.size} is sold out` : `${s.quantity} in stock`}
                  onClick={() => {
                    setSelected(s.size)
                    setAdded(null)
                  }}
                >
                  <span className="size-label">{s.size}</span>
                  <span className="size-stock">
                    {out ? 'Sold out' : s.quantity <= LOW_STOCK ? `Only ${s.quantity} left` : 'In stock'}
                  </span>
                </button>
              )
            })}
          </div>
          <p className="stock-note">
            {selectedStock
              ? `${selectedStock.size}: ${selectedStock.quantity} in stock`
              : product.total_stock > 0
                ? `${product.total_stock} units in stock across all sizes. Select a size to see availability.`
                : 'This item is currently sold out in every size.'}
          </p>

          <AddToCart
            selected={selectedStock ?? null}
            soldOutEverywhere={product.total_stock === 0}
            alreadyInCart={selectedStock ? inCart(product.product_id, selectedStock.size) : 0}
            added={added}
            onAdd={() => {
              if (!selectedStock) return
              addToCart({
                product_id: product.product_id,
                name: product.name,
                size: selectedStock.size,
                price: product.price,
                image_url: product.image_url,
                max: selectedStock.quantity,
              })
              setAdded(selectedStock.size)
              celebrateAddToCart() // Handsome Dan pops up with encouragement
            }}
          />

          <table className="stock-table">
            <caption>Stock by size</caption>
            <thead>
              <tr>{product.inventory.map(s => <th key={s.size} scope="col">{s.size}</th>)}</tr>
            </thead>
            <tbody>
              <tr>
                {product.inventory.map(s => (
                  <td key={s.size} className={s.quantity === 0 ? 'zero' : ''}>
                    {s.quantity === 0 ? 'Out' : s.quantity}
                  </td>
                ))}
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </section>
  )
}

function AddToCart(props: {
  selected: { size: string; quantity: number } | null
  soldOutEverywhere: boolean
  alreadyInCart: number
  added: string | null
  onAdd: () => void
}) {
  const { selected, soldOutEverywhere, alreadyInCart, added, onAdd } = props
  // Clickable only when the selected size has stock (and the cart doesn't already hold all of it).
  let label = 'Add to Cart'
  let disabled = false
  let soldOut = false
  if (soldOutEverywhere || selected?.quantity === 0) {
    label = 'Sold Out'
    disabled = soldOut = true
  } else if (!selected) {
    label = 'Select a size'
    disabled = true
  } else if (alreadyInCart >= selected.quantity) {
    label = 'All available units are in your cart'
    disabled = true
  }
  return (
    <div className="add-to-cart">
      <button
        className={`btn btn-primary btn-block add-to-cart-btn ${soldOut ? 'sold-out' : ''}`}
        disabled={disabled}
        onClick={onAdd}
      >
        {label}
      </button>
      {added && (
        <p className="add-to-cart-note" role="status">
          Added size {added} to your cart{alreadyInCart > 1 ? ` (${alreadyInCart} in cart)` : ''}.{' '}
          <Link to="/cart">View cart &rarr;</Link>
        </p>
      )}
    </div>
  )
}
