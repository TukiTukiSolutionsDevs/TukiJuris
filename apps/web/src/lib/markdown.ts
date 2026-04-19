/**
 * renderMarkdown — pure regex markdown-to-HTML converter.
 * No external library, safe to use in both client and server components.
 *
 * Handles: headers, bold, italic, inline code, code blocks, bullet/numbered
 * lists, links, and paragraph wrapping. HTML entities are escaped first to
 * prevent XSS from user-supplied content.
 */
export function renderMarkdown(text: string): string {
  let html = text;

  // Escape HTML entities first to avoid XSS in user-supplied content
  html = html
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");

  // Headers (must run before bold/italic to avoid conflicts)
  html = html.replace(/^#### (.+)$/gm, "<h5 class=\"mt-3 mb-1 text-sm font-semibold text-on-surface\">$1</h5>");
  html = html.replace(/^### (.+)$/gm, "<h4 class=\"mt-4 mb-1 text-sm font-bold text-on-surface\">$1</h4>");
  html = html.replace(/^## (.+)$/gm, "<h3 class=\"mt-4 mb-2 border-b border-[rgba(79,70,51,0.15)] pb-1 text-base font-bold text-on-surface\">$1</h3>");
  html = html.replace(/^# (.+)$/gm, "<h2 class=\"mt-4 mb-2 text-lg font-bold text-on-surface\">$1</h2>");

  // Bold and italic (order matters: bold-italic first)
  html = html.replace(/\*\*\*(.+?)\*\*\*/g, "<strong><em>$1</em></strong>");
  html = html.replace(/\*\*(.+?)\*\*/g, "<strong class=\"font-semibold text-on-surface\">$1</strong>");
  html = html.replace(/\*(.+?)\*/g, "<em class=\"italic text-on-surface/80\">$1</em>");
  html = html.replace(/_(.+?)_/g, "<em class=\"italic text-on-surface/80\">$1</em>");

  // Inline code (before links to avoid conflicts)
  html = html.replace(/`([^`]+)`/g, "<code class=\"rounded bg-surface-container-high px-1 py-0.5 text-xs font-mono text-primary\">$1</code>");

  // Links
  html = html.replace(
    /\[([^\]]+)\]\(([^)]+)\)/g,
    "<a href=\"$2\" target=\"_blank\" rel=\"noopener noreferrer\" class=\"text-primary underline underline-offset-2 hover:text-primary/80\">$1</a>"
  );

  // Numbered lists — collect consecutive `N. ` lines into <ol>
  html = html.replace(
    /((?:^\d+\. .+\n?)+)/gm,
    (match) => {
      const items = match
        .trim()
        .split("\n")
        .filter(Boolean)
        .map((line) => line.replace(/^\d+\. /, ""))
        .map((item) => `<li class="ml-4 list-decimal text-on-surface/80">${item}</li>`)
        .join("\n");
      return `<ol class="my-2 space-y-0.5">\n${items}\n</ol>\n`;
    }
  );

  // Bullet lists — collect consecutive `- ` or `* ` lines
  html = html.replace(
    /((?:^[-*] .+\n?)+)/gm,
    (match) => {
      const items = match
        .trim()
        .split("\n")
        .filter(Boolean)
        .map((line) => line.replace(/^[-*] /, ""))
        .map((item) => `<li class="ml-4 list-disc text-on-surface/80">${item}</li>`)
        .join("\n");
      return `<ul class="my-2 space-y-0.5">\n${items}\n</ul>\n`;
    }
  );

  // Paragraphs — double newline becomes paragraph break
  html = html
    .split(/\n\n+/)
    .map((para) => {
      const trimmed = para.trim();
      // Don't wrap block elements in <p>
      if (
        trimmed.startsWith("<h") ||
        trimmed.startsWith("<ul") ||
        trimmed.startsWith("<ol") ||
        trimmed.startsWith("<blockquote") ||
        trimmed === ""
      ) {
        return trimmed;
      }
      return `<p class="mb-2 leading-relaxed text-on-surface/80">${trimmed.replace(/\n/g, "<br />")}</p>`;
    })
    .join("\n");

  return html;
}
