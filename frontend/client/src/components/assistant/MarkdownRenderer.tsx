import React from "react";

interface MarkdownRendererProps {
  content: string;
  className?: string;
}

/**
 * Robust, safe, zero-dependency Markdown renderer for conversational assistant responses.
 * Never uses dangerouslySetInnerHTML. Safely parses headings, bold, italics, code, lists,
 * blockquotes/governance notices, citations, and separators.
 */
export function MarkdownRenderer({ content, className = "" }: MarkdownRendererProps) {
  if (!content) return null;

  const elements = parseMarkdownBlocks(content);

  return <div className={`space-y-2.5 text-xs text-slate-700 leading-relaxed ${className}`}>{elements}</div>;
}

/**
 * Split text into logical blocks (headings, blockquotes, lists, hr, paragraphs)
 */
function parseMarkdownBlocks(rawText: string): React.ReactNode[] {
  // Normalize newlines
  const lines = rawText.replace(/\r\n/g, "\n").split("\n");
  const nodes: React.ReactNode[] = [];

  let i = 0;
  let blockIndex = 0;

  while (i < lines.length) {
    const line = lines[i];
    const trimmed = line.trim();

    // 1. Empty lines
    if (!trimmed) {
      i++;
      continue;
    }

    // 2. Horizontal Rule (---, ***, ___)
    if (/^(\*{3,}|-{3,}|_{3,})$/.test(trimmed)) {
      nodes.push(
        <hr key={`hr-${blockIndex++}`} className="my-3 border-t border-slate-200" />
      );
      i++;
      continue;
    }

    // 3. Headings (#, ##, ###, ####)
    const headingMatch = trimmed.match(/^(#{1,4})\s+(.+)$/);
    if (headingMatch) {
      const level = headingMatch[1].length;
      const text = headingMatch[2];

      if (level === 1) {
        nodes.push(
          <h2
            key={`h1-${blockIndex++}`}
            className="text-sm font-black text-slate-900 tracking-tight mt-3 mb-1 flex items-center gap-1.5"
          >
            {renderInlineMarkdown(text)}
          </h2>
        );
      } else if (level === 2) {
        nodes.push(
          <h3
            key={`h2-${blockIndex++}`}
            className="text-[13px] font-extrabold text-slate-900 tracking-tight mt-3 mb-1 flex items-center gap-1.5"
          >
            {renderInlineMarkdown(text)}
          </h3>
        );
      } else {
        // H3 or H4
        nodes.push(
          <h4
            key={`h3-${blockIndex++}`}
            className="text-xs font-bold text-slate-900 tracking-wide mt-2.5 mb-1 flex items-center gap-1.5 text-[#123057]"
          >
            {renderInlineMarkdown(text)}
          </h4>
        );
      }
      i++;
      continue;
    }

    // 4. Blockquotes / Governance Callouts (> ...)
    if (trimmed.startsWith(">")) {
      const quoteLines: string[] = [];
      while (i < lines.length && lines[i].trim().startsWith(">")) {
        quoteLines.push(lines[i].trim().replace(/^>\s?/, ""));
        i++;
      }
      const quoteText = quoteLines.join("\n");
      const isNotice = quoteText.includes("💡") || quoteText.toLowerCase().includes("notice") || quoteText.toLowerCase().includes("governance");
      const isWarning = quoteText.includes("⚠️") || quoteText.toLowerCase().includes("warning");

      nodes.push(
        <div
          key={`quote-${blockIndex++}`}
          className={`rounded-xl border p-3 my-2 text-[11px] leading-relaxed shadow-2xs ${
            isWarning
              ? "border-amber-200 bg-amber-50/80 text-amber-900"
              : isNotice
              ? "border-teal-200 bg-teal-50/70 text-teal-950"
              : "border-slate-200 bg-slate-50 text-slate-700"
          }`}
        >
          <div className="space-y-1">
            {quoteLines.map((ql, qIdx) => (
              <p key={qIdx} className={qIdx === 0 ? "font-medium" : ""}>
                {renderInlineMarkdown(ql)}
              </p>
            ))}
          </div>
        </div>
      );
      continue;
    }

    // 5. Unordered List Items (- , * , • )
    if (/^[-*•]\s+/.test(trimmed)) {
      const listItems: string[] = [];
      while (i < lines.length && /^[-*•]\s+/.test(lines[i].trim())) {
        listItems.push(lines[i].trim().replace(/^[-*•]\s+/, ""));
        i++;
      }

      nodes.push(
        <ul key={`ul-${blockIndex++}`} className="my-2 space-y-1.5 pl-1">
          {listItems.map((itemText, lIdx) => (
            <li key={lIdx} className="flex items-start gap-2 text-xs">
              <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-[#ef7e37]" />
              <div className="flex-1 leading-snug">{renderInlineMarkdown(itemText)}</div>
            </li>
          ))}
        </ul>
      );
      continue;
    }

    // 6. Ordered List Items (1. , 2. )
    if (/^\d+\.\s+/.test(trimmed)) {
      const listItems: { num: string; text: string }[] = [];
      while (i < lines.length && /^\d+\.\s+/.test(lines[i].trim())) {
        const match = lines[i].trim().match(/^(\d+)\.\s+(.+)$/);
        if (match) {
          listItems.push({ num: match[1], text: match[2] });
        }
        i++;
      }

      nodes.push(
        <ol key={`ol-${blockIndex++}`} className="my-2 space-y-1.5 pl-1">
          {listItems.map((item, oIdx) => (
            <li key={oIdx} className="flex items-start gap-2 text-xs">
              <span className="flex h-4 w-4 shrink-0 items-center justify-center rounded-full bg-[#123057] text-[9px] font-bold text-white mt-0.5">
                {item.num}
              </span>
              <div className="flex-1 leading-snug">{renderInlineMarkdown(item.text)}</div>
            </li>
          ))}
        </ol>
      );
      continue;
    }

    // 7. Regular Paragraph (accumulate consecutive non-empty lines)
    const paraLines: string[] = [];
    while (
      i < lines.length &&
      lines[i].trim() &&
      !lines[i].trim().startsWith("#") &&
      !lines[i].trim().startsWith(">") &&
      !/^[-*•]\s+/.test(lines[i].trim()) &&
      !/^\d+\.\s+/.test(lines[i].trim()) &&
      !/^(\*{3,}|-{3,}|_{3,})$/.test(lines[i].trim())
    ) {
      paraLines.push(lines[i].trim());
      i++;
    }

    if (paraLines.length > 0) {
      nodes.push(
        <p key={`p-${blockIndex++}`} className="leading-relaxed">
          {renderInlineMarkdown(paraLines.join(" "))}
        </p>
      );
    }
  }

  return nodes;
}

/**
 * Safely parse inline markdown formatting:
 * **bold**, *italic*, `code`, [link](url), [SRC-01] badges
 */
function renderInlineMarkdown(text: string): React.ReactNode {
  if (!text) return null;

  // Regex tokens:
  // 1. Links: [text](url)
  // 2. Bold: **text** or __text__
  // 3. Italic: *text* or _text_
  // 4. Inline code: `code`
  // 5. Citations: [SRC-xx] or [iGOT Course] or [NSSTA Module]
  const tokenRegex = /(\[[^\]]+\]\([^)]+\)|\*\*[^*]+\*\*|__[^_]+__|`[^`]+`|\*[^*]+\*|_[^_]+_|\[(?:SRC-\d+|iGOT[^\]]*|NSSTA[^\]]*)\])/g;

  const parts = text.split(tokenRegex);

  return parts.map((part, index) => {
    if (!part) return null;

    // Link: [text](url)
    const linkMatch = part.match(/^\[([^\]]+)\]\(([^)]+)\)$/);
    if (linkMatch) {
      const [, label, url] = linkMatch;
      return (
        <a
          key={index}
          href={url}
          target="_blank"
          rel="noopener noreferrer"
          className="font-semibold text-teal-700 underline decoration-teal-400 hover:text-teal-900"
        >
          {label}
        </a>
      );
    }

    // Bold: **text** or __text__
    if ((part.startsWith("**") && part.endsWith("**")) || (part.startsWith("__") && part.endsWith("__"))) {
      const inner = part.slice(2, -2);
      return (
        <strong key={index} className="font-extrabold text-slate-900">
          {renderInlineMarkdown(inner)}
        </strong>
      );
    }

    // Inline Code: `code`
    if (part.startsWith("`") && part.endsWith("`")) {
      const inner = part.slice(1, -1);
      return (
        <code
          key={index}
          className="rounded bg-slate-100 px-1.5 py-0.5 font-mono text-[10px] font-semibold text-pink-700 border border-slate-200/60"
        >
          {inner}
        </code>
      );
    }

    // Italic: *text* or _text_
    if ((part.startsWith("*") && part.endsWith("*")) || (part.startsWith("_") && part.endsWith("_"))) {
      const inner = part.slice(1, -1);
      return (
        <em key={index} className="italic text-slate-800">
          {inner}
        </em>
      );
    }

    // Citation badge: [SRC-01] or [iGOT Course]
    const citationMatch = part.match(/^\[(SRC-\d+|iGOT[^\]]*|NSSTA[^\]]*)\]$/);
    if (citationMatch) {
      return (
        <span
          key={index}
          className="inline-flex items-center mx-1 px-1.5 py-0.2 rounded-md bg-teal-50 text-[10px] font-bold text-teal-800 border border-teal-200"
        >
          {citationMatch[1]}
        </span>
      );
    }

    // Plain text
    return <React.Fragment key={index}>{part}</React.Fragment>;
  });
}

export default MarkdownRenderer;
