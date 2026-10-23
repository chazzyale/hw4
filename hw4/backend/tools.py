"""Tools the shop agent can call, plus the read-only database helpers they use (also used by main.py).

The agent tools read the catalogue and inventory tables only.

Specific-product questions go through two tools, in order:
1. "Product Confirmation" (product_confirmation): best match on catalogue.description (+ name) -> product name to confirm.
2. "Information Output" (information_output): price and inventory.quantity for the confirmed product_id.

Questions about a type of product ("what hoodies do you have?") use
3. "Product Preview" (product_preview): best match on catalogue.garment_type -> up to 6 cards shown on the page.

Page context ("do you have this in pink?" on a product page) uses identify_page_product and
find_similar_products. Broad questions that aren't about one product ("anything in green?", gifts, budgets)
use "General Inquiry" (general_inquiry). catalogue_overview summarizes the whole shop.

"Save Chat History" (save_chat_history), load_chat_history, and get_customer read/write the users and
chat_messages tables for the logged-in shopper only. The server calls them; they are not given to the model.
"""

import asyncio
import base64
import hashlib
import hmac
import json
import logging
import math
import os
import re
import secrets
import smtplib
import sqlite3
import time
from email.message import EmailMessage
from pathlib import Path

from dotenv import find_dotenv, load_dotenv

from models import (
    CartLine,
    CartItemOut,
    CartOut,
    MAX_PREVIEW_CARDS,
    PREVIEW_NOT_FOUND_REPLY,
    CustomerInfo,
    GeneralInquiryResult,
    HistoryMessage,
    InquiryProduct,
    InquiryUnderstanding,
    InformationOutputResult,
    PageProductResult,
    PreviewProduct,
    ProductConfirmationResult,
    ProductMatch,
    ProductPreviewResult,
    SavedChatMessage,
    SimilarProduct,
    SimilarProductsResult,
    SizeQuantity,
)

# Settings such as SITE_URL, SMTP_*, and CC_SESSION_SECRET are read at import time, so load .env first.
load_dotenv(find_dotenv())


# --- Database access and product shaping (shared with the API routes in main.py) ---

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
# CC_DB_PATH lets tests point at a copy of the database.
DB_PATH = Path(os.environ.get("CC_DB_PATH", DATA_DIR / "campus_customs.db"))
SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL"]
LOW_STOCK_MAX = 5  # a size with 1 to 5 units left is "low stock"

# Image URLs carry a version (newest image file time), so browsers fetch fresh copies whenever the
# product photos are re-processed instead of showing an old cached version.
_image_dir = DATA_DIR / "products_white" if (DATA_DIR / "products_white").is_dir() else DATA_DIR / "products"
IMAGE_VERSION = max((int(p.stat().st_mtime) for p in _image_dir.glob("*.jpg")), default=0)


def image_url(image_file_path: str) -> str:
    return f"/media/{image_file_path}?v={IMAGE_VERSION}"


def strip_image_url(url: str) -> str:
    """"/media/products/x.jpg?v=123" -> "products/x.jpg" (the catalogue's image_file_path)."""
    return url.split("?", 1)[0].removeprefix("/media/").lstrip("/")


