# Campus Customs: Yale apparel shop with an AI shopping assistant (HW4)

A customer-facing storefront for Campus Customs, a family-run Yale apparel shop at 57 Broadway, New Haven. Shoppers can browse products, create an account, chat about merchandise with an AI assistant, see matching products appear right on the page, and get honest, database-backed answers about price and stock.

- **Front end:** React + Vite + TypeScript (`frontend/`)
- **Back end:** Python FastAPI (`backend/`) with a **PydanticAI** agent
- **Database:** SQLite (`data/campus_customs.db`, from the course data pack; not in this repo)

For a full, business-friendly explanation of how everything works (data models, tools, safety rules, audit trail, and specs), see **[output/harness.md](output/harness.md)**.

## Repository layout

```
hw4/
├── backend/
│   ├── prompts/prompt.md     ┐
│   ├── agent.py              │  The agent: exactly these four files
│   ├── tools.py              │
│   ├── models.py             ┘
│   ├── main.py               # FastAPI app (run with Uvicorn): products, accounts, cart, chat routes
│   ├── auth.py, privacy.py, cart.py, password_reset.py, mailer.py   # supporting web-app modules
│   ├── scripts/whiten_images.py  # optional: put product photos on white backgrounds
│   ├── requirements.txt
│   └── .env.example          # copy to backend/.env (placeholders only)
├── frontend/                 # React + Vite + TypeScript website
├── data/                     # put the data pack here (see below; not committed)
├── output/                   # harness.md, usability.md, design.md, app_check.html, audit_trail.json
└── AI_prompts.md             # log of the prompts used to build this homework
```

**The agent** is four files under `backend/`:

| File | What it is |
|---|---|
| `prompts/prompt.md` | System prompt: Campus Customs voice, tool flows, safety and audit rules |
| `agent.py` | Agent entry and wiring: model, prompt, tools, structured output, loop limits, audit trail |
| `tools.py` | The 7 tools the agent can call (Product Confirmation, Information Output, Product Preview, page context, General Inquiry, catalogue overview) and their database helpers |
| `models.py` | Pydantic / PydanticAI structured types for requests, tool results, and replies |

## Prerequisites

- **Python 3.11+** (developed on 3.14)
- **Node.js 20.19+ or 22.12+** (developed on Node 24)
- An API key for the course **Portkey** gateway (for the chatbot)
- The course **data pack** (`data.zip`)

## 1. Place the data pack

The real database and product images are not in this repository. Unzip the data pack into `hw4/data/` so you have:

```
hw4/data/campus_customs.db
hw4/data/products/*.jpg
```

## 2. Configure the back end

Copy the example environment file and add your key:

```bash
cd backend
cp .env.example .env
```

Then edit `backend/.env` and set `PORTKEY_API_KEY`. The other settings have working defaults; see the comments in `.env.example`.

## 3. Run the back end (FastAPI, port 8000)

From the `backend/` folder:

```bash
python -m venv .venv
```

Activate it (Windows: `.venv\Scripts\activate`; macOS/Linux: `source .venv/bin/activate`), then:

```bash
pip install -r requirements.txt
```

```bash
uvicorn main:app --reload --port 8000
```

Check it's up at http://localhost:8000/api/health.

**Optional:** put every product photo on a white background (a one-time step that creates `data/products_white/`; the server uses it automatically if it exists):

```bash
python scripts/whiten_images.py
```

## 4. Run the front end (React + Vite, port 5175)

In a second terminal, from the `frontend/` folder:

```bash
npm install
```

```bash
npm run dev
```

Open **http://localhost:5175**. The dev server forwards `/api` and `/media` requests to the back end on port 8000, so both must be running.

## Try it

- **Test account:** `test@campuscustoms.yale.edu` / `password` (from the data pack), or create your own account.
- **In the chat** (bottom right), try:
  - "A navy hoodie with big white YALE letters" (confirm the item, then pick a size for price and stock)
  - "What hoodies do you have?" (cards appear on the page, with **Show More**)
  - "Do you have anything in green?"
  - On a product page: "Do you have this in large?"
- **Forgot your password?** Without an email server configured, reset emails are saved to `backend/outbox/`; open the newest file for the link.
- **Audit trail:** every chat turn is appended to `output/audit_trail.json`.

## Notes

- Restart the back end after editing `backend/prompts/prompt.md` (the agent loads it at startup).
- The back end creates two extra tables on first run: `cart_items` (account carts) and `password_resets`.
- Never commit `backend/.env`, the database, or the product images; `.gitignore` already excludes them.

## Documentation

| File | Contents |
|---|---|
| [output/harness.md](output/harness.md) | How the system works: models, tools, safety rules, audit trail, specs |
| [output/usability.md](output/usability.md) | Usability improvements (cart, Recent Picks, chat password protection, General Inquiry, password reset) |
| [output/design.md](output/design.md) | Site design and why |
| [output/app_check.html](output/app_check.html) | Manual test checks with screenshots |
| [AI_prompts.md](AI_prompts.md) | The prompts used for each problem |
