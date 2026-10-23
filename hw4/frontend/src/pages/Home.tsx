import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { fetchProducts, type Collection, type Product } from '../api'
import ProductCard from '../components/ProductCard'
import SectionArt from '../components/SectionArt'
import YaleY from '../components/YaleY'
import { SectionCheer, useInView, type Cheer } from '../components/motion'

const SECTIONS: { collection: Collection; title: string; tagline: string; cheer: Cheer }[] = [
  {
    collection: 'residential-colleges',
    title: 'Residential colleges',
    tagline: 'REP YOUR SCHOOL WITH PRIDE!',
    cheer: { text: 'BOOLA BOOLA!' },
  },
  {
    collection: 'athletics',
    title: 'Yale Athletics',
    tagline: 'BULLDOG ATHLETICS - TOP OF THE PACK',
    cheer: { text: 'BEAT HARVARD!', pose: 'chomp' },
  },
  {
    collection: 'family',
    title: 'Yale family',
    tagline: 'HAPPILY BRAG ABOUT YOUR BULLDOGS!',
    cheer: { text: 'BULLDOG! BULLDOG! BOW, WOW, WOW!', pose: 'cheer' },
  },
]

const PER_SECTION = 6 // two rows of three tiles beside the section image

function Banner() {
  return (
    <section className="hero snap-section">
      <YaleY className="hero-logo" color="#ffffff" gapColor="#00356b" />
      <div className="hero-content container">
        <p className="hero-motto">Lux et Veritas</p>
        <p className="eyebrow">Est. 1975 &middot; 57 Broadway &middot; New Haven</p>
        <h1>Yale pride, made to wear.</h1>
        <p className="hero-lede">
          Sweatshirts, tees, and game-day gear for every Bulldog, from the family-run shop that has dressed Yale
          for half a century.
        </p>
        <div className="hero-actions">
          <Link to="/products" className="btn btn-light">Shop the collection</Link>
          <Link to="/about" className="btn btn-outline-light">Our story</Link>
        </div>
      </div>
      <a href="#residential-colleges" className="scroll-cue" aria-label="Scroll to the collections">
        <span>Scroll</span>
        <svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true">
          <path d="M6 9l6 6 6-6" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
        </svg>
      </a>
    </section>
  )
}

function CollectionSection({ section, index, products, loading }: {
  section: (typeof SECTIONS)[number]
  index: number
  products: Product[]
  loading: boolean
}) {
  const [ref, landed] = useInView<HTMLElement>(0.55)
  return (
    <section
      ref={ref}
      id={section.collection}
      className={`collection-section snap-section ${index % 2 ? 'alt flip' : ''} ${landed ? 'is-revealed' : ''}`}
    >
      <SectionCheer cheer={section.cheer} show={landed} />
      <div className="container collection-grid">
        <div className="collection-art">
          <SectionArt collection={section.collection} />
        </div>
        <div className="collection-body">
          <div className="section-head">
            <div>
              <p className="eyebrow">{section.title}</p>
              <h2 className="tagline">{section.tagline}</h2>
            </div>
            {products.length > 0 && (
              <Link to={`/products?collection=${section.collection}`} className="text-link">
                Shop all {products.length} &rarr;
              </Link>
            )}
          </div>
          {loading ? (
            <p className="muted">Loading...</p>
          ) : products.length > 0 ? (
            <div className="collection-tiles">
              {products.slice(0, PER_SECTION).map((p, i) => (
                <div key={p.product_id} className="tile-in" style={{ ['--i' as string]: i }}>
                  <ProductCard product={p} />
                </div>
              ))}
            </div>
          ) : (
            <div className="empty-card">
              <p>More {section.title} gear is in the shop at 57 Broadway and coming soon online.</p>
              <Link to="/about" className="text-link">Plan a visit &rarr;</Link>
            </div>
          )}
        </div>
      </div>
    </section>
  )
}

export default function Home() {
  const [products, setProducts] = useState<Product[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchProducts().then(setProducts).catch(e => setError(e.message))
  }, [])

  // Section-by-section scrolling: each scroll lands on the next full-screen section (homepage only).
  useEffect(() => {
    document.documentElement.classList.add('snap-page')
    return () => document.documentElement.classList.remove('snap-page')
  }, [])

  return (
    <>
      <Banner />
      {error && <p className="container page-message error">Couldn't load products: {error}</p>}
      {SECTIONS.map((s, i) => (
        <CollectionSection
          key={s.collection}
          section={s}
          index={i}
          products={products?.filter(p => p.collections.includes(s.collection)) ?? []}
          loading={products === null && !error}
        />
      ))}
    </>
  )
}
