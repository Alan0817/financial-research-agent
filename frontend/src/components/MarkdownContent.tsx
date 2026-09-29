import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import { isSafeExternalUrl } from "../lib/format";


interface MarkdownContentProps {
  content: string;
}


export function MarkdownContent({ content }: MarkdownContentProps) {
  return (
    <div className="markdown-content">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
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
        {content}
      </ReactMarkdown>
    </div>
  );
}