def get_db(writable: bool = False) -> sqlite3.Connection:
    # Read-only by default: only signup writes (to the users table).
    mode = "rw" if writable else "ro"
    conn = sqlite3.connect(f"file:{DB_PATH.as_posix()}?mode={mode}", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def category_for(garment_type: str) -> str:
    """Map the inconsistent free-text garment_type values onto the shop's categories."""
    g = garment_type.lower()
    if "t-shirt" in g:
        return "t-shirts"
    if "hat" in g or "cap" in g or "beanie" in g:
        return "hats"
    if "hood" in g:
        return "hoodies"
    if "quarter-zip" in g:
        return "quarter-zips"
    if any(k in g for k in ("crewneck", "sweatshirt", "mockneck")):
        return "crewnecks"
    if "jacket" in g or "fleece" in g:
        return "outerwear"
    return "other"


RESIDENTIAL_COLLEGES = (
    "benjamin franklin", "berkeley", "branford", "davenport", "ezra stiles", "grace hopper",
    "jonathan edwards", "morse", "pauli murray", "pierson", "saybrook", "silliman",
    "timothy dwight", "trumbull",
)
# Word-boundary match; rowing is only "Crew Left Chest" since some crewnecks are named just "Crew".
SPORTS_RE = re.compile(
    r"\b(baseball|basketball|crew left chest|diving|fencing|football|hockey|lacrosse|sailing|soccer|swim\w*|"
    r"tennis|track|squash|golf|volleyball|softball|rugby|wrestling|gymnastics|rowing)\b"
)
FAMILY_RE = re.compile(r"\b(dad|mom|parent|family|grandparent|grandma|grandpa|alumni)\b")


def collections_for(name: str, search_tags: list[str]) -> list[str]:
    """Themed groupings used for the homepage sections, matched on product names."""
    n = name.lower()
    tags = " ".join(search_tags).lower()
    found = []
    if any(c in n for c in RESIDENTIAL_COLLEGES):
        found.append("residential-colleges")
    if SPORTS_RE.search(n) or "the game" in tags:
        found.append("athletics")
    if FAMILY_RE.search(n):
        found.append("family")
    return found


def product_from_row(row: sqlite3.Row, inventory: list[dict]) -> dict:
    search_tags = json.loads(row["search_tags"])
    return {
        "product_id": row["product_id"],
        "name": row["name"],
        "garment_type": row["garment_type"],
        "category": category_for(row["garment_type"]),
        "collections": collections_for(row["name"], search_tags),
        "description": row["description"],
        "colors": json.loads(row["colors"]),
        "search_tags": search_tags,
        "image_url": image_url(row["image_file_path"]),
        "price": row["price"],
        "inventory": inventory,
        "total_stock": sum(i["quantity"] for i in inventory),
    }


def load_inventory(conn: sqlite3.Connection) -> dict[str, list[dict]]:
    by_product: dict[str, list[dict]] = {}
    for r in conn.execute("SELECT product_id, size, quantity FROM inventory"):
        by_product.setdefault(r["product_id"], []).append({"size": r["size"], "quantity": r["quantity"]})
    for sizes in by_product.values():
        sizes.sort(key=lambda s: SIZE_ORDER.index(s["size"]) if s["size"] in SIZE_ORDER else len(SIZE_ORDER))
    return by_product


def all_products() -> list[dict]:
    with get_db() as conn:
        inventory = load_inventory(conn)
        rows = conn.execute("SELECT * FROM catalogue ORDER BY name").fetchall()
    return [product_from_row(r, inventory.get(r["product_id"], [])) for r in rows]


def find_product(product_id: str) -> dict | None:
    with get_db() as conn:
        row = conn.execute("SELECT * FROM catalogue WHERE product_id = ?", (product_id,)).fetchone()
        if row is None:
            return None
        inventory = load_inventory(conn).get(product_id, [])
    return product_from_row(row, inventory)


# --- Agent tools ---

TOOL_TIMEOUT_SECONDS = 30

STOPWORDS = {
    "a", "an", "and", "any", "are", "do", "for", "have", "i", "in", "is", "it", "me", "my", "of", "on",
    "or", "show", "some", "something", "the", "to", "want", "with", "you", "your", "looking", "need",
    "yale", "size", "sizes", "stock", "available", "please", "can", "get", "what", "which",
}
# Shopper words -> words used in the catalogue.
SYNONYMS = {
    "tee": "t-shirt", "tees": "t-shirt", "tshirt": "t-shirt", "t-shirts": "t-shirt",
    "hoody": "hoodie", "hoodies": "hoodie", "hooded": "hoodie",
    "sweatshirts": "sweatshirt", "crewnecks": "crewneck",
    "quarterzip": "quarter-zip", "1/4": "quarter-zip",
    "jackets": "jacket", "grey": "gray",
    "dog": "bulldog", "dan": "bulldog", "mother": "mom", "father": "dad",
    "grandmother": "grandma", "grandfather": "grandpa",
}
SIZES = {s.lower(): s for s in SIZE_ORDER} | {
    "small": "S", "medium": "M", "large": "L", "xlarge": "XL", "x-large": "XL",
    "xxlarge": "XXL", "2xl": "XXL", "xsmall": "XS", "x-small": "XS",
}


def _url(product_id: str) -> str:
    return f"/products/{product_id}"


def _normalize_size(size: str | None) -> str | None:
    if not size:
        return None
    return SIZES.get(size.strip().lower().replace(" ", ""), size.strip().upper())


# --- Tool 1: Product Confirmation ---

DESCRIBE_STOPWORDS = STOPWORDS | {
    "about", "asking", "item", "inquiring", "like", "one", "this", "that", "there", "these", "those",
    "been", "was", "were", "has", "had", "its", "but", "from", "very", "kind", "type",
}
# Shopper words -> words used in the catalogue descriptions.
DESCRIBE_SYNONYMS = {
    "tee": "shirt", "tees": "shirt", "tshirt": "shirt", "hoody": "hoodie", "hooded": "hoodie",
    "grey": "gray", "sweater": "sweatshirt", "zipper": "zip", "zipped": "zip",
    "dog": "bulldog", "puppy": "bulldog", "letters": "lettering", "words": "lettering",
}


def _tokens(text: str) -> list[str]:
    text = text.lower().replace("1/4", "quarter")
    out = []
    for w in re.findall(r"[a-z0-9]+", text):
        w = DESCRIBE_SYNONYMS.get(w, w)
        if len(w) > 3 and w.endswith("s") and not w.endswith("ss"):
            w = w[:-1]  # hoodies -> hoodie, colors -> color
        if len(w) >= 2 and w not in DESCRIBE_STOPWORDS:
            out.append(w)
    return out


def _confirm(inquiry: str, exclude_product_ids: list[str]) -> ProductConfirmationResult:
    with get_db() as conn:
        rows = conn.execute("SELECT product_id, name, description FROM catalogue").fetchall()

    docs = {r["product_id"]: (set(_tokens(r["description"])), set(_tokens(r["name"]))) for r in rows}
    # Rarer words count for more (inverse document frequency): "saybrook" outweighs "navy".
    df: dict[str, int] = {}
    for desc, name in docs.values():
        for t in desc | name:
            df[t] = df.get(t, 0) + 1
    idf = {t: math.log((len(docs) + 1) / (n + 0.5)) for t, n in df.items()}

    known = [t for t in dict.fromkeys(_tokens(inquiry)) if t in idf]
    scored = []
    if known:
        total = sum(idf[t] for t in known)
        for r in rows:
            if r["product_id"] in exclude_product_ids:
                continue
            desc, name = docs[r["product_id"]]
            # The description is the main field matched; words found only in the name count for half.
            score = sum(idf[t] if t in desc else 0.5 * idf[t] if t in name else 0 for t in known)
            if score > 0:
                scored.append((score / total, r))
    if not scored:
        return ProductConfirmationResult(
            status="no_match", message="No catalogue description matched. Ask the shopper for more details."
        )
    scored.sort(key=lambda x: (-x[0], x[1]["name"]))
    score, best = scored[0]
    return ProductConfirmationResult(
        status="match",
        best_match=ProductMatch(
            product_id=best["product_id"],
            name=best["name"],
            description=best["description"],
            match_score=round(score, 2),
        ),
        other_close_matches=[r["name"] for _, r in scored[1:4]],
        message="Show the shopper the name in quotation marks and ask \"Is this the item you're inquiring about?\"",
    )


async def product_confirmation(
    inquiry: str, exclude_product_ids: list[str] | None = None
) -> ProductConfirmationResult:
    """Product Confirmation: find the catalogue product whose description best matches the shopper's inquiry.

    Call this whenever a shopper describes a specific product, and again (with all the details so far)
    after they say No and describe it further. Then show the returned name in quotation marks and ask
    "Is this the item you're inquiring about?". Do not give price or stock yet.

    Args:
        inquiry: Everything the shopper has said about the item, e.g. "gray crewneck with a red Davenport crest".
        exclude_product_ids: product_ids the shopper already said No to, so they are skipped.
    """
    try:
        return await asyncio.wait_for(
            asyncio.to_thread(_confirm, inquiry, exclude_product_ids or []), TOOL_TIMEOUT_SECONDS
        )
    except TimeoutError:
        return ProductConfirmationResult(
            status="timeout",
            message=f"The catalogue lookup took longer than {TOOL_TIMEOUT_SECONDS} seconds and was stopped.",
        )


# --- Tool 2: Information Output ---

def _display(quantity: int) -> str:
    if quantity == 0:
        return "0 - Sold Out"
    if quantity <= LOW_STOCK_MAX:
        return f"{quantity} - Low Stock"
    return str(quantity)


def _information(product_id: str, size: str | None) -> InformationOutputResult:
    with get_db() as conn:
        product = conn.execute(
            "SELECT product_id, name, price FROM catalogue WHERE product_id = ?", (product_id,)
        ).fetchone()
        if product is None:
            return InformationOutputResult(
                status="not_found",
                product_id=product_id,
                message="No product with this product_id in the catalogue. Do not make up a price or stock.",
            )
        query = "SELECT size, quantity FROM inventory WHERE product_id = ?"
        params: tuple = (product_id,)
        if size:
            query += " AND size = ?"
            params += (size,)
        rows = conn.execute(query, params).fetchall()

    sizes = sorted(
        (SizeQuantity(size=r["size"], quantity=r["quantity"], display=_display(r["quantity"])) for r in rows),
        key=lambda s: SIZE_ORDER.index(s.size) if s.size in SIZE_ORDER else len(SIZE_ORDER),
    )
    if product["price"] is None or not sizes:
        return InformationOutputResult(
            status="not_found",
            product_id=product_id,
            name=product["name"],
            size_requested=size,
            message="The price or inventory for this product/size is missing in the database. "
            "Tell the shopper; do not make up values.",
        )
    return InformationOutputResult(
        status="found",
        product_id=product_id,
        name=product["name"],
        url=f"/products/{product_id}",
        price=product["price"],
        size_requested=size,
        sizes=sizes,
        message="Give the price and the quantity for each size listed, using each size's display text exactly.",
    )


async def information_output(product_id: str, size: str | None = None) -> InformationOutputResult:
    """Information Output: price (catalogue.price) and stock (inventory.quantity) for a confirmed product.

    Call this only after the shopper confirmed the product (said Yes) and answered the size question.

    Args:
        product_id: The product_id the shopper confirmed in Product Confirmation.
        size: The one size they picked (XS, S, M, L, XL, XXL), or omit it to get every size.
    """
    size = _normalize_size(size)
    if size and size not in SIZE_ORDER:
        return InformationOutputResult(
            status="not_found",
            product_id=product_id,
            size_requested=size,
            message=f"'{size}' is not one of our sizes ({', '.join(SIZE_ORDER)}).",
        )
    try:
        return await asyncio.wait_for(asyncio.to_thread(_information, product_id, size), TOOL_TIMEOUT_SECONDS)
    except TimeoutError:
        return InformationOutputResult(
            status="timeout",
            product_id=product_id,
            size_requested=size,
            message=f"The price and inventory lookup took longer than {TOOL_TIMEOUT_SECONDS} seconds and was stopped.",
        )


def catalogue_overview() -> dict:
    """Summarize what the shop carries: product counts by category and collection, and the price range.

    Use this for broad questions like "what do you sell?" or before giving general recommendations.
    """
    products = all_products()
    by_category: dict[str, int] = {}
    by_collection: dict[str, int] = {}
    for p in products:
        by_category[p["category"]] = by_category.get(p["category"], 0) + 1
        for c in p["collections"]:
            by_collection[c] = by_collection.get(c, 0) + 1
    prices = [p["price"] for p in products]
    return {
        "total_products": len(products),
        "by_category": by_category,
        "by_collection": by_collection,
        "price_range": {"min": min(prices), "max": max(prices)},
        "sizes": SIZE_ORDER,
    }


# --- Tool 3: Product Preview ---

# Phrases normalized before splitting into words, so "t-shirt", "tee", and "1/4 zip" line up.
GARMENT_PHRASES = [
    (r"\bt[\s-]?shirts?\b|\btees?\b", " tshirt "),
    (r"\bquarter[\s-]?zips?\b|\b1/4[\s-]?zips?\b|\bqtr[\s-]?zips?\b", " quarterzip "),
    (r"\bfull[\s-]?zips?\b", " fullzip "),
    (r"\bcrew[\s-]?necks?\b", " crewneck "),
    (r"\bshort[\s-]?sleeves?\b", " shortsleeve "),
    (r"\blong[\s-]?sleeves?\b", " longsleeve "),
]
GARMENT_SYNONYMS = {
    "hooded": "hoodie", "hoody": "hoodie", "hoodies": "hoodie", "hood": "hoodie",
    "sweater": "sweatshirt", "coat": "jacket", "crew": "crewneck",
}


def _garment_words(text: str) -> set[str]:
    text = text.lower()
    for pattern, repl in GARMENT_PHRASES:
        text = re.sub(pattern, repl, text)
    words = set()
    for w in re.findall(r"[a-z]+", text):
        w = GARMENT_SYNONYMS.get(w, w)
        if len(w) > 3 and w.endswith("s") and not w.endswith("ss"):
            w = w[:-1]  # jackets -> jacket
        words.add(w)
    return words


def _garment_type_words(garment_type: str) -> set[str]:
    words = _garment_words(garment_type)
    if "tshirt" in words:
        words.discard("crewneck")  # a "crew-neck t-shirt" is a tee, not a crewneck sweatshirt
    elif "hoodie" in words or "crewneck" in words:
        words.add("sweatshirt")  # shoppers call both of these sweatshirts
    return words


def _preview(query: str, offset: int = 0, limit: int = MAX_PREVIEW_CARDS) -> ProductPreviewResult:
    """Match the query to garment types and return one page of products (the tool always gets page 1)."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT c.product_id, c.name, c.price, c.description, c.image_file_path, c.garment_type, "
            "COALESCE(SUM(i.quantity), 0) AS total_stock "
            "FROM catalogue c LEFT JOIN inventory i ON i.product_id = c.product_id GROUP BY c.product_id"
        ).fetchall()

    types = {r["garment_type"]: _garment_type_words(r["garment_type"]) for r in rows}
    vocabulary = set().union(*types.values())
    asked = _garment_words(query)
    if "shirt" in asked:
        asked.add("tshirt")  # "shirts" should include T-shirts
    garment_terms = asked & vocabulary
    scores = {gt: len(garment_terms & words) for gt, words in types.items()} if garment_terms else {}
    best = max(scores.values(), default=0)
    if best == 0:
        return ProductPreviewResult(status="no_match", query=query, message=PREVIEW_NOT_FOUND_REPLY)

    matched_types = sorted(gt for gt, sc in scores.items() if sc == best)
    matches = [r for r in rows if r["garment_type"] in matched_types]
    # Within the matched types, rank by the shopper's other words (color, college, sport...),
    # then in-stock items first, then name.
    extra = set(_tokens(query)) - vocabulary - {"tshirt", "shirt", "hoodie"}

    def rank(r):
        text = f"{r['name']} {r['description']}".lower()
        return (-sum(t in text for t in extra), r["total_stock"] == 0, r["name"])

    matches.sort(key=rank)
    detail_matches = sum(rank(r)[0] < 0 for r in matches) if extra else None
    shown = min(len(matches), MAX_PREVIEW_CARDS)
    page = matches[offset:offset + limit]
    message = (
        f"These {shown} cards are now shown on the website (out of {len(matches)} products of this type). "
        "Don't list them all again in your reply."
    )
    if extra:
        message += (
            f" Only {detail_matches} of the {len(matches)} mention {', '.join(sorted(extra))}; they are shown first. "
            "Don't claim more match those words than that."
        )
    return ProductPreviewResult(
        status="match",
        query=query,
        garment_types=matched_types,
        total_matches=len(matches),
        offset=offset,
        products=[
            PreviewProduct(
                product_id=r["product_id"],
                name=r["name"],
                price=r["price"],
                description=r["description"],
                image_url=image_url(r["image_file_path"]),
                url=f"/products/{r['product_id']}",
                garment_type=r["garment_type"],
                total_stock=r["total_stock"],
            )
            for r in page
        ],
        detail_matches=detail_matches,
        message=message,
    )


async def product_preview(query: str) -> ProductPreviewResult:
    """Product Preview: show product cards on the website for a TYPE of product, e.g. "what hoodies do you have?".

    Matches the inquiry to catalogue.garment_type and returns at most 6 products (image, name, price,
    description). The website renders them as product cards on the page; each card opens the product page.

    Args:
        query: The shopper's words about the type of product, e.g. "navy hoodies", "t-shirts", "quarter zips".
    """
    try:
        return await asyncio.wait_for(asyncio.to_thread(_preview, query), TOOL_TIMEOUT_SECONDS)
    except TimeoutError:
        return ProductPreviewResult(
            status="timeout",
            query=query,
            message=f"The catalogue search took longer than {TOOL_TIMEOUT_SECONDS} seconds and was stopped.",
        )


# --- Page context tools ---

def identify_page_product(product_name: str | None = None, image_file_path: str | None = None) -> PageProductResult:
    """Identify the catalogue product on the shopper's current page from its name and/or image_file_path.

    Use when the shopper says "this", "it", or "this one" while on a product page (the page details are in
    the [Page context] note). Then use the product_id with information_output for stock questions, or with
    find_similar_products for "do you have this in pink?" style questions.

    Args:
        product_name: The product name shown on the page.
        image_file_path: The product image path on the page, e.g. "products/basic-hoodie-big-yale.jpg".
    """
    with get_db() as conn:
        row, matched_on = None, None
        if image_file_path:
            path = strip_image_url(image_file_path)
            row = conn.execute("SELECT * FROM catalogue WHERE image_file_path = ?", (path,)).fetchone()
            matched_on = "image_file_path" if row else None
        if row is None and product_name:
            row = conn.execute(
                "SELECT * FROM catalogue WHERE lower(name) = lower(?)", (product_name.strip(),)
            ).fetchone()
            matched_on = "name" if row else None
    if row is None:
        return PageProductResult(
            status="not_found", message="No catalogue product matches this page. Ask the shopper which item they mean."
        )
    return PageProductResult(
        status="found",
        product_id=row["product_id"],
        name=row["name"],
        garment_type=row["garment_type"],
        colors=json.loads(row["colors"]),
        price=row["price"],
        url=f"/products/{row['product_id']}",
        matched_on=matched_on,
        message="This is the product on the shopper's page; treat it as the item they mean.",
    )


def find_similar_products(product_id: str, color: str | None = None) -> SimilarProductsResult:
    """Find catalogue products similar to a given product (same kind of garment, shared themes), optionally in a color.

    Use for questions like "do you have this in pink?" or "anything like this?". Reports whether the product
    itself comes in that color, and up to 6 similar products, closest first (in that color when possible).

    Args:
        product_id: The product to compare against, e.g. from identify_page_product.
        color: Optional color the shopper wants, e.g. "pink", "gray", "navy".
    """
    products = all_products()
    base = next((p for p in products if p["product_id"] == product_id), None)
    if base is None:
        return SimilarProductsResult(product_id=product_id, color=color, message="Unknown product_id.")

    wanted = color.strip().lower().replace("grey", "gray") if color else None
    has_color = lambda p: bool(wanted) and any(wanted in c.lower() for c in p["colors"])  # noqa: E731
    base_tags = {t.lower() for t in base["search_tags"]}

    def closeness(p: dict) -> tuple:
        return (
            p["category"] != base["category"],  # same kind of garment first
            -len(set(p["collections"]) & set(base["collections"])),  # shared theme (college, sport, family)
            -len(base_tags & {t.lower() for t in p["search_tags"]}),
            p["total_stock"] == 0,
            p["name"],
        )

    others = [p for p in products if p["product_id"] != product_id]
    in_color = [p for p in others if has_color(p)] if wanted else []
    pool = in_color if in_color else others
    pool.sort(key=closeness)
    if wanted and not in_color:
        message = f"Nothing in the catalogue comes in {color}. These are the closest similar items in other colors."
    elif wanted:
        message = f"These similar items come in {color}, closest first."
    else:
        message = "These are the most similar items, closest first."
    return SimilarProductsResult(
        product_id=product_id,
        color=color,
        exact_color_available=has_color(base),
        products=[
            SimilarProduct(
                product_id=p["product_id"], name=p["name"], garment_type=p["garment_type"], colors=p["colors"],
                price=p["price"], url=f"/products/{p['product_id']}", total_stock=p["total_stock"],
            )
            for p in pool[:MAX_PREVIEW_CARDS]
        ],
        message=message,
    )


# --- Tool: General Inquiry ---

GENERAL_INQUIRY_TIMEOUT_SECONDS = 12  # stop quickly so a broad question never burns time or tokens

ORDER_WORDS = {
    "order", "orders", "ordered", "shipping", "ship", "shipped", "delivery", "deliver", "track", "tracking",
    "return", "returns", "refund", "exchange", "purchase", "purchased", "bought", "checkout", "pay", "payment",
}
# Shopper color words -> words used in catalogue.colors.
COLOR_SYNONYMS = {"grey": "gray", "silver": "gray", "charcoal": "gray", "maroon": "red", "crimson": "red",
                  "golden": "gold", "offwhite": "cream", "beige": "cream", "tan": "cream"}
EXTRA_COLOR_WORDS = {"pink", "purple", "orange", "brown", "teal", "maroon", "crimson", "silver", "beige", "tan"}
BUDGET = re.compile(r"(?:under|below|less than|cheaper than|max(?:imum)?|up to|within|budget(?: of| is)?)\s*\$?\s*(\d+(?:\.\d+)?)"
                    r"|\$\s*(\d+(?:\.\d+)?)", re.IGNORECASE)
GIFT_WORDS = {"gift", "present", "birthday", "graduation", "christmas", "holiday"}
# Question words that say nothing about which products to show.
INQUIRY_FILLER = {
    "where", "when", "how", "why", "who", "whats", "stuff", "gear", "items", "item", "things", "thing", "products",
    "product", "under", "below", "less", "than", "cheaper", "budget", "max", "within", "cost", "price", "much",
    "color", "colors", "colour", "come", "comes", "sell", "carry", "got", "more", "else", "anything", "everything",
    "options", "recommend", "recommendation", "suggest", "ideas", "idea", "good", "nice", "cool", "student",
    "someone", "somebody", "person", "buy", "shop", "store", "online", "tshirt", "shirt", "hoodie", "dollar", "dollars",
}


def _catalogue_color_words(products: list[dict]) -> set[str]:
    words: set[str] = set()
    for p in products:
        for color in p["colors"]:
            words.update(re.findall(r"[a-z]+", color.lower()))
    return words - {"heather", "dark", "light", "dusty", "royal"}  # shades, not colors on their own


def _understand(question: str, products: list[dict]) -> dict:
    """Work out what the shopper is asking about: an order, colors, product types, themes, budget, size."""
    q = question.lower()
    words = set(re.findall(r"[a-z0-9]+", q))
    catalogue_colors = _catalogue_color_words(products)
    colors_asked = {COLOR_SYNONYMS.get(w, w) for w in words if w in catalogue_colors | EXTRA_COLOR_WORDS | set(COLOR_SYNONYMS)}
    garment_vocab = set().union(*(_garment_type_words(p["garment_type"]) for p in products))
    asked_garment = _garment_words(question)
    if "shirt" in asked_garment:
        asked_garment.add("tshirt")
    garment_terms = asked_garment & garment_vocab
    budget = BUDGET.search(question)
    size = next((SIZES[w] for w in words if w in SIZES and w not in {"m", "s", "l"}), None)
    if size is None:
        size = next((t.upper() for t in re.findall(r"\b(xs|xxl|xl|s|m|l)\b", question) if t.upper() in SIZE_ORDER), None)
    # Everything else (college, sport, family, vintage, school...) is matched against search_tags, name, description.
    # Garment phrases are folded first ("quarter zip" -> quarterzip) so their words aren't counted twice.
    folded = q
    for pattern, repl in GARMENT_PHRASES:
        folded = re.sub(pattern, repl, folded)
    theme_terms = [
        SYNONYMS.get(t, t) for t in _tokens(folded)
        if t not in garment_vocab and COLOR_SYNONYMS.get(t, t) not in colors_asked and t not in ORDER_WORDS
        and t not in GIFT_WORDS and t not in SIZES and t not in INQUIRY_FILLER and not t.isdigit()
        and GARMENT_SYNONYMS.get(t, t) not in garment_vocab
    ]
    intents = []
    if words & ORDER_WORDS:
        intents.append("order")
    if colors_asked:
        intents.append("color")
    if garment_terms:
        intents.append("product_type")
    if theme_terms:
        intents.append("theme")
    if budget:
        intents.append("budget")
    if size:
        intents.append("size")
    if words & GIFT_WORDS:
        intents.append("gift")
    return {
        "intents": intents or ["general"],
        "colors": sorted(colors_asked),
        "unavailable_colors": sorted(c for c in colors_asked if c not in catalogue_colors),
        "garment_terms": sorted(garment_terms),
        "theme_terms": theme_terms,
        "max_price": float(budget.group(1) or budget.group(2)) if budget else None,
        "size": size,
    }


def _general_inquiry(question: str) -> GeneralInquiryResult:
    products = all_products()
    u = _understand(question, products)
    understood = InquiryUnderstanding(**{k: v for k, v in u.items() if k != "unavailable_colors"})

    if "order" in u["intents"] and not (u["colors"] or u["garment_terms"] or u["theme_terms"]):
        return GeneralInquiryResult(
            understood=understood,
            message="This is about an order. Campus Customs has no online ordering or checkout yet, so there are no "
            "orders to look up. Shoppers can save items in their cart and visit the store at 57 Broadway.",
        )

    def matches(p: dict) -> bool:
        if u["colors"]:
            colors = " ".join(p["colors"]).lower()
            if not any(c in colors for c in u["colors"]):
                return False
        if u["garment_terms"] and not set(u["garment_terms"]) & _garment_type_words(p["garment_type"]):
            return False
        if u["max_price"] is not None and p["price"] > u["max_price"]:
            return False
        if u["size"] and not any(s["size"] == u["size"] and s["quantity"] > 0 for s in p["inventory"]):
            return False
        return True

    def relevance(p: dict) -> int:
        # Theme words: search_tags and collections count most, then name, then description.
        tags = " ".join(p["search_tags"] + p["collections"]).lower()
        name, desc = p["name"].lower(), p["description"].lower()
        return sum(3 if t in tags else 2 if t in name else 1 if t in desc else 0 for t in u["theme_terms"])

    pool = [p for p in products if matches(p)]
    if u["theme_terms"]:
        themed = [p for p in pool if relevance(p) > 0]
        pool = themed if themed else pool
    pool.sort(key=lambda p: (-relevance(p), p["total_stock"] == 0, p["name"]))

    notes = []
    if u["unavailable_colors"]:
        notes.append(f"Nothing in the catalogue comes in {', '.join(u['unavailable_colors'])}.")
    if not pool:
        notes.append("No products match all of that. Suggest loosening one detail (color, type, budget, or size).")
    else:
        notes.append(f"{len(pool)} products match; the best {min(len(pool), MAX_PREVIEW_CARDS)} are listed. "
                     "Put their product_ids in product_ids to show them as cards.")
    return GeneralInquiryResult(
        status="match" if pool else "no_match",
        understood=understood,
        total_matches=len(pool),
        products=[
            InquiryProduct(
                product_id=p["product_id"], name=p["name"], garment_type=p["garment_type"], colors=p["colors"],
                price=p["price"], url=f"/products/{p['product_id']}", total_stock=p["total_stock"],
                size_stock=next((s["quantity"] for s in p["inventory"] if s["size"] == u["size"]), None) if u["size"] else None,
            )
            for p in pool[:MAX_PREVIEW_CARDS]
        ],
        message=" ".join(notes),
    )


async def general_inquiry(question: str) -> GeneralInquiryResult:
    """General Inquiry: answer broad questions that are NOT about one specific product.

    First works out what the shopper is asking about (an order, a color, a product type, a theme such as a
    residential college, sport, or family, a budget, a size, or a gift), then searches the catalogue:
    colors via catalogue.colors, product types via garment_type, themes via search_tags (and name/description).
    Returns up to 6 best matches. Stops after 12 seconds.

    Args:
        question: The shopper's question in their own words, e.g. "do you have anything in green?".
    """
    try:
        return await asyncio.wait_for(
            asyncio.to_thread(_general_inquiry, question), GENERAL_INQUIRY_TIMEOUT_SECONDS
        )
    except TimeoutError:
        return GeneralInquiryResult(
            status="timeout",
            understood=InquiryUnderstanding(intents=["general"]),
            message=f"The search took longer than {GENERAL_INQUIRY_TIMEOUT_SECONDS} seconds and was stopped.",
        )


# --- Tool: Save Chat History (logged-in shoppers only; run by the server, not the model) ---

def save_chat_history(
    user_id: int, role: str, content: str, products_json: str | None = None
) -> SavedChatMessage:
    """Save Chat History: write one chat message to chat_messages for a logged-in shopper.

    Called by the /api/chat route for every user message and every assistant reply, and only when the
    request carries a valid login session. chat_messages.id is assigned by the database (unique per
    message) and created_at is timestamped by the database.
    """
    with get_db(writable=True) as conn:
        cur = conn.execute(
            "INSERT INTO chat_messages (user_id, role, content, products_json) VALUES (?, ?, ?, ?)",
            (user_id, role, content, products_json),
        )
        row = conn.execute("SELECT * FROM chat_messages WHERE id = ?", (cur.lastrowid,)).fetchone()
    return SavedChatMessage(**dict(row))


def load_chat_history(user_id: int, limit: int) -> list[HistoryMessage]:
    """The shopper's most recent chat_messages rows (content only), oldest first."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT role, content, created_at FROM chat_messages WHERE user_id = ? ORDER BY id DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
    return [HistoryMessage(**dict(r)) for r in reversed(rows)]


def get_customer(user_id: int) -> CustomerInfo | None:
    """The logged-in shopper's id, name, and email from the users table (never the password hash)."""
    with get_db() as conn:
        row = conn.execute("SELECT id, name, email FROM users WHERE id = ?", (user_id,)).fetchone()
    return CustomerInfo(**dict(row)) if row else None


# ============================================================================
# Accounts: password hashing and login sessions (server-only; not an agent tool)
# ============================================================================
# Password hashing and login sessions for Campus Customs.
#
# Stored format (matches the seed database): pbkdf2_sha256$<salt>$<hex digest>
# - PBKDF2-HMAC-SHA256, 120,000 iterations, salt string encoded as UTF-8.
# - Signup and login both go through hash_password(), so the settings can never drift apart.

ALGORITHM = "pbkdf2_sha256"
ITERATIONS = 120_000
SALT_BYTES = 8  # 8 random bytes -> 16 hex characters, same shape as the seed users' salts
SESSION_TTL_SECONDS = 7 * 24 * 60 * 60


def hash_password(password: str, salt: str) -> str:
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), ITERATIONS)
    return f"{ALGORITHM}${salt}${digest.hex()}"


