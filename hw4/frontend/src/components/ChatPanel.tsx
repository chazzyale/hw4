import { useEffect, useRef, useState, type FormEvent } from 'react'
import { Link, useLocation } from 'react-router-dom'
import {
  INITIAL_CHAT_STATE,
  fetchChatHistory,
  formatPrice,
  sendChat,
  type ChatProductCard,
  type ChatState,
  type ChatTurn,
  type ProductPreview,
} from '../api'
import ChatMarkdown from './ChatMarkdown'
import { useAuth } from '../auth'
import { usePageProduct } from '../pageContext'

type ChatMessage = ChatTurn & { products?: ChatProductCard[]; choices?: string[]; error?: boolean; saved?: boolean }

const WELCOME: ChatMessage = {
  role: 'assistant',
  content:
    "Hi, I'm the Campus Customs assistant. Boola Boola! Are you asking about a specific product? If so, please describe the item.",
}

const SUGGESTIONS = ['A navy hoodie with big white YALE letters', 'Gift ideas for a Yale dad', 'Show me Saybrook gear']

function ProductMiniCard({ product }: { product: ChatProductCard }) {
  const soldOut = product.total_stock === 0
  const sizesIn = product.inventory.filter(s => s.quantity > 0).map(s => s.size)
  return (
    <Link to={product.url} className="chat-card">
      <img src={product.image_url} alt="" loading="lazy" />
      <span className="chat-card-body">
        <span className="chat-card-name">{product.name}</span>
        <span className="chat-card-meta">
          <strong>{formatPrice(product.price)}</strong>
          <span className={soldOut ? 'chat-card-out' : ''}>
            {soldOut ? 'Sold out' : `Sizes: ${sizesIn.join(', ')}`}
          </span>
        </span>
      </span>
    </Link>
  )
}

