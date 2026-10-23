"""Campus Customs API (run from backend/: uvicorn main:app --reload --port 8000).

Serves the product catalogue and images, account signup/login (tools.py), and the
shop chatbot (agent.py, a PydanticAI agent).
"""

import asyncio
import json
import logging
import re
import sqlite3
from contextlib import asynccontextmanager

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

import agent
import tools
from tools import DATA_DIR, all_products, find_product, get_db, strip_image_url
from models import (
    CartUpdate,
    CartOut,
    HISTORY_RELOAD_LIMIT,
    MAX_PREVIEW_CARDS,
    ChatHistoryResponse,
    ChatRequest,
    ChatResponse,
    ProductPreviewResult,
)

log = logging.getLogger("campus_customs")

@asynccontextmanager
async def lifespan(_: FastAPI):
    tools.ensure_cart_table()  # account carts live in cart_items (created on first run)
    tools.ensure_password_reset_table()  # one-time password reset links
    yield


app = FastAPI(title="Campus Customs API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5175"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Product images live at data/products/*.jpg and are served at /media/products/*.jpg.
# White-background copies (scripts/whiten_images.py) are served instead when they exist.
WHITE_IMAGES = DATA_DIR / "products_white"
if WHITE_IMAGES.is_dir():
    app.mount("/media/products", StaticFiles(directory=WHITE_IMAGES), name="media-white")
app.mount("/media", StaticFiles(directory=DATA_DIR), name="media")


@app.middleware("http")
async def cache_images(request, call_next):
    """Image URLs are versioned (?v=...), so browsers can cache them for a week and still get updates."""
    response = await call_next(request)
    if request.url.path.startswith("/media/"):
        response.headers["Cache-Control"] = "public, max-age=604800"
    return response


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/products")
def list_products(category: str | None = None, collection: str | None = None) -> list[dict]:
    products = all_products()
    if category:
        products = [p for p in products if p["category"] == category]
    if collection:
        products = [p for p in products if collection in p["collections"]]
    return products


@app.get("/api/products/{product_id}")
def get_product(product_id: str) -> dict:
    product = find_product(product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


# --- Accounts ---

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MIN_PASSWORD_LENGTH = 8


class RegisterRequest(BaseModel):
    first_name: str
    last_name: str
    email: str
    password: str
    confirm_password: str


class LoginRequest(BaseModel):
    email: str
    password: str


def public_user(row: sqlite3.Row) -> dict:
    # Never send password_hash to the browser.
    return {
        "id": row["id"],
        "first_name": row["first_name"],
        "last_name": row["last_name"],
        "name": row["name"],
        "email": row["email"],
    }


def session_response(row: sqlite3.Row) -> dict:
    return {"token": tools.create_session_token(row["id"], row["password_hash"]), "user": public_user(row)}


def check_new_password(password: str, confirm_password: str) -> None:
    """Same rules for signup and password reset."""
    if len(password) < MIN_PASSWORD_LENGTH:
        raise HTTPException(400, f"Password must be at least {MIN_PASSWORD_LENGTH} characters.")
    if password != confirm_password:
        raise HTTPException(400, "Passwords do not match.")


@app.post("/api/auth/register", status_code=201)
def register(body: RegisterRequest) -> dict:
    first, last = body.first_name.strip(), body.last_name.strip()
    email = body.email.strip().lower()
    if not first or not last:
        raise HTTPException(400, "First and last name are required.")
    if not EMAIL_RE.match(email):
        raise HTTPException(400, "Enter a valid email address.")
    check_new_password(body.password, body.confirm_password)

    password_hash = tools.make_password_hash(body.password)
    with get_db(writable=True) as conn:
        try:
            cur = conn.execute(
                "INSERT INTO users (name, email, password_hash, first_name, last_name) VALUES (?, ?, ?, ?, ?)",
                (f"{first} {last}", email, password_hash, first, last),
            )
        except sqlite3.IntegrityError:
            raise HTTPException(409, "An account with this email already exists.")
        row = conn.execute("SELECT * FROM users WHERE id = ?", (cur.lastrowid,)).fetchone()
    return session_response(row)


@app.post("/api/auth/login")
def login(body: LoginRequest) -> dict:
    email = body.email.strip().lower()
    with get_db() as conn:
        row = conn.execute("SELECT * FROM users WHERE lower(email) = ?", (email,)).fetchone()
    # Always run one hash check so unknown emails take as long as wrong passwords.
    stored = row["password_hash"] if row else tools.DUMMY_HASH
    if not tools.verify_password(body.password, stored) or row is None:
        raise HTTPException(401, "Incorrect email or password.")
    return session_response(row)


# --- Product Preview "Show More" ---

class PreviewPageRequest(BaseModel):
    query: str = Field(min_length=1, max_length=200)
    offset: int = Field(ge=0, le=500)
    limit: int = Field(default=MAX_PREVIEW_CARDS, ge=1, le=MAX_PREVIEW_CARDS)


@app.post("/api/product-preview")
def product_preview_page(body: PreviewPageRequest) -> ProductPreviewResult:
    """The next 6 Product Preview results for the same search ("Show More" on the page).

    Runs the same garment_type match in the database, with no AI call, so it costs no tokens.
    """
    return tools._preview(body.query, body.offset, body.limit)


# --- Self-service password reset (tools.py) ---

RESET_SENT_MESSAGE = (
    "If an account exists for that email, we've sent a link to reset your password. "
    "It works once and expires in 30 minutes."
)


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetTokenRequest(BaseModel):
    token: str


class ResetPasswordRequest(BaseModel):
    token: str
    password: str
    confirm_password: str


@app.post("/api/auth/forgot-password", status_code=202)
def forgot_password(body: ForgotPasswordRequest) -> dict:
    """Always the same answer, so the page never reveals which emails have accounts."""
    if EMAIL_RE.match(body.email.strip().lower()):
        tools.request_reset(body.email)
    return {"message": RESET_SENT_MESSAGE}


@app.post("/api/auth/reset-password/check")
def check_reset_link(body: ResetTokenRequest) -> dict:
    return {"valid": tools.token_is_valid(body.token)}


@app.post("/api/auth/reset-password")
def reset_password(body: ResetPasswordRequest) -> dict:
    check_new_password(body.password, body.confirm_password)
    row = tools.complete_reset(body.token, body.password)
    if row is None:
        raise HTTPException(400, "This reset link is invalid or has expired. Please request a new one.")
    return session_response(row)  # logged in with the new password; older sessions have ended


def session_user(authorization: str | None) -> sqlite3.Row | None:
    """The logged-in user for an "Authorization: Bearer <token>" header, or None."""
    token = (authorization or "").removeprefix("Bearer ").strip()
    claims = tools.read_session_token(token) if token else None
    if claims is None:
        return None
    with get_db() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (claims["uid"],)).fetchone()
    # A password reset ends every session that was created with the old password.
    if row is None or not tools.session_is_current(claims, row["password_hash"]):
        return None
    return row


@app.get("/api/auth/me")
def me(authorization: str | None = Header(default=None)) -> dict:
    row = session_user(authorization)
    if row is None:
        raise HTTPException(401, "Not logged in.")
    return public_user(row)


# --- Shop chatbot ---

def products_snapshot(product_ids: list[str]) -> str | None:
    """products_json for an assistant message: the catalogue fields, inventory, and total stock shown
    with the reply (same shape as the seed rows)."""
    snapshot = []
    for pid in product_ids:
        p = find_product(pid)
        if p is None:
            continue
        snapshot.append({
            "product_id": p["product_id"],
            "name": p["name"],
            "garment_type": p["garment_type"],
            "description": p["description"],
            "colors": p["colors"],
            "search_tags": p["search_tags"],
            "image_file_path": strip_image_url(p["image_url"]),
            "image_url": p["image_url"],
            "price": p["price"],
            "inventory": p["inventory"],
            "total_stock": p["total_stock"],
        })
    return json.dumps(snapshot) if snapshot else None


# --- Account cart ---

@app.get("/api/cart")
def get_cart(authorization: str | None = Header(default=None)) -> CartOut:
    """The logged-in shopper's saved cart, with live prices and stock."""
    user = session_user(authorization)
    if user is None:
        raise HTTPException(401, "Log in to see your saved cart.")
    return tools.load_cart(user["id"])


@app.put("/api/cart")
def put_cart(body: CartUpdate, authorization: str | None = Header(default=None)) -> CartOut:
    """Save the logged-in shopper's whole cart (quantities are limited to what's in stock)."""
    user = session_user(authorization)
    if user is None:
        raise HTTPException(401, "Log in to save your cart.")
    return tools.save_cart(user["id"], body.items)


@app.get("/api/chat/history")
def chat_history(authorization: str | None = Header(default=None)) -> ChatHistoryResponse:
    """For a logged-in shopper: the welcome-back greeting and their 4 most recent saved messages."""
    user = session_user(authorization)
    if user is None:
        raise HTTPException(401, "Log in to see your chat history.")
    return ChatHistoryResponse(
        greeting=f"Welcome back {user['name']}! How can I help you?",
        messages=tools.load_chat_history(user["id"], HISTORY_RELOAD_LIMIT),
    )


@app.post("/api/chat")
async def chat(body: ChatRequest, authorization: str | None = Header(default=None)) -> ChatResponse:
    """One chat turn: the website sends the message, page context, and flow state; the agent replies.

    Logged-in shoppers: the agent gets their name/email and their saved history from chat_messages,
    and the Save Chat History tool stores both the message and the reply. Guests can chat, but
    nothing is saved (the website's own copy of the conversation is used for context).
    """
    user = session_user(authorization)
    customer = tools.get_customer(user["id"]) if user is not None else None

    # Never store a password typed into the chat, and never send it to the model: remove it first.
    # Logged-in shoppers' messages are also checked against their own password hash.
    password_hash = user["password_hash"] if user is not None else None
    cleaned, redacted = await asyncio.to_thread(tools.clean_message, body.message, password_hash)
    history = [t.model_copy(update={"content": tools.clean_message(t.content)[0]}) for t in body.history]
    body = body.model_copy(update={"message": cleaned, "history": history})

    saved_history = None
    if customer is not None:
        # Read history before saving this message, so the agent doesn't see it twice.
        saved_history = tools.load_chat_history(customer.id, agent.HISTORY_TURNS)
        # Saved before calling the agent, so the question is kept even if the agent fails.
        tools.save_chat_history(customer.id, "user", body.message)
    try:
        response = await agent.chat(body, customer=customer, saved_history=saved_history)
    except Exception:
        log.exception("Chat agent failed")
        raise HTTPException(
            502, "Sorry, our shop assistant is having trouble right now. Please try again in a moment."
        )
    if customer is not None:
        # products_json: every product the shopper was shown, chat cards plus Product Preview cards on the page.
        shown = [p.product_id for p in response.products]
        if response.preview:
            shown += [p.product_id for p in response.preview.products]
        snapshot = products_snapshot(list(dict.fromkeys(shown)))
        tools.save_chat_history(customer.id, "assistant", response.reply, snapshot)
    if redacted:
        # Let the chat panel replace what the shopper typed, so the password doesn't stay on screen either.
        response.user_message = cleaned
    return response