def make_password_hash(password: str) -> str:
    """Signup: a fresh random salt per user, stored inside the hash string."""
    return hash_password(password, secrets.token_hex(SALT_BYTES))


def verify_password(password: str, stored: str) -> bool:
    """Login: never un-hash. Read the salt from the stored string, re-hash what was typed, compare."""
    try:
        algorithm, salt, _ = stored.split("$")
    except ValueError:
        return False
    if algorithm != ALGORITHM:
        return False
    return hmac.compare_digest(hash_password(password, salt), stored)


# Used when an email isn't registered, so a login attempt costs the same either way
# and response time doesn't reveal which emails have accounts.
DUMMY_HASH = make_password_hash(secrets.token_hex(16))


# --- Sessions: a signed token "payload.signature" carrying the user id and expiry ---

def _load_secret() -> bytes:
    if env := os.environ.get("CC_SESSION_SECRET"):
        return env.encode()
    path = Path(__file__).resolve().parent / ".session_secret"
    if not path.exists():
        path.write_text(secrets.token_hex(32))
    return path.read_text().strip().encode()


SECRET = _load_secret()


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _sign(payload: str) -> str:
    return _b64(hmac.new(SECRET, payload.encode(), hashlib.sha256).digest())


def password_fingerprint(password_hash: str) -> str:
    """A short fingerprint of the stored hash. Sessions carry it, so changing the password ends old sessions."""
    return hashlib.sha256(password_hash.encode()).hexdigest()[:16]


