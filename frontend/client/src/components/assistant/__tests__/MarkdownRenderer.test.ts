import { describe, it, expect } from "vitest";
import React from "react";
import { renderToString } from "react-dom/server";
import { MarkdownRenderer } from "../MarkdownRenderer";

describe("MarkdownRenderer (AST-based react-markdown)", () => {
  it("renders basic paragraphs without raw markers", () => {
    const html = renderToString(React.createElement(MarkdownRenderer, { content: "Hello Officer Abhishek Pathak." }));
    expect(html).toContain("Hello Officer Abhishek Pathak.");
    expect(html).not.toContain("###");
    expect(html).not.toContain("**");
  });

  it("renders headings properly without # syntax in DOM text", () => {
    const markdown = "### 📋 Your Top Skill Gaps";
    const html = renderToString(React.createElement(MarkdownRenderer, { content: markdown }));
    expect(html).toContain("<h4");
    expect(html).toContain("Your Top Skill Gaps");
    expect(html).not.toContain("###");
  });

  it("renders bold text into <strong> tags without asterisks", () => {
    const markdown = "Deficit: **4.0**, Priority: **1**";
    const html = renderToString(React.createElement(MarkdownRenderer, { content: markdown }));
    expect(html).toContain("<strong");
    expect(html).toContain("4.0");
    expect(html).toContain("1");
    expect(html).not.toContain("**");
  });

  it("renders unordered lists with custom bullet containers", () => {
    const markdown = "- **Data Quality Frameworks**: Deficit 4.0\n- **Sampling**: Deficit 4.0";
    const html = renderToString(React.createElement(MarkdownRenderer, { content: markdown }));
    expect(html).toContain("<ul");
    expect(html).toContain("<li");
    expect(html).toContain("Data Quality Frameworks");
    expect(html).toContain("Sampling");
    expect(html).not.toContain("- **");
  });

  it("renders horizontal dividers without raw --- characters in text", () => {
    const markdown = "Above\n\n---\n\nBelow";
    const html = renderToString(React.createElement(MarkdownRenderer, { content: markdown }));
    expect(html).toContain("<hr");
    expect(html).toContain("Above");
    expect(html).toContain("Below");
    expect(html).not.toContain("---");
  });

  it("renders governance notice blockquotes with styled callouts", () => {
    const markdown = "> 💡 **Governance Notice**: Completing learning courses records **Supporting Evidence (0.30)** in your capability ledger.";
    const html = renderToString(React.createElement(MarkdownRenderer, { content: markdown }));
    expect(html).toContain("Governance Notice");
    expect(html).toContain("Supporting Evidence (0.30)");
    expect(html).not.toContain("&gt;");
    expect(html).not.toContain("**");
  });

  it("renders the exact target multi-block response completely clean of raw markdown", () => {
    const sample = `### 📋 Your Current Capability & Skill Gap Profile

**Workforce: Skill Gaps**

[SRC-01] National Competency Framework

You currently have **5 identified skill gaps**.

---

**Governance Notice**

Learning completion creates **Supporting Evidence (0.30)**.
Formal assessment creates **Authoritative Evidence (0.85)**.`;

    const html = renderToString(React.createElement(MarkdownRenderer, { content: sample }));
    expect(html).toContain("📋 Your Current Capability &amp; Skill Gap Profile");
    expect(html).toContain("Workforce: Skill Gaps");
    expect(html).toContain("SRC-01");
    expect(html).toContain("5 identified skill gaps");
    expect(html).toContain("<hr");
    expect(html).toContain("Governance Notice");
    expect(html).toContain("Supporting Evidence (0.30)");
    expect(html).toContain("Authoritative Evidence (0.85)");

    // Ensure ZERO raw Markdown control characters exist in rendered text
    expect(html).not.toContain("###");
    expect(html).not.toContain("**");
    expect(html).not.toContain("---");
  });

  it("renders Hindi Devanagari text cleanly", () => {
    const markdown = "### 📊 आपके मुख्य कौशल अंतराल\n- **डेटा गुणवत्ता ढांचा**: कमी **4.0**";
    const html = renderToString(React.createElement(MarkdownRenderer, { content: markdown }));
    expect(html).toContain("आपके मुख्य कौशल अंतराल");
    expect(html).toContain("डेटा गुणवत्ता ढांचा");
    expect(html).toContain("<strong");
    expect(html).not.toContain("###");
    expect(html).not.toContain("**");
  });

  it("renders citation badges [SRC-01] and [iGOT Course]", () => {
    const markdown = "Verified under [SRC-01] and [iGOT Course] materials.";
    const html = renderToString(React.createElement(MarkdownRenderer, { content: markdown }));
    expect(html).toContain("SRC-01");
    expect(html).toContain("iGOT Course");
  });
});
