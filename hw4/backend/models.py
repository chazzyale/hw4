"""Pydantic / PydanticAI structured types for the shop chatbot.

- ChatRequest / ChatTurn / ChatState: what the website sends to POST /api/chat.
- AgentReply / ChatStep: the agent's structured output (PydanticAI output_type).
- ProductConfirmationResult / ProductMatch: return type of the "Product Confirmation" tool.
- InformationOutputResult / SizeQuantity: return type of the "Information Output" tool.
- ProductPreviewResult / PreviewProduct: return type of the "Product Preview" tool (cards shown on the page).
- ProductCard / SizeStock: product data shown as cards under a chat reply, built from the database.
- ChatResponse: what POST /api/chat returns to the website, including the Yes/No or size buttons.
"""

from typing import Literal

from pydantic import BaseModel, Field

MAX_MESSAGE_CHARS = 1000
SIZE_OPTIONS = ["XS", "S", "M", "L", "XL", "XXL"]

# Where the product inquiry flow is after the agent's reply:
# - confirm_product: asked 'Is this the item you're inquiring about?' (Yes/No)
# - ask_more_details: the shopper said No; asked them to describe the item more
# - ask_specific_size: asked whether they mean a specific size (Yes/No)
# - choose_size: asked them to pick one size (XS, S, M, L, XL, XXL)
# - information_output: gave the price and stock from the Information Output tool
# - timeout: a database lookup took longer than 30 seconds (shopper can try again)
# - product_preview: showed product cards on the page for a type of product ("what hoodies do you have?")
# - none: general chat or recommendations, not in the product flow
ChatStep = Literal[
    "confirm_product",
    "ask_more_details",
    "ask_specific_size",
    "choose_size",
    "information_output",
    "timeout",
    "product_preview",
    "none",
]

MAX_PREVIEW_CARDS = 6  # Product Preview shows at most 6 cards per request (token efficiency)
PREVIEW_NOT_FOUND_REPLY = "I cannot locate this type of product. Is there another type of product you're looking for?"

# Buttons the website shows for each step. The server sets these, not the model,
# so the choices are always exactly Yes/No or our six sizes.
STEP_CHOICES: dict[str, list[str]] = {
    "confirm_product": ["Yes", "No"],
    "ask_specific_size": ["Yes", "No"],
    "choose_size": SIZE_OPTIONS,
    "timeout": ["Try again"],
}


# --- Requests from the website ---

class ChatTurn(BaseModel):
    """One earlier message in the conversation, sent by the website for context."""

    role: Literal["user", "assistant"]
    content: str = Field(max_length=4000)


class ChatState(BaseModel):
    """Product-flow memory that round-trips between the website and the server each turn."""

    step: ChatStep = "none"
    product_id: str | None = Field(default=None, description="Product being confirmed or already confirmed.")
    product_name: str | None = None
    confirmed: bool = False
    size: str | None = Field(default=None, description="Size the shopper picked, if any.")
    rejected_product_ids: list[str] = Field(
        default_factory=list, description="Products the shopper said No to, so Product Confirmation skips them."
    )


class PageContext(BaseModel):
    """What the shopper is looking at, sent with each chat message."""

    path: str = Field(default="/", max_length=300, description='The page URL path, e.g. "/products/basic-hoodie-big-yale".')
    product_name: str | None = Field(default=None, max_length=200, description="The product name shown on a product page.")
    image_file_path: str | None = Field(
        default=None, max_length=300, description='The product image on the page, e.g. "products/basic-hoodie-big-yale.jpg".'
    )


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=MAX_MESSAGE_CHARS)
    history: list[ChatTurn] = Field(default_factory=list, max_length=40)
    state: ChatState = Field(default_factory=ChatState)
    page: PageContext | None = None


# --- Customer memory (logged-in shoppers only) ---

HISTORY_RELOAD_LIMIT = 4  # most recent messages shown again when a logged-in shopper returns


class CustomerInfo(BaseModel):
    """The logged-in shopper, from the users table. Never includes password_hash."""

    id: int
    name: str
    email: str


class SavedChatMessage(BaseModel):
    """Return type of the Save Chat History tool: the chat_messages row that was written."""

    id: int = Field(description="chat_messages.id, unique for every saved message.")
    user_id: int
    role: Literal["user", "assistant"]
    content: str
    products_json: str | None = None
    created_at: str


class HistoryMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(description="chat_messages.content, shown again in the chat panel.")
    created_at: str


class ChatHistoryResponse(BaseModel):
    """GET /api/chat/history: what the chat panel shows when a logged-in shopper opens it."""

    greeting: str = Field(description='"Welcome back [NAME]! How can I help you?" using users.name.')
    messages: list[HistoryMessage] = Field(
        default_factory=list, description=f"The {HISTORY_RELOAD_LIMIT} most recent messages, oldest first."
    )


# --- Agent output ---

class AgentReply(BaseModel):
    """Structured output the agent must return for every message."""

    reply: str = Field(
        description="The message shown to the shopper, in Markdown. Link products as [Name](/products/<product_id>)."
    )
    step: ChatStep = Field(description="Where the product inquiry flow is after this reply (see the prompt).")
    product_id: str | None = Field(
        default=None,
        description="product_id of the product being confirmed or discussed, from the Product Confirmation tool.",
    )
    product_ids: list[str] = Field(
        default_factory=list,
        description="product_id values (from tool results) to show as product cards, most relevant first, at most 6.",
    )