def create_session_token(user_id: int, password_hash: str) -> str:
    claims = {"uid": user_id, "pv": password_fingerprint(password_hash), "exp": int(time.time()) + SESSION_TTL_SECONDS}
    payload = _b64(json.dumps(claims).encode())
    return f"{payload}.{_sign(payload)}"


def session_is_current(claims: dict, password_hash: str) -> bool:
    """False if the password changed (e.g. after a reset) since this session was created."""
    return hmac.compare_digest(str(claims.get("pv", "")), password_fingerprint(password_hash))


def read_session_token(token: str) -> dict | None:
    """Return the claims ({"uid", "pv", "exp"}) of a valid, unexpired token, else None."""
    try:
        payload, signature = token.split(".")
    except ValueError:
        return None
    if not hmac.compare_digest(_sign(payload), signature):
        return None
    try:
        data = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
    except ValueError:
        return None
    if data.get("exp", 0) < time.time() or "uid" not in data:
        return None
    return data


# ============================================================================
# Email for password-reset links (server-only)
# ============================================================================
# Outgoing email (used for password reset links).
#
# - If SMTP_HOST is set in .env, mail is sent through that server (SMTP_PORT, SMTP_USER, SMTP_PASSWORD,
#   SMTP_FROM; STARTTLS on port 587).
# - Otherwise (development), each email is saved as a text file in backend/outbox/ instead of being sent,
#   so the reset flow can be tested without an email service. Open the newest file to find the link.

