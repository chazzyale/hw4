# Campus Customs: Website Design

This round restyles the Campus Customs site so it clearly reads as a shop for an Ivy League college: refined typography, Yale's colors, sleek section-by-section motion, consistent product imagery, and plenty of Bulldog spirit from Handsome Dan.

**Why:** making the site feel more **professional**, more **connected to Yale**, and more **fun** should resonate with our target audience of Yale students and their families. A site that looks like it belongs to Yale earns trust; tasteful motion and a playful mascot make browsing enjoyable. Together these encourage shoppers to **stay on the site longer** and **make a purchase**.

---

## 1. Sophisticated typography

| Role | Typeface | Why |
|---|---|---|
| Headings, product names, prices | **Cormorant Garamond** | A classic Garamond-style serif: elegant, literary, and academic. It is the look of university presses and diplomas. |
| Eyebrows, section taglines, labels | **Cinzel** | Roman inscription capitals, like the lettering carved over collegiate gates and buildings. It gives "REP YOUR SCHOOL WITH PRIDE!" a timeless, engraved feel. |
| Body text, buttons, forms | **Libre Franklin** | A Franklin Gothic revival: the traditional collegiate sans-serif, very readable at small sizes. |

- Buttons use letter-spaced small capitals, and headings use slightly tighter spacing, both hallmarks of high-end editorial and Ivy League design.
- Fonts are self-hosted (installed with the site), so they load fast and don't depend on outside services.
- The hero adds Yale's motto, ***Lux et Veritas***, in italic Garamond above the headline.

## 2. Yale colors for school pride

- **Yale Blue `#00356B`** stays the anchor color (header, hero, buttons, accents), with Yale's secondary blues **`#286DC0`** and **`#63AAFF`** for highlights.
- Sections alternate between white and a warm **parchment** neutral (`#F8F6F1`) with fine beige rules, which feels like old campus stone and paper, instead of plain gray.
- Blue headers carry a subtle diagonal pinstripe texture, like a varsity sweater or a tie.
- Product cards get a Yale Blue rule that draws across the top on hover.

## 3. Sleek motion: landing on each section

- **Section-by-section scrolling on the homepage:** each scroll lands on the next full-screen section (hero, Residential colleges, Yale Athletics, Yale family, footer) instead of scrolling continuously. This uses CSS scroll snapping that stops at each section, aligned exactly below the sticky header (whose real height the site measures).
- **Sections load as you land on them:** the illustration glides in from the side, the heading rises in, and the four product tiles follow one after another.
- **The hero** builds itself on arrival: the Yale "Y" eases in and each line of text rises in turn. A pulsing **Scroll** cue invites the first scroll.
- **On other pages,** product cards, service cards, store facts, and cart items glide in as they scroll into view (in browsers that support scroll-driven animations; others show them immediately).
- **Easing:** all motion uses one soft "ease-out" curve, so it feels fluid and expensive rather than bouncy.
- **Accessibility:** for shoppers who set "reduce motion" on their device, animations are turned off or made instant, and scrolling isn't smoothed.

## 4. Every product photo on a white background

- Many catalogue photos sat on black backgrounds and others on white. Now **every image is presented on white**.
- A one-time script (`backend/scripts/whiten_images.py`) finds the near-pure-black background **connected to the photo's edges** and turns it white, softening the outline so it isn't jagged. Dark garments (navy, charcoal, black) are left intact; all 73 converted photos were checked by eye.
- A second pass also removes **thin black frames and dark letterbox bars** along the edges, including bars that are dark gray rather than pure black. It peels them away line by line from each edge, never more than 12% of the photo, so a dark garment can't be mistaken for a bar. After this pass, no product photo has any dark pixels on its outer edge (checked automatically, and by eye for all 102).
- All 102 photos are standard JPEGs with no transparency, so there were no transparent PNGs to fill.
- The white copies are saved separately (`data/products_white/`) and served automatically. The original catalogue photos are never changed.
- Image addresses include a version tag (`?v=...`), so browsers always load the latest white copies instead of an older cached black-background version. Photos saved in Recent Picks and the cart are refreshed too.
- Product images now sit inside their tiles ("contain") with breathing room, instead of being cropped, for a clean, consistent, catalog-style grid.

## 5. Yale-spirited expressions as you scroll

Each homepage section greets you with a quick pop-up (about 1.4 seconds) when you land on it:

