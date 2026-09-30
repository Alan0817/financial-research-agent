import "katex/dist/katex.min.css";

import ReactMarkdown from "react-markdown";
import rehypeKatex from "rehype-katex";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";

import { isSafeExternalUrl } from "../lib/format";


interface MarkdownContentProps {
  content: string;
}

// Normalize only literal LaTeX delimiter pairs outside Markdown code spans.
const protectedCodePattern = /(```[\s\S]*?```|`[^`\r\n]*`)/g;
const inlineMathDelimiterPattern = /\\\(([^\r\n]*?)\\\)/g;
const displayMathDelimiterPattern = /\\\[([\s\S]*?)\\\]/g;



function normalizeMathDelimiters(content: string): string {
  return content
    .split(protectedCodePattern)
    .map((segment, index) => {
      if (index % 2 === 1) {
        return segment;
      }

      return segment
        .replace(displayMathDelimiterPattern, (match, expression) => {
          const math = expression.trim();
          return math ? `\n\n$$\n${math}\n$$\n\n` : match;
        })
        .replace(inlineMathDelimiterPattern, (match, expression) => {
          const math = expression.trim();
          return math ? `$${math}$` : match;
        });
    })
    .join("");
}


export function MarkdownContent({ content }: MarkdownContentProps) {
  const normalizedContent = normalizeMathDelimiters(content);

  return (
    <div className="markdown-content">
      <ReactMarkdown
        rehypePlugins={[[rehypeKatex, { trust: false }]]}
        remarkPlugins={[remarkGfm, remarkMath]}
        components={{
          a({ children, href }) {
            if (!isSafeExternalUrl(href)) {
              return <span>{children}</span>;
            }

            return (
              <a href={href} rel="noopener noreferrer" target="_blank">
                {children}
              </a>
            );
          },
        }}
      >
        {normalizedContent}
      </ReactMarkdown>
    </div>
  );
}