OUTBOX = Path(__file__).resolve().parent / "outbox"
mail_log = logging.getLogger("campus_customs")


def send_email(to: str, subject: str, body: str) -> None:
    sender = os.getenv("SMTP_FROM", "Campus Customs <no-reply@campuscustoms.example>")
    host = os.getenv("SMTP_HOST")
    if host:
        msg = EmailMessage()
        msg["From"], msg["To"], msg["Subject"] = sender, to, subject
        msg.set_content(body)
        with smtplib.SMTP(host, int(os.getenv("SMTP_PORT", "587")), timeout=15) as smtp:
            smtp.starttls()
            if user := os.getenv("SMTP_USER"):
                smtp.login(user, os.getenv("SMTP_PASSWORD", ""))
            smtp.send_message(msg)
        return

    OUTBOX.mkdir(exist_ok=True)
    safe_to = re.sub(r"[^a-z0-9]+", "-", to.lower()).strip("-")
    path = OUTBOX / f"{time.strftime('%Y%m%d-%H%M%S')}-{time.time_ns() % 1_000_000:06d}-{safe_to}.txt"  # unique per email
    path.write_text(f"From: {sender}\nTo: {to}\nSubject: {subject}\n\n{body}\n", encoding="utf-8")
    mail_log.warning("No SMTP server configured; email to %s saved to %s", to, path)


