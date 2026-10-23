const SERVICES = [
  { title: 'Embroidery', text: 'Custom stitched logos and lettering for teams, clubs, and residential colleges.' },
  { title: 'Design services', text: 'Our designers help bring your Yale-inspired ideas to life.' },
  { title: 'Screen printing', text: 'Large-scale runs for organizations, reunions, and departments.' },
  { title: 'Event merchandise', text: 'Gear for The Game, Commencement, and every celebration in between.' },
]

export default function About() {
  return (
    <>
      <section className="page-header about-header">
        <div className="container">
          <p className="eyebrow">About us &middot; Since 1975</p>
          <h1>Delivering Yale tradition for half a century.</h1>
        </div>
      </section>

      <section className="container about-body">
        <div className="about-story">
          <h2>Our story</h2>
          <p>
            Our family began Campus Customs in 1975 because our father loved Yale so much, he created a Yale
            University memorabilia store on campus. Our entire family fell in love with the store and with Yale,
            so much so that we retired our father and continue to run the shop. There's no store that's more
            prideful, ethical, and Yale-centric.
          </p>
          <p>
            Our business has grown over time. We now offer embroidery, design services, large-scale screen
            printing, and event merchandise services.
          </p>
          <p>
            We've scaled so that we can deliver the experience that you deserve as a fellow Bulldog. We love New
            Haven and Yale University, and it's our genuine pleasure to serve you with what you need to rep your
            Yale school spirit.
          </p>
        </div>

        <aside className="about-facts" aria-label="Store facts">
          <div className="fact"><span className="fact-number">1975</span><span>Family-owned since</span></div>
          <div className="fact"><span className="fact-number">50</span><span>Years serving Bulldogs</span></div>
          <div className="fact"><span className="fact-number">1</span><span>Location on Broadway</span></div>
        </aside>
      </section>

      <section className="category-section alt">
        <div className="container">
          <p className="eyebrow">What we do</p>
          <h2>More than a merch shop</h2>
          <div className="service-grid">
            {SERVICES.map(s => (
              <div key={s.title} className="service-card">
                <h3>{s.title}</h3>
                <p>{s.text}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="container visit">
        <div className="visit-card">
          <div>
            <p className="eyebrow">Visit the store</p>
            <h2>Come visit us at our location at 57 Broadway, New Haven, CT, 06511!</h2>
          </div>
          <a
            className="btn btn-light"
            href="https://www.google.com/maps/search/?api=1&query=57+Broadway+New+Haven+CT+06511"
            target="_blank"
            rel="noreferrer"
          >
            Get directions
          </a>
        </div>
      </section>
    </>
  )
}
