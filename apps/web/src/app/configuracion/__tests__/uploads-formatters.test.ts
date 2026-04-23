/**
 * Unit tests — uploads-formatters.ts
 *
 * Covers:
 *   formatFileSize — byte / KB / MB boundary conditions
 *   formatUploadDate — ISO string → DD/MM/YYYY
 */

import { describe, expect, it } from "vitest";
import { formatFileSize, formatUploadDate } from "../uploads-formatters";

// ---------------------------------------------------------------------------
// formatFileSize
// ---------------------------------------------------------------------------

describe("formatFileSize", () => {
  it("returns bytes for values under 1024", () => {
    expect(formatFileSize(0)).toBe("0 bytes");
    expect(formatFileSize(1)).toBe("1 bytes");
    expect(formatFileSize(512)).toBe("512 bytes");
    expect(formatFileSize(1023)).toBe("1023 bytes");
  });

  it("returns KB for values in [1024, 1_048_576)", () => {
    expect(formatFileSize(1024)).toBe("1.0 KB");
    expect(formatFileSize(1536)).toBe("1.5 KB");
    expect(formatFileSize(10240)).toBe("10.0 KB");
    expect(formatFileSize(1_048_575)).toBe("1024.0 KB");
  });

  it("returns MB for values >= 1_048_576", () => {
    expect(formatFileSize(1_048_576)).toBe("1.0 MB");
    expect(formatFileSize(1_572_864)).toBe("1.5 MB");
    expect(formatFileSize(10_485_760)).toBe("10.0 MB");
  });
});

// ---------------------------------------------------------------------------
// formatUploadDate
// ---------------------------------------------------------------------------

describe("formatUploadDate", () => {
  it("formats ISO string as DD/MM/YYYY", () => {
    // Fixed date: January 5, 2025
    expect(formatUploadDate("2025-01-05T14:30:00.000Z")).toMatch(/^05\/01\/2025$/);
  });

  it("zero-pads day and month", () => {
    expect(formatUploadDate("2024-03-07T08:00:00.000Z")).toMatch(/^07\/03\/2024$/);
  });

  it("handles end-of-year dates", () => {
    expect(formatUploadDate("2023-12-31T23:59:59.000Z")).toMatch(/^31\/12\/2023$/);
  });
});
