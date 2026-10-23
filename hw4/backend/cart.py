"""Account carts: a logged-in shopper's cart is stored in the cart_items table, so it follows them
across devices and sessions. Guests keep their cart in the browser only.

Quantities are always limited to live inventory, and there is no checkout.
"""

from pydantic import BaseModel, Field

from tools import SIZE_ORDER, find_product, get_db

MAX_CART_LINES = 50


def ensure_table() -> None:
    """Create cart_items if it doesn't exist yet (run once at startup)."""
    with get_db(writable=True) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS cart_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id TEXT NOT NULL,
                size TEXT NOT NULL,
                quantity INTEGER NOT NULL CHECK (quantity > 0),
                updated_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (product_id) REFERENCES catalogue(product_id),
                UNIQUE (user_id, product_id, size)
            )
            """
        )


class CartLine(BaseModel):
    product_id: str = Field(max_length=200)
    size: str = Field(max_length=5)
    quantity: int = Field(ge=0, le=999)


class CartUpdate(BaseModel):
    """PUT /api/cart: the shopper's whole cart, which replaces what's saved."""

    items: list[CartLine] = Field(default_factory=list, max_length=MAX_CART_LINES)


class CartItemOut(BaseModel):
    product_id: str
    name: str
    size: str
    price: float
    image_url: str
    quantity: int
    max: int = Field(description="Units in stock for this size right now.")


class CartOut(BaseModel):
    items: list[CartItemOut]
    adjusted: list[str] = Field(
        default_factory=list, description="Lines whose quantity was lowered (or removed) because of stock."
    )


def _validated(lines: list[CartLine]) -> tuple[list[tuple[dict, str, int, int]], list[str]]:
    """Merge duplicate lines, drop unknown products/sizes, and limit quantities to live stock."""
    merged: dict[tuple[str, str], int] = {}
    for line in lines:
        key = (line.product_id, line.size.upper())
        merged[key] = merged.get(key, 0) + line.quantity
    out, adjusted = [], []
    for (pid, size), qty in merged.items():
        product = find_product(pid)
        if product is None or size not in SIZE_ORDER or qty <= 0:
            continue
        stock = next((s["quantity"] for s in product["inventory"] if s["size"] == size), 0)
        if qty > stock:
            adjusted.append(f"{product['name']} ({size})")
            qty = stock
        if qty > 0:
            out.append((product, size, qty, stock))
    return out, adjusted


def _to_out(rows: list[tuple[dict, str, int, int]], adjusted: list[str]) -> CartOut:
    return CartOut(
        items=[
            CartItemOut(
                product_id=p["product_id"], name=p["name"], size=size, price=p["price"],
                image_url=p["image_url"], quantity=qty, max=stock,
            )
            for p, size, qty, stock in rows
        ],
        adjusted=adjusted,
    )


def load_cart(user_id: int) -> CartOut:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT product_id, size, quantity FROM cart_items WHERE user_id = ? ORDER BY id", (user_id,)
        ).fetchall()
    lines = [CartLine(product_id=r["product_id"], size=r["size"], quantity=r["quantity"]) for r in rows]
    valid, adjusted = _validated(lines)
    return _to_out(valid, adjusted)


def save_cart(user_id: int, lines: list[CartLine]) -> CartOut:
    """Replace the shopper's saved cart with these lines (limited to stock) and return it."""
    valid, adjusted = _validated(lines)
    with get_db(writable=True) as conn:
        conn.execute("DELETE FROM cart_items WHERE user_id = ?", (user_id,))
        conn.executemany(
            "INSERT INTO cart_items (user_id, product_id, size, quantity) VALUES (?, ?, ?, ?)",
            [(user_id, p["product_id"], size, qty) for p, size, qty, _ in valid],
        )
    return _to_out(valid, adjusted)
