# Campus Customs: Usability Improvements

This round adds two front-end improvements and two backend improvements to the Campus Customs website and shop chatbot. Each section explains what we added and why it helps a Campus Customs shopper or the business.

---

## Front end 1: "Add to Cart" and "View Cart"

### What we added

- **Add to Cart button on every product page** (the large single-item page), under the size options.
  - It is **clickable** when the selected size has inventory.
  - It is **grayed out, reads "Sold Out", and can't be clicked** when the selected size has 0 inventory (or the product is sold out in every size). Sold-out sizes can still be selected, so shoppers see clearly that this size is unavailable.
  - Before a size is chosen, it reads "Select a size". If the cart already holds every unit in stock for that size, it says so and can't be clicked.
  - After adding, a confirmation appears ("Added size M to your cart") with a **View cart** link.
- **Cart page** (`/cart`) that lists everything added: photo, name (links back to the product page), size, price each, quantity, and line total, plus a summary with the item count and total.
  - **Increase or decrease** the quantity with − / + buttons. The + button stops at the **maximum inventory available** for that product size, so the cart can never hold more than we have.
  - **Remove** any item from the cart.
  - When the cart opens, it **re-checks live stock** from the database. If stock dropped since an item was added, its quantity is lowered and the shopper is told.
- **Cart icon in the header banner**, to the right of the "Menu" button (on wide screens, to the right of the nav links). A badge shows how many items are in the cart, and clicking it opens the cart page.
- **The cart follows logged-in shoppers across devices and sessions.** When a shopper is logged in, every change (add, +/−, remove) is saved to their account in a new `cart_items` database table. When they log in on another device, or come back days later, the same cart loads. Switching back to an open tab picks up changes made elsewhere.
  - **Guests** keep their cart in the browser. If they log in, that guest cart is **merged** into their account cart, so nothing they picked is lost.
  - **Logging out** clears the cart from that browser (it stays saved in the account), so the next person using a shared computer doesn't see it.
  - The server always limits quantities to live stock when it saves or loads a cart.
- **No checkout, on purpose.** We are explicitly not building a "Checkout" option yet, so the site can't take a purchase. The cart summary invites shoppers to bring their list to the store at 57 Broadway, and the chatbot knows the cart exists but that there's no online checkout.

Files: `frontend/src/shop.tsx` (cart state and account sync), the cart functions in `backend/tools.py` and `GET`/`PUT /api/cart` in `backend/main.py` (account carts), `frontend/src/pages/Cart.tsx`, `frontend/src/pages/ProductDetail.tsx` (Add to Cart), `frontend/src/components/NavBar.tsx` (cart icon).

### Why it helps

- **Shoppers:** until now there was no way to collect items they want. Now they can build a list of exact products and sizes, adjust quantities, and see a running total, with no risk of picking a sold-out size or more units than exist.
- **Shoppers (account carts):** a cart built on a phone between classes is waiting on the laptop at home, and it's still there after closing the browser.
- **Campus Customs:** the site couldn't lead to a sale as it was set up. A cart is the first step toward purchases: it captures shopper intent and brings ready-to-buy customers into the store. Because the limits match real inventory, the business never promises stock it doesn't have.

---

## Front end 2: "Your Recent Picks"

### What we added

- A **small row stuck to the bottom of the screen** titled **"Your Recent Picks"**, showing the **5 most recent products the shopper clicked into** (the large product page), newest first, each with a thumbnail, name, and price.
- It **updates automatically**: opening a product page moves that product to the front. Revisiting a product doesn't create duplicates, and only the latest 5 are kept.
- Clicking a pick goes straight back to that product's page.
- The row can be collapsed to just its title. It appears only after the first product view, and the page and chat button shift up so nothing is hidden behind it.
- Saved in the browser, so picks are still there on the next visit.

Files: `frontend/src/components/RecentPicks.tsx`, `frontend/src/shop.tsx` (recent picks state).

### Why it helps

- **Shoppers:** comparing options (for example several residential college crewnecks) means bouncing between product pages. Recent Picks keeps those products one click away, so nobody has to search for an item again.
- **Campus Customs:** keeping recently viewed products top of mind encourages shoppers to come back to items they were interested in, which can raise purchase conversions.

---

## Backend 1: Never store a customer's password from the chat

### What we added