# --- Tool: Product Confirmation ---

class ProductMatch(BaseModel):
    product_id: str
    name: str
    description: str
    match_score: float = Field(description="0 to 1; higher means the description matched more of the inquiry.")


class ProductConfirmationResult(BaseModel):
    status: Literal["match", "no_match", "timeout"]
    best_match: ProductMatch | None = None
    other_close_matches: list[str] = Field(
        default_factory=list, description="Names of the next-best matches, for asking follow-up questions."
    )
    message: str


# --- Tool: Information Output ---

class SizeQuantity(BaseModel):
    size: str
    quantity: int
    display: str = Field(description='What to show the shopper, e.g. "12", "3 - Low Stock", or "0 - Sold Out".')


class InformationOutputResult(BaseModel):
    status: Literal["found", "not_found", "timeout"]
    product_id: str
    name: str | None = None
    url: str | None = None
    price: float | None = Field(default=None, description="From catalogue.price. None if not found; never guess.")
    size_requested: str | None = None
    sizes: list[SizeQuantity] = Field(
        default_factory=list, description="inventory.quantity for the requested size only, or for every size."
    )
    message: str


# --- Tool: Product Preview ---

class PreviewProduct(BaseModel):
    """One product card rendered on the page: image, name, price, and short info from the catalogue."""

    product_id: str
    name: str
    price: float
    description: str
    image_url: str = Field(description="Built from catalogue.image_file_path, served at /media/...")
    url: str = Field(description="The single-item product page, /products/<product_id>.")
    garment_type: str
    total_stock: int


class ProductPreviewResult(BaseModel):
    status: Literal["match", "no_match", "timeout"]
    query: str
    garment_types: list[str] = Field(
        default_factory=list, description="The catalogue.garment_type values that best matched the inquiry."
    )
    total_matches: int = Field(default=0, description="How many products have those garment types in total.")
    offset: int = Field(default=0, description="Position of the first product in this page (0 for the tool's results).")
    detail_matches: int | None = Field(
        default=None,
        description="How many of those also mention the shopper's other words (e.g. 'navy'); None if there were none.",
    )
    products: list[PreviewProduct] = Field(
        default_factory=list, description=f"At most {MAX_PREVIEW_CARDS} products, best matches first."
    )
    message: str


# --- Tools: page context ---

class PageProductResult(BaseModel):
    """Return type of identify_page_product: which catalogue product is on the shopper's page."""

    status: Literal["found", "not_found"]
    product_id: str | None = None
    name: str | None = None
    garment_type: str | None = None
    colors: list[str] = Field(default_factory=list)
    price: float | None = None
    url: str | None = None
    matched_on: str | None = Field(default=None, description='"image_file_path" or "name".')
    message: str


class SimilarProduct(BaseModel):
    product_id: str
    name: str
    garment_type: str
    colors: list[str]
    price: float
    url: str
    total_stock: int


class SimilarProductsResult(BaseModel):
    """Return type of find_similar_products: catalogue items like the page product (optionally in a color)."""

    product_id: str
    color: str | None = None
    exact_color_available: bool = Field(
        default=False, description="True if the page product itself comes in the requested color."
    )
    products: list[SimilarProduct] = Field(default_factory=list, description="At most 6, closest first.")
    message: str


# --- Tool: General Inquiry ---

InquiryIntent = Literal["order", "color", "product_type", "theme", "budget", "size", "gift", "general"]


class InquiryUnderstanding(BaseModel):
    """What General Inquiry worked out the shopper is asking about."""

    intents: list[InquiryIntent]
    colors: list[str] = Field(default_factory=list, description="Colors asked for, matched against catalogue.colors.")
    garment_terms: list[str] = Field(default_factory=list, description="Product types, matched against garment_type.")
    theme_terms: list[str] = Field(
        default_factory=list, description="Other words (college, sport, family...), matched against search_tags."
    )
    max_price: float | None = None
    size: str | None = None


class InquiryProduct(BaseModel):
    product_id: str
    name: str
    garment_type: str
    colors: list[str]
    price: float
    url: str
    total_stock: int
    size_stock: int | None = Field(default=None, description="Units in the asked-for size, if a size was asked.")


class GeneralInquiryResult(BaseModel):
    status: Literal["match", "no_match", "timeout"] = "no_match"
    understood: InquiryUnderstanding
    total_matches: int = 0
    products: list[InquiryProduct] = Field(default_factory=list, description="At most 6 best matches.")
    message: str


# --- Response to the website ---

class SizeStock(BaseModel):
    size: str
    quantity: int


class ProductCard(BaseModel):
    """A product shown under a chat reply. Price and stock always come from the database, not the model."""

    product_id: str
    name: str
    price: float
    image_url: str
    url: str
    category: str
    total_stock: int
    inventory: list[SizeStock]


class ChatResponse(BaseModel):
    reply: str
    products: list[ProductCard] = Field(default_factory=list)
    choices: list[str] = Field(default_factory=list, description="Buttons to show under the reply (Yes/No or sizes).")
    state: ChatState = Field(default_factory=ChatState)
    preview: ProductPreviewResult | None = Field(
        default=None, description="Product Preview results for the website to render as cards on the page."
    )
    user_message: str | None = Field(
        default=None,
        description='Set only when a password was removed: the shopper\'s message as saved, with "[password removed]".',
    )
