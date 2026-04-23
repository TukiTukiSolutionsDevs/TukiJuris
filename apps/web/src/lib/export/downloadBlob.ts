/**
 * downloadBlob — centralized blob download primitive.
 *
 * Parses `Content-Disposition` for:
 *   - `filename*=UTF-8''<percent-encoded>` (RFC 5987, takes precedence)
 *   - `filename="<value>"` or `filename=<value>`
 *
 * Falls back to `fallbackFilename` when no parseable header is present.
 */

/**
 * Extracts the filename from a `Content-Disposition` header value.
 * Returns `null` when the header is absent or unparseable.
 */
export function parseContentDispositionFilename(
  header: string | null,
): string | null {
  if (!header) return null;

  // filename*=UTF-8''<encoded> takes precedence per RFC 5987
  const starMatch = header.match(/filename\*=UTF-8''([^;\s]+)/i);
  if (starMatch) {
    try {
      return decodeURIComponent(starMatch[1]);
    } catch {
      // fall through to plain filename
    }
  }

  // Plain: filename="value" or filename=value
  const plainMatch = header.match(/filename=["']?([^"';\r\n]+)["']?/i);
  if (plainMatch) return plainMatch[1].trim();

  return null;
}

/**
 * Downloads a `Blob` as a file by creating a temporary anchor element.
 *
 * @param blob               The blob to download.
 * @param fallbackFilename   Filename to use when `contentDisposition` is absent or unparseable.
 * @param contentDisposition Optional `Content-Disposition` header value for filename extraction.
 */
export function downloadBlob(
  blob: Blob,
  fallbackFilename: string,
  contentDisposition?: string | null,
): void {
  const filename =
    parseContentDispositionFilename(contentDisposition ?? null) ??
    fallbackFilename;

  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  document.body.removeChild(anchor);
  URL.revokeObjectURL(url);
}
