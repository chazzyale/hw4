export type SizeStock = { size: string; quantity: number }

// localStorage key for the login session token (set by auth.tsx).
export const TOKEN_KEY = 'cc_session'

export type Product = {
  product_id: string
  name: string
  garment_type: string
  category: Category
  collections: Collection[]
  description: string
  colors: string[]
  search_tags: string[]
  image_url: string
  price: number
  inventory: SizeStock[]
  total_stock: number
}

export type Category = 'hoodies' | 'crewnecks' | 'quarter-zips' | 't-shirts' | 'outerwear' | 'hats' | 'other'

// Order here is the order of the filter chips on the Products page.
export const CATEGORY_LABELS: Record<Category, string> = {
  hoodies: 'Hoodies',
  crewnecks: 'Crewnecks',
  'quarter-zips': 'Quarter-zips',
  't-shirts': 'T-Shirts',
  outerwear: 'Outerwear',
  hats: 'Hats',
  other: 'Other',
}

export type Collection = 'residential-colleges' | 'athletics' | 'family'

export const COLLECTION_LABELS: Record<Collection, string> = {
  'residential-colleges': 'Residential colleges',
  athletics: 'Yale Athletics',
  family: 'Yale family',
}

async function getJson<T>(url: string): Promise<T> {
  const res = await fetch(url)
  if (!res.ok) throw new Error(res.status === 404 ? 'Not found' : `Request failed (${res.status})`)
  return res.json() as Promise<T>
}

export function fetchProducts(): Promise<Product[]> {
  return getJson<Product[]>('/api/products')
}

export function fetchProduct(productId: string): Promise<Product> {
  return getJson<Product>(`/api/products/${encodeURIComponent(productId)}`)
}

export const formatPrice = (price: number) =>
  price.toLocaleString('en-US', { style: 'currency', currency: 'USD' })

// --- Shop chatbot (types mirror backend/models.py) ---

export type ChatTurn = { role: 'user' | 'assistant'; content: string }

export type ChatProductCard = {
  product_id: string
  name: string
  price: number
  image_url: string
  url: string
  category: Category
  total_stock: number
  inventory: SizeStock[]
}

export type ChatStep =
  | 'confirm_product'
  | 'ask_more_details'
  | 'ask_specific_size'
  | 'choose_size'
  | 'information_output'
  | 'timeout'
  | 'product_preview'
  | 'none'

// Product-flow memory: sent back unchanged with the next message (see backend/models.py ChatState).
export type ChatState = {
  step: ChatStep
  product_id: string | null
  product_name: string | null
  confirmed: boolean
  size: string | null
  rejected_product_ids: string[]
}

export const INITIAL_CHAT_STATE: ChatState = {
  step: 'none',
  product_id: null,
  product_name: null,
  confirmed: false,
  size: null,
  rejected_product_ids: [],
}

// Product Preview: cards the chat puts on the page (see backend/models.py ProductPreviewResult).
export type PreviewProduct = {
  product_id: string
  name: string
  price: number
  description: string
  image_url: string
  url: string
  garment_type: string
  total_stock: number
}

export type ProductPreview = {
  status: 'match' | 'no_match' | 'timeout'
  query: string
  garment_types: string[]
  total_matches: number
  offset: number
  products: PreviewProduct[] // at most 6
  message: string
}

export type ChatResponse = {
  reply: string
  products: ChatProductCard[]
  choices: string[] // Yes/No or size buttons to show under the reply
  state: ChatState
  preview: ProductPreview | null
  user_message: string | null // set when a password was removed from what the shopper typed
}

// What the shopper is looking at (see backend/models.py PageContext).
export type ChatPage = { path: string; product_name: string | null; image_file_path: string | null }

export async function sendChat(
  message: string,
  history: ChatTurn[],
  state: ChatState,
  page: ChatPage,
): Promise<ChatResponse> {
  // Logged-in shoppers send their session token so the conversation is saved to their account.
  const token = localStorage.getItem(TOKEN_KEY)
  const res = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) },
    body: JSON.stringify({ message, history, state, page }),
  })
  const data = await res.json().catch(() => ({}))
  if (!res.ok) {
    throw new Error(typeof data.detail === 'string' ? data.detail : "Sorry, I couldn't reach the shop assistant.")
  }
  return data as ChatResponse
}

// Logged-in shoppers: welcome-back greeting plus their 4 most recent saved messages (oldest first).
export type ChatHistory = {
  greeting: string
  messages: { role: 'user' | 'assistant'; content: string; created_at: string }[]
}

export async function fetchChatHistory(): Promise<ChatHistory> {
  const token = localStorage.getItem(TOKEN_KEY)
  const res = await fetch('/api/chat/history', { headers: token ? { Authorization: `Bearer ${token}` } : {} })
  if (!res.ok) throw new Error('Could not load chat history')
  return res.json() as Promise<ChatHistory>
}

// --- Account cart (logged-in shoppers; see backend/cart.py) ---

export type SavedCartItem = {
  product_id: string
  name: string
  size: string
  price: number
  image_url: string
  quantity: number
  max: number
}
export type SavedCart = { items: SavedCartItem[]; adjusted: string[] }

function authHeaders(): Record<string, string> {
  const token = localStorage.getItem(TOKEN_KEY)
  return token ? { Authorization: `Bearer ${token}` } : {}
}

export async function fetchSavedCart(): Promise<SavedCart> {
  const res = await fetch('/api/cart', { headers: authHeaders() })
  if (!res.ok) throw new Error('Could not load your saved cart')
  return res.json() as Promise<SavedCart>
}

export async function saveCart(items: { product_id: string; size: string; quantity: number }[]): Promise<SavedCart> {
  const res = await fetch('/api/cart', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify({ items }),
  })
  if (!res.ok) throw new Error('Could not save your cart')
  return res.json() as Promise<SavedCart>
}

// "Show More" on Product Preview results: the next 6 for the same search (database only, no AI call).
export async function fetchPreviewPage(query: string, offset: number): Promise<ProductPreview> {
  const res = await fetch('/api/product-preview', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, offset }),
  })
  if (!res.ok) throw new Error('Could not load more products')
  return res.json() as Promise<ProductPreview>
}
