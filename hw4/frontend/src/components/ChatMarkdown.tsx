import { Fragment, type ReactNode } from 'react'
import { Link } from 'react-router-dom'

// Minimal, safe Markdown for chat replies: paragraphs, "- " bullet lists, **bold**, and [links](url).
// Builds React elements directly (no innerHTML), so model output can't inject HTML.

const INLINE = /(\*\*[^*]+\*\*|\[[^\]]+\]\([^)\s]+\))/g

function inline(text: string): ReactNode[] {
  return text.split(INLINE).map((part, i) => {
    if (part.startsWith('**') && part.endsWith('**')) return <strong key={i}>{part.slice(2, -2)}</strong>
    const link = part.match(/^\[([^\]]+)\]\(([^)\s]+)\)$/)
    if (link) {
      const [, label, href] = link
      if (href.startsWith('/')) return <Link key={i} to={href}>{label}</Link>
      if (/^https?:\/\//.test(href)) {
        return <a key={i} href={href} target="_blank" rel="noreferrer">{label}</a>
      }
      return <Fragment key={i}>{label}</Fragment>
    }
    return <Fragment key={i}>{part}</Fragment>
  })
}

export default function ChatMarkdown({ text }: { text: string }) {
  const blocks: ReactNode[] = []
  let list: string[] = []
  const flush = () => {
    if (list.length) {
      blocks.push(<ul key={blocks.length}>{list.map((item, i) => <li key={i}>{inline(item)}</li>)}</ul>)
      list = []
    }
  }
  for (const raw of text.split('\n')) {
    const line = raw.trim()
    const bullet = line.match(/^[-*•]\s+(.*)$/)
    if (bullet) {
      list.push(bullet[1])
    } else {
      flush()
      if (line) blocks.push(<p key={blocks.length}>{inline(line)}</p>)
    }
  }
  flush()
  return <>{blocks}</>
}