- Even with the chatbot's guardrails, a shopper could type their password into the chat, and it would have been saved in the `chat_messages` history (and sent to the AI model). Now **a password typed into the chat is never stored.**
- Every chat message is cleaned by `clean_message()` in `backend/tools.py` **before** it is saved and **before** it reaches the agent:
  1. Anything following a password phrase ("my password is …", "password: …", "reset my password to …") is removed, for guests and logged-in shoppers.
  2. For logged-in shoppers, each longer word is also checked against **their own stored password hash**, using the same secure check as login. That catches their real password even when it's typed on its own ("here it is Bulldog#2026"). The check only compares hashes; the password itself is never written anywhere.
  3. Each match becomes **`[password removed]`** in the saved message, in what the agent sees, and on the shopper's screen.
- The agent then gently reminds the shopper that we never keep passwords from chat and they shouldn't share one.

### Why it helps

- **Shoppers:** a moment of carelessness (or a panicked "here's my password, please help") no longer leaves their password sitting in a database or with a third-party AI provider.
- **Campus Customs:** passwords are the most sensitive data we hold. Keeping them out of chat logs keeps data protection extremely high, avoids data-privacy problems, and protects customer trust. The rule is enforced in code, not left to the AI model.

---

## Backend 2: Better product understanding with "General Inquiry"

### What we added

- Asking "do you have anything in green?" used to send the agent looking for one specific product. Now broad questions that **aren't about a specific product** go to a new **General Inquiry** tool (`general_inquiry`). Questions about one specific item still use Product Confirmation, and "this" on a product page ("do you have this in pink?") still uses the page-context tools.
- **Step 1: understand the ask.** The tool first works out what the shopper is asking about: an **order**, a **color**, a **product type**, a **theme** (residential college, sport, Yale family, vintage), a **budget**, a **size**, or a **gift**. One question can have several ("navy hoodies under $70" is color + product type + budget).
- **Step 2: search the catalogue for the best matches:**
  - **Color** questions query the catalogue's **`colors`** field ("green" finds the 4 products that come in green; "pink" honestly finds none).
  - **Product type / category** questions match **`garment_type`**, and themes match **`search_tags`** (then name and description).
  - Budget filters by price, and size keeps only items in stock in that size.
  - Up to 6 best matches are shown as product cards in the chat.
  - **Order** questions ("where is my order?") get an honest answer: there's no online ordering yet, so the agent points to the cart and the store instead of searching products or inventing order details.
- **Step 3: never run longer than 12 seconds.** If a search would take longer, it stops and the agent offers to try again. A typical search takes about 10 milliseconds.

Files: `backend/tools.py` (`general_inquiry`), `backend/models.py` (`GeneralInquiryResult`, `InquiryUnderstanding`, `InquiryProduct`), `backend/prompts/prompt.md`.

### Why it helps

- **Shoppers:** they can ask the way people actually shop ("anything in green?", "gift for a Saybrook student", "hockey gear in XL", "tees under $35") and get relevant products right away, instead of being asked to describe one item.
- **Campus Customs:** better matches mean more products discovered and more chances to sell. The search runs in the database, not in the AI model, and the 12-second cap means a broad question never turns into a long, expensive run. That saves tokens and keeps the chatbot fast.

---

## Account improvement: Self-service password reset

*(Added during Problem 10 testing; it belongs with these usability improvements.)*

### What we added

- A **"Forgot your password?"** link on the Log in page. The customer enters their account email, and we email them a **one-time link** to choose a new password. The link works once and expires in 30 minutes.
- The **"Choose a new password"** page uses the same password rules as signup (at least 8 characters, confirmed), then logs the customer straight in.
- **Security built in:**
  - Only a hash of each link's secret token is stored.
  - New passwords are salted and hashed exactly like signup.
  - Resetting signs out every other device.
  - The page never reveals whether an email has an account.
  - A customer's inbox can't be flooded (at most 3 links per hour).
- The chatbot now points customers to "Forgot your password?" instead of sending them to the store. It still never sees, shares, or resets a password itself.

### Why it helps

- **Shoppers:** a forgotten password no longer means a dead end or a trip to 57 Broadway. They can be back in their account (with their saved cart and chat history) in a minute, at any hour.
- **Campus Customs:** fewer lost customers at login, fewer support requests for staff, and a secure, standard reset process that protects customer accounts.
