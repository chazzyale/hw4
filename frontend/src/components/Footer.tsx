import { Link } from 'react-router-dom'

const YEAR = new Date().getFullYear()

export default function Footer() {
  return (
    <footer className="site-footer">
      <div className="container footer-grid">
        <div>
          <p className="footer-brand">Campus Customs</p>
          <p>Delivering Yale tradition for half a century.</p>
        </div>
        <div>
          <p className="footer-heading">Visit us</p>
          <p>57 Broadway<br />New Haven, CT 06511</p>
        </div>
        <div>
          <p className="footer-heading">Shop</p>
          <ul>
            <li><Link to="/products">All products</Link></li>
            <li><Link to="/products?category=hoodies">Hoodies</Link></li>
            <li><Link to="/products?collection=residential-colleges">Residential colleges</Link></li>
            <li><Link to="/products?collection=athletics">Yale Athletics</Link></li>
            <li><Link to="/products?collection=family">Yale family</Link></li>
            <li><Link to="/about">About us</Link></li>
          </ul>
        </div>
      </div>
      <div className="container footer-legal">
        &copy; {YEAR} Campus Customs. An independent retailer serving the Yale community.
      </div>
    </footer>
  )
}
