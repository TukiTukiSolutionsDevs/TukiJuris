/**
 * Formatters for the Archivos (uploads) tab.
 */

/**
 * Converts a byte count to a human-readable string.
 * - < 1 024            → "N bytes"
 * - < 1 048 576 (1 MB) → "N.N KB"
 * - else               → "N.N MB"
 */
export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} bytes`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

/**
 * Formats an ISO datetime string as DD/MM/YYYY (Argentina locale, timezone-safe).
 */
export function formatUploadDate(iso: string): string {
  const d = new Date(iso);
  const day = String(d.getDate()).padStart(2, "0");
  const month = String(d.getMonth() + 1).padStart(2, "0");
  const year = d.getFullYear();
  return `${day}/${month}/${year}`;
}
