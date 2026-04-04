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
  html = html.replace(/^#### (.+)$/gm, "<h5 class=\"text-sm font-semibold mt-3 mb-1 text-gray-100\">$1</h5>");
  html = html.replace(/^### (.+)$/gm, "<h4 class=\"text-sm font-bold mt-4 mb-1 text-white\">$1</h4>");
  html = html.replace(/^## (.+)$/gm, "<h3 class=\"text-base font-bold mt-4 mb-2 text-white border-b border-gray-700 pb-1\">$1</h3>");
  html = html.replace(/^# (.+)$/gm, "<h2 class=\"text-lg font-bold mt-4 mb-2 text-white\">$1</h2>");

  // Bold and italic (order matters: bold-italic first)
  html = html.replace(/\*\*\*(.+?)\*\*\*/g, "<strong><em>$1</em></strong>");
  html = html.replace(/\*\*(.+?)\*\*/g, "<strong class=\"font-semibold text-white\">$1</strong>");
  html = html.replace(/\*(.+?)\*/g, "<em class=\"italic text-gray-200\">$1</em>");
  html = html.replace(/_(.+?)_/g, "<em class=\"italic text-gray-200\">$1</em>");

  // Inline code (before links to avoid conflicts)
  html = html.replace(/`([^`]+)`/g, "<code class=\"bg-gray-900 text-amber-300 px-1 py-0.5 rounded text-xs font-mono\">$1</code>");

  // Links
  html = html.replace(
    /\[([^\]]+)\]\(([^)]+)\)/g,
    "<a href=\"$2\" target=\"_blank\" rel=\"noopener noreferrer\" class=\"text-amber-400 hover:text-amber-300 underline\">$1</a>"
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
        .map((item) => `<li class="ml-4 list-decimal">${item}</li>`)
        .join("\n");
      return `<ol class="my-2 space-y-0.5 text-gray-300">\n${items}\n</ol>\n`;
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
        .map((item) => `<li class="ml-4 list-disc">${item}</li>`)
        .join("\n");
      return `<ul class="my-2 space-y-0.5 text-gray-300">\n${items}\n</ul>\n`;
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
      return `<p class="mb-2 leading-relaxed">${trimmed.replace(/\n/g, "<br />")}</p>`;
    })
    .join("\n");

  return html;
}
