import { createContext, useContext, useState, type ReactNode } from 'react'

// The product the shopper is looking at, shared with the chat so "do you have this in pink?" makes sense.
export type PageProduct = { name: string; image_file_path: string }

type PageProductState = { product: PageProduct | null; setProduct: (product: PageProduct | null) => void }

const PageProductContext = createContext<PageProductState | null>(null)

export function PageProductProvider({ children }: { children: ReactNode }) {
  const [product, setProduct] = useState<PageProduct | null>(null)
  return <PageProductContext.Provider value={{ product, setProduct }}>{children}</PageProductContext.Provider>
}

// eslint-disable-next-line react-refresh/only-export-components
export function usePageProduct(): PageProductState {
  const ctx = useContext(PageProductContext)
  if (!ctx) throw new Error('usePageProduct must be used inside PageProductProvider')
  return ctx
}
