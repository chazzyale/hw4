import { Link } from 'react-router-dom'
import { formatPrice, type Product } from '../api'

// Anything with these fields can be a card: catalogue products and Product Preview results.
export type CardProduct = Pick<Product, 'product_id' | 'name' | 'price' | 'description' | 'image_url' | 'total_stock'>

export default function ProductCard({ product }: { product: CardProduct }) {
  const soldOut = product.total_stock === 0
  return (
    <Link to={`/products/${product.product_id}`} className="product-card">
      <div className="product-card-image">
        <img src={product.image_url} alt={product.name} loading="lazy" />
        {soldOut && <span className="badge badge-muted">Sold out</span>}
      </div>
      <div className="product-card-body">
        <h3>{product.name}</h3>
        <p className="product-card-desc">{product.description}</p>
        <p className="price">{formatPrice(product.price)}</p>
      </div>
    </Link>
  )
}