export default function ChatPanel({ onPreview }: { onPreview: (preview: ProductPreview | null) => void }) {
  const { user } = useAuth()
  const { pathname, search } = useLocation()
  const { product: pageProduct } = usePageProduct()
  const [open, setOpen] = useState(false)
  // Guests start with the product question; logged-in shoppers wait for their saved history.
  const [messages, setMessages] = useState<ChatMessage[]>(user ? [] : [WELCOME])
  const [draft, setDraft] = useState('')
  const [sending, setSending] = useState(false)
  const [chatState, setChatState] = useState<ChatState>(INITIAL_CHAT_STATE)
  const listRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages, sending, open])

  useEffect(() => {
    if (open) inputRef.current?.focus()
  }, [open])

  // Lets the chat-results panel leave room for the open chat on wide screens.
  useEffect(() => {
    document.body.classList.toggle('chat-open', open)
    return () => document.body.classList.remove('chat-open')
  }, [open])

  // Logged in: reload the 4 most recent saved messages, then "Welcome back [NAME]! How can I help you?"
  // (just the greeting if there's no history). The panel is keyed by user, so this runs once per login.
  useEffect(() => {
    if (!user) return
    let cancelled = false
    fetchChatHistory()
      .then(h => {
        if (cancelled) return
        const saved: ChatMessage[] = h.messages.map(m => ({ role: m.role, content: m.content, saved: true }))
        setMessages([...saved, { role: 'assistant', content: h.greeting }])
      })
      .catch(() => !cancelled && setMessages([WELCOME]))
    return () => {
      cancelled = true
    }
  }, [user])

  async function send(text: string) {
    text = text.trim()
    if (!text || sending) return
    // History for the agent: every turn including the opening question, minus error notices.
    const history: ChatTurn[] = messages
      .filter(m => !m.error)
      .map(({ role, content }) => ({ role, content }))
    setMessages(m => [...m, { role: 'user', content: text }])
    setDraft('')
    setSending(true)
    try {
      const page = {
        path: pathname + search,
        product_name: pageProduct?.name ?? null,
        image_file_path: pageProduct?.image_file_path ?? null,
      }
      const res = await sendChat(text, history, chatState, page)
      setChatState(res.state)
      // Product Preview results go on the page; a "not found" clears any old results.
      if (res.preview) onPreview(res.preview.status === 'match' ? res.preview : null)
      setMessages(m => {
        // If the server removed a password from the message, show the cleaned text instead of what was typed.
        const shown = res.user_message
          ? m.map((msg, i) => (i === m.length - 1 && msg.role === 'user' ? { ...msg, content: res.user_message! } : msg))
          : m
        return [...shown, { role: 'assistant', content: res.reply, products: res.products, choices: res.choices }]
      })
    } catch (err) {
      setMessages(m => [...m, { role: 'assistant', content: (err as Error).message, error: true }])
    } finally {
      setSending(false)
      inputRef.current?.focus()
    }
  }

  function submit(e: FormEvent) {
    e.preventDefault()
    send(draft)
  }

  return (
    <div className="chat">
      {open && (
        <section className="chat-panel" role="dialog" aria-label="Campus Customs chat">
          <header className="chat-header">
            <div>
              <p className="chat-title">Ask Campus Customs</p>
              <p className="chat-subtitle">
                {user ? 'Questions about merch, sizes & stock' : (
                  <><Link to="/login" onClick={() => setOpen(false)}>Log in</Link> to save your chat history</>
                )}
              </p>
            </div>
            <button className="chat-close" aria-label="Close chat" onClick={() => setOpen(false)}>
              &times;
            </button>
          </header>
          <div className="chat-messages" ref={listRef} aria-live="polite">
            {messages.length === 0 && <p className="chat-history-label">Loading your chat...</p>}
            {messages.map((m, i) => (
              <div key={i} className={`chat-row chat-row-${m.role} ${m.saved ? 'chat-row-saved' : ''}`}>
                {m.saved && i === 0 && <p className="chat-history-label">Your recent conversation</p>}
                <div className={`chat-bubble chat-${m.role} ${m.error ? 'chat-error' : ''}`}>
                  {m.role === 'assistant' ? <ChatMarkdown text={m.content} /> : m.content}
                </div>
                {m.products && m.products.length > 0 && (
                  <div className="chat-cards">
                    {m.products.map(p => <ProductMiniCard key={p.product_id} product={p} />)}
                  </div>
                )}
                {/* Yes/No or size buttons: only on the latest reply, until the shopper answers. */}
                {m.choices && m.choices.length > 0 && i === messages.length - 1 && !sending && (
                  <div
                    className={`chat-choices ${m.choices.length > 2 ? 'chat-choices-sizes' : ''}`}
                    role="group"
                    aria-label="Choose an answer"
                  >
                    {m.choices.map(c => (
                      <button key={c} className="chat-choice" onClick={() => send(c)}>
                        {c}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            ))}
            {messages.length > 0 && !messages.some(m => m.role === 'user' && !m.saved) && !sending && (
              <div className="chat-suggestions">
                {SUGGESTIONS.map(s => (
                  <button key={s} className="chip" onClick={() => send(s)}>{s}</button>
                ))}
              </div>
            )}
            {sending && (
              <div className="chat-bubble chat-assistant chat-typing" aria-label="Assistant is typing">
                <span /><span /><span />
              </div>
            )}
          </div>
          <form className="chat-input" onSubmit={submit}>
            <input
              ref={inputRef}
              value={draft}
              onChange={e => setDraft(e.target.value)}
              placeholder="Ask about a hoodie, size, or color..."
              aria-label="Chat message"
              maxLength={1000}
            />
            <button type="submit" className="btn btn-primary" disabled={!draft.trim() || sending}>
              Send
            </button>
          </form>
        </section>
      )}
      <button
        className="chat-launcher"
        aria-expanded={open}
        aria-label={open ? 'Close chat' : 'Open chat'}
        onClick={() => setOpen(o => !o)}
      >
        {open ? (
          <span aria-hidden="true" className="chat-launcher-x">&times;</span>
        ) : (
          <>
            <svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true">
              <path
                d="M4 5h16v10H8l-4 4V5z"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinejoin="round"
              />
            </svg>
            <span>Chat with us</span>
          </>
        )}
      </button>
    </div>
  )
}