# ============================================================================
# Self-service password reset (server-only)
# ============================================================================
# Self-service password reset.
#
# 1. The shopper enters their email on "Forgot your password?". If it belongs to an account, a one-time
#    reset link is emailed to that address (send_email below). The response is the same either way, so the
#    page never reveals which emails have accounts.
# 2. The link holds a random token. Only a SHA-256 hash of it is stored (password_resets table), it
#    expires after 30 minutes, and it works once.
# 3. On the reset page the shopper chooses a new password (same rules as signup). It is hashed exactly
#    like signup (auth.make_password_hash: PBKDF2-HMAC-SHA256, 120,000 iterations, new random salt),
#    all of the account's reset links are cancelled, and every old login session ends.

RESET_TTL_SECONDS = 30 * 60
MAX_REQUESTS_PER_HOUR = 3
SITE_URL = os.getenv("SITE_URL", "http://localhost:5175")


def ensure_password_reset_table() -> None:
    with get_db(writable=True) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS password_resets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token_hash TEXT NOT NULL UNIQUE,
                expires_at INTEGER NOT NULL,
                used_at TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            """
        )


def _reset_token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def request_reset(email: str) -> None:
    """Email a reset link if the address has an account. Silently does nothing otherwise."""
    email = email.strip().lower()
    with get_db(writable=True) as conn:
        user = conn.execute("SELECT id, first_name, name, email FROM users WHERE lower(email) = ?", (email,)).fetchone()
        if user is None:
            return
        recent = conn.execute(
            "SELECT count(*) FROM password_resets WHERE user_id = ? AND created_at >= datetime('now', '-1 hour')",
            (user["id"],),
        ).fetchone()[0]
        if recent >= MAX_REQUESTS_PER_HOUR:  # stop someone flooding a customer's inbox
            return
        token = secrets.token_urlsafe(32)
        conn.execute(
            "INSERT INTO password_resets (user_id, token_hash, expires_at) VALUES (?, ?, ?)",
            (user["id"], _reset_token_hash(token), int(time.time()) + RESET_TTL_SECONDS),
        )
    link = f"{SITE_URL}/reset-password?token={token}"
    send_email(
        user["email"],
        "Reset your Campus Customs password",
        f"Hi {user['first_name'] or user['name']},\n\n"
        "We received a request to reset the password for your Campus Customs account.\n"
        f"Choose a new password here (this link works once and expires in {RESET_TTL_SECONDS // 60} minutes):\n\n"
        f"{link}\n\n"
        "If you didn't ask for this, you can ignore this email; your password won't change.\n\n"
        "Boola Boola!\nCampus Customs, 57 Broadway, New Haven",
    )


def _valid_reset(conn: sqlite3.Connection, token: str) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT * FROM password_resets WHERE token_hash = ? AND used_at IS NULL AND expires_at > ?",
        (_reset_token_hash(token), int(time.time())),
    ).fetchone()


def token_is_valid(token: str) -> bool:
    with get_db() as conn:
        return _valid_reset(conn, token) is not None


def complete_reset(token: str, new_password: str) -> sqlite3.Row | None:
    """Set the new password if the token is valid. Returns the updated user row, or None."""
    with get_db(writable=True) as conn:
        reset = _valid_reset(conn, token)
        if reset is None:
            return None
        conn.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (make_password_hash(new_password), reset["user_id"]),
        )
        # This link and any other outstanding links for the account stop working.
        conn.execute(
            "UPDATE password_resets SET used_at = datetime('now') WHERE user_id = ? AND used_at IS NULL",
            (reset["user_id"],),
        )
        return conn.execute("SELECT * FROM users WHERE id = ?", (reset["user_id"],)).fetchone()


# ============================================================================
# Chat privacy: never store or forward a password typed into the chat (server-only)
# ============================================================================
# Keep passwords out of the chat: never stored in chat_messages, never sent to the model.
#
# Two checks run on every chat message before it is saved or given to the agent:
# 1. Phrases that introduce a password ("my password is X", "password: X", "reset my password to X")
#    -> X is removed. Works for guests and logged-in shoppers.
# 2. Logged-in shoppers only: each longer word in the message is checked against their stored
#    password hash (the same PBKDF2 check as login). A match means they typed their real password,
#    even with no lead-in phrase, so it is removed. The password itself is never stored or logged.

REDACTED = "[password removed]"
MIN_CANDIDATE_LEN = 6
MAX_HASH_CHECKS = 20  # ~55 ms each, so at most about a second per message

# "password is X", "pwd: X", "passcode = X", "password to X", "password should be X", ...
LEAD_IN = re.compile(
    r"\b(?:pass\s?(?:word|code|phrase)|pwd|pw)s?\b\s*(?:is|was|=|:|-|to|should be|will be|would be)\s*"
    r"[\"'“‘]?(?P<secret>[^\s\"'”’]+)",
    re.IGNORECASE,
)
# Words that follow "password to/is" in normal sentences, not real passwords.
NOT_SECRETS = {
    "something", "anything", "what", "the", "a", "an", "my", "it", "be", "reset", "change", "new",
    "forgotten", "forgot", "wrong", "incorrect", "correct", "right", "safe", "secure", "stronger", "longer",
    "shown", "visible", "saved", "stored", "reset?", "work", "working", "not",
}


PUNCTUATION = ".,!?;:()[]{}<>\"'“”‘’"


def _word_spans(text: str) -> list[tuple[int, int]]:
    """(start, end) of each whitespace-separated word, with surrounding punctuation trimmed off."""
    spans = []
    for m in re.finditer(r"\S+", text):
        start, end = m.start(), m.end()
        while start < end and text[start] in PUNCTUATION:
            start += 1
        while end > start and text[end - 1] in PUNCTUATION:
            end -= 1
        if end > start:
            spans.append((start, end))
    return spans


def find_secret_spans(text: str, password_hash: str | None = None) -> list[tuple[int, int]]:
    """Character positions in the text that hold a password."""
    spans: set[tuple[int, int]] = set()
    for m in LEAD_IN.finditer(text):
        start, end = m.span("secret")
        while end > start and text[end - 1] in PUNCTUATION:
            end -= 1
        if end > start and text[start:end].lower() not in NOT_SECRETS:
            spans.add((start, end))
    if password_hash:
        by_word: dict[str, list[tuple[int, int]]] = {}
        for start, end in _word_spans(text):
            if end - start >= MIN_CANDIDATE_LEN:
                by_word.setdefault(text[start:end], []).append((start, end))
        # Words with digits or symbols look most like passwords, so check those first.
        for word in sorted(by_word, key=str.isalpha)[:MAX_HASH_CHECKS]:
            if verify_password(word, password_hash):
                spans.update(by_word[word])  # every place they typed it
    return sorted(spans)


def clean_message(text: str, password_hash: str | None = None) -> tuple[str, bool]:
    """Return the message with any passwords replaced by "[password removed]", and whether anything was removed."""
    spans = find_secret_spans(text, password_hash)
    if not spans:
        return text, False
    out, last = [], 0
    for start, end in spans:
        if start < last:  # overlapping match, already removed
            continue
        out += [text[last:start], REDACTED]
        last = end
    out.append(text[last:])
    return "".join(out), True


# ============================================================================
# Account carts (server-only)
# ============================================================================
# Account carts: a logged-in shopper's cart is stored in the cart_items table, so it follows them
# across devices and sessions. Guests keep their cart in the browser only.
#
# Quantities are always limited to live inventory, and there is no checkout.

def ensure_cart_table() -> None:
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


# Tools the model can call. Save Chat History, load_chat_history, and get_customer are deliberately
# not here: the server runs them for the logged-in shopper, so the model can't touch other customers' data.
TOOLS = [
    product_confirmation,
    information_output,
    product_preview,
    identify_page_product,
    find_similar_products,
    general_inquiry,
    catalogue_overview,
]
