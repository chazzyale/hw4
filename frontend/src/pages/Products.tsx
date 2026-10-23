import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import {
  CATEGORY_LABELS,
  COLLECTION_LABELS,
  fetchProducts,
  type Category,
  type Collection,
  type Product,
} from '../api'
import ProductCard from '../components/ProductCard'

const CATEGORIES = Object.keys(CATEGORY_LABELS) as Category[]
const COLLECTIONS = Object.keys(COLLECTION_LABELS) as Collection[]

export default function Products() {
  const [products, setProducts] = useState<Product[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [params, setParams] = useSearchParams()
  const category = params.get('category') as Category | null
  const collection = params.get('collection') as Collection | null

  useEffect(() => {
    fetchProducts().then(setProducts).catch(e => setError(e.message))
  }, [])

  // Only offer garment chips that have products (e.g. no hats online yet).
  const categories = CATEGORIES.filter(c => products?.some(p => p.category === c))
  const visible =
    products?.filter(
      p => (!category || p.category === category) && (!collection || p.collections.includes(collection)),
    ) ?? []
  const title = collection
    ? COLLECTION_LABELS[collection]
    : category
      ? CATEGORY_LABELS[category]
      : 'All products'

  return (
    <>
      <section className="page-header">
        <div className="container">
          <p className="eyebrow">Shop</p>
          <h1>{title}</h1>
          <p>Yale apparel, printed and stocked right here in New Haven.</p>
        </div>
      </section>

      <section className="container products-page">
        <div className="filters" role="group" aria-label="Filter by garment">
          <button className={!category && !collection ? 'chip active' : 'chip'} onClick={() => setParams({})}>
            All
          </button>
          {categories.map(c => (
            <button
              key={c}
              className={category === c ? 'chip active' : 'chip'}
              onClick={() => setParams({ category: c })}
            >
              {CATEGORY_LABELS[c]}
            </button>
          ))}
        </div>
        <div className="filters" role="group" aria-label="Shop by collection">
          {COLLECTIONS.map(c => (
            <button
              key={c}
              className={collection === c ? 'chip chip-collection active' : 'chip chip-collection'}
              onClick={() => setParams({ collection: c })}
            >
              {COLLECTION_LABELS[c]}
            </button>
          ))}
        </div>

        {error && <p className="page-message error">Couldn't load products: {error}</p>}
        {products === null && !error && <p className="muted">Loading products...</p>}
        {products && (
          <>
            <p className="muted result-count">{visible.length} {visible.length === 1 ? 'item' : 'items'}</p>
            {visible.length > 0 ? (
              <div className="product-grid">
                {visible.map(p => <ProductCard key={p.product_id} product={p} />)}
              </div>
            ) : (
              <div className="empty-card">
                <p>No {title.toLowerCase()} online yet. Stop by 57 Broadway to see the full in-store selection.</p>
              </div>
            )}
          </>
        )}
      </section>
    </>
  )
}