| Section | Pop-up |
|---|---|
| Residential colleges | **"BOOLA BOOLA!"** |
| Yale Athletics | Handsome Dan **chomping a Harvard pennant** (crimson bits flying) with **"BEAT HARVARD!"** |
| Yale family | Handsome Dan **waving a Yale pennant** with **"BULLDOG! BULLDOG! BOW, WOW, WOW!"** |

## 6. Handsome Dan between pages

- **Every time a new page loads,** a Yale Blue curtain sweeps over the screen for about a second while an animated Handsome Dan does something funny or school-spirited, picked at random:
  - chewing on a Harvard pennant ("Handsome Dan is chewing on a Harvard pennant…")
  - wearing a graduation cap, tassel swinging ("Handsome Dan is cramming for finals…")
  - waving a Yale pennant ("Bulldog! Bulldog! Bow, wow, wow!")
  - wagging his tail ("Fetching your page… good boy!")
- It hides the moment of loading, makes navigation feel deliberate, and adds delight. Clicking it skips it.

## 7. Handsome Dan cheers when you add to cart

- When a shopper clicks **Add to Cart**, Handsome Dan pops up in the corner with a speech bubble, chosen at random from: **"Great Choice!"**, **"Looks Good!"**, **"I'd Chew That!"**, **"Boola Boola!"**, **"Bulldog approved!"**, and **"Woof! Excellent pick!"**
- Positive reinforcement at the moment of choosing builds confidence in the purchase.

## 8. Homepage sections: an image beside the products

- Each homepage section is now a two-column layout: a **scene image** on one side and the section's **2x2 preview tiles** on the other, alternating sides from section to section:
  - **Residential colleges:** students waving college banners on the lawn of an ivy-covered Gothic courtyard, with a Harkness-style tower at golden hour.
  - **Yale Athletics:** Yale athletes celebrating under the stadium lights, with a packed Yale-blue crowd, falling confetti, and a "YALE WINS!" scoreboard.
  - **Yale family:** a graduate in a gown throwing a cap in front of an Old Campus building hung with Yale banners, surrounded by family.
- The scenes are gently animated (confetti falls, banners wave, athletes jump, the cap tosses).
- **Large product photos in the tiles:** each section shows **two rows of three tiles** (six products). Narrower tiles at the same height make each photo box nearly square, so the square product photos fill it with very little white space. The tiles fill the full height of the section, and each tile shows the name and price on one line; the description is left to the Products page. The tiles keep the wider column (two-thirds of the width) on both sides of the alternating layout. On a 1280×800 laptop each photo box is about 241×209 px. On phones the tiles are two across.
- **How the images were made:** the course AI key can't generate images (every image model is routed to a text model), so these scenes and the animated Handsome Dan were **drawn by AI (Claude) as code-based vector illustrations**, rather than using photos or GIFs found online, which raise copyright questions. They're crisp at any size and tiny to download. To use AI-generated photos instead, save them as `residential-colleges`, `athletics`, and `family` (`.jpg`, `.png`, or `.webp`) in `frontend/src/assets/sections/`, and the site uses them automatically.

## 9. Mobile-friendly

- On phones and tablets, each homepage section stacks the scene image above the product tiles, and the snap becomes gentle ("proximity"), so sections taller than the screen scroll naturally.
- Sections count as "landed" once they fill most of the screen, so the reveals and cheers work on small screens too.
- The header tightens (smaller brand, one-line top bar, Menu and cart icon side by side), tiles go two-up with compact text, and Handsome Dan's pop-ups shrink.
- Checked at 375px wide (a typical phone): nothing scrolls sideways.

---

### Files

- `frontend/src/design.css`: the design layer (typography, colors, snapping, reveals, Dan's animations, mobile rules).
- `frontend/src/components/HandsomeDan.tsx`: the animated Handsome Dan (chomp, cap, cheer, wag).
- `frontend/src/components/SectionArt.tsx`: the three homepage scene illustrations (with automatic photo override).
- `frontend/src/components/motion.tsx`: scroll reveals, section cheers, the page transition, and the add-to-cart cheer.
- `frontend/src/pages/Home.tsx`: full-screen snapping sections with art beside the tiles.
- `backend/scripts/whiten_images.py`, and `backend/main.py` (serves the white images): consistent white product photos.
