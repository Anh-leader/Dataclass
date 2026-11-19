import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import remarkMath from 'remark-math'
import rehypeKatex from 'rehype-katex'
import 'katex/dist/katex.min.css'

/** Accept common TeX delimiters while leaving Markdown code examples intact. */
function normalizeMath(value: string) {
  return value.split(/(```[\s\S]*?```|~~~[\s\S]*?~~~|`[^`\n]*`)/g).map((part, i) => i % 2 ? part : part
    .replace(/\\\[([\s\S]*?)\\\]/g, (_, math: string) => `\n\n$$\n${math.trim()}\n$$\n\n`)
    .replace(/\\\(([\s\S]*?)\\\)/g, (_, math: string) => `$${math.trim()}$`)).join('')
}

export default function MarkdownContent({ children }: { children: string }) {
  return <ReactMarkdown remarkPlugins={[remarkGfm, remarkMath]} rehypePlugins={[[rehypeKatex, { trust: false, strict: 'ignore' }]]} components={{ table: ({ children }) => <div className="markdown-table-scroll"><table>{children}</table></div> }} skipHtml>{normalizeMath(children)}</ReactMarkdown>
}
