import React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface MarkdownRendererProps {
  content: string;
  className?: string;
}

/**
 * Transforms citation tags like [SRC-01], [iGOT Course] inside text into styled badges.
 */
function renderFormattedText(text: string): React.ReactNode {
  if (typeof text !== "string") return text;

  const citationRegex = /(\[(?:SRC-\d+|iGOT[^\]]*|NSSTA[^\]]*)\])/g;
  const parts = text.split(citationRegex);

  if (parts.length === 1) return text;

  return parts.map((part, idx) => {
    const match = part.match(/^\[(SRC-\d+|iGOT[^\]]*|NSSTA[^\]]*)\]$/);
    if (match) {
      return (
        <span
          key={idx}
          className="inline-flex items-center mx-1 px-1.5 py-0.5 rounded-md bg-teal-50 text-[10px] font-bold text-teal-800 border border-teal-200 shadow-2xs"
        >
          {match[1]}
        </span>
      );
    }
    return <React.Fragment key={idx}>{part}</React.Fragment>;
  });
}

/**
 * Recursively process children of an element to render inline citation badges
 */
function processChildren(children: React.ReactNode): React.ReactNode {
  if (typeof children === "string") {
    return renderFormattedText(children);
  }
  if (Array.isArray(children)) {
    return children.map((child, i) => (
      <React.Fragment key={i}>{processChildren(child)}</React.Fragment>
    ));
  }
  return children;
}

/**
 * Production AST-based Markdown Renderer for Karmayogi AI Co-Pilot.
 * Powered by react-markdown and remark-gfm.
 * Completely eliminates raw markdown tokens while preserving full visual hierarchy.
 */
export function MarkdownRenderer({ content, className = "" }: MarkdownRendererProps) {
  if (!content) return null;

  return (
    <div className={`space-y-2 text-xs text-slate-700 leading-relaxed overflow-hidden ${className}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          // Headings
          h1: ({ children }) => (
            <h2 className="text-sm font-black text-slate-900 tracking-tight mt-3 mb-1.5 flex items-center gap-1.5">
              {processChildren(children)}
            </h2>
          ),
          h2: ({ children }) => (
            <h3 className="text-[13px] font-extrabold text-slate-900 tracking-tight mt-2.5 mb-1 flex items-center gap-1.5">
              {processChildren(children)}
            </h3>
          ),
          h3: ({ children }) => (
            <h4 className="text-xs font-bold text-slate-900 tracking-wide mt-2 mb-1 flex items-center gap-1.5 text-[#123057]">
              {processChildren(children)}
            </h4>
          ),
          h4: ({ children }) => (
            <h5 className="text-xs font-semibold text-slate-800 mt-1.5 mb-0.5">
              {processChildren(children)}
            </h5>
          ),

          // Paragraphs
          p: ({ children }) => (
            <p className="leading-relaxed my-1.5">
              {processChildren(children)}
            </p>
          ),

          // Strong & Emphasis
          strong: ({ children }) => (
            <strong className="font-black text-slate-900">
              {processChildren(children)}
            </strong>
          ),
          em: ({ children }) => (
            <em className="italic text-slate-800">
              {processChildren(children)}
            </em>
          ),

          // Horizontal Divider
          hr: () => (
            <hr className="my-3 border-t border-slate-200" />
          ),

          // Lists
          ul: ({ children }) => (
            <ul className="my-2 space-y-1.5 pl-0.5 list-none">
              {children}
            </ul>
          ),
          ol: ({ children }) => (
            <ol className="my-2 space-y-1.5 pl-0.5 list-decimal list-inside">
              {children}
            </ol>
          ),
          li: ({ children, ...props }) => {
            return (
              <li className="flex items-start gap-2 text-xs leading-snug my-1">
                <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-[#ef7e37]" />
                <div className="flex-1">{processChildren(children)}</div>
              </li>
            );
          },

          // Blockquotes / Governance Notices
          blockquote: ({ children }) => (
            <div className="rounded-xl border border-teal-200 bg-teal-50/70 p-3 my-2.5 text-[11px] leading-relaxed text-teal-950 shadow-2xs">
              {processChildren(children)}
            </div>
          ),

          // Inline Code & Blocks
          code: ({ children, className: codeClass }) => (
            <code className="rounded bg-slate-100 px-1.5 py-0.5 font-mono text-[10px] font-semibold text-pink-700 border border-slate-200/60">
              {children}
            </code>
          ),

          // Links
          a: ({ href, children }) => (
            <a
              href={href}
              target="_blank"
              rel="noopener noreferrer"
              className="font-semibold text-teal-700 underline decoration-teal-400 hover:text-teal-900"
            >
              {children}
            </a>
          ),
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}

export default MarkdownRenderer;
