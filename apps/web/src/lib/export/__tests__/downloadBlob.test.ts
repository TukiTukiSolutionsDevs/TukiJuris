/**
 * Unit tests for the downloadBlob helper.
 * AC IDs: FE-EXP-HELPER, FE-EXP-TESTS
 *
 * Covers:
 *  - parseContentDispositionFilename: plain filename, UTF-8 filename*, fallback, null
 *  - downloadBlob: uses Content-Disposition filename, falls back, revokes URL, clicks anchor
 */

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  downloadBlob,
  parseContentDispositionFilename,
} from "../downloadBlob";

// ---------------------------------------------------------------------------
// parseContentDispositionFilename
// ---------------------------------------------------------------------------

describe("parseContentDispositionFilename", () => {
  it("returns null for null input", () => {
    expect(parseContentDispositionFilename(null)).toBeNull();
  });

  it("returns null for empty string", () => {
    expect(parseContentDispositionFilename("")).toBeNull();
  });

  it("parses plain quoted filename", () => {
    expect(
      parseContentDispositionFilename('attachment; filename="consulta.pdf"'),
    ).toBe("consulta.pdf");
  });

  it("parses plain unquoted filename", () => {
    expect(
      parseContentDispositionFilename("attachment; filename=consulta.pdf"),
    ).toBe("consulta.pdf");
  });

  it("parses filename* UTF-8 encoded (RFC 5987)", () => {
    const header =
      "attachment; filename*=UTF-8''busqueda-derecho%20laboral.pdf";
    expect(parseContentDispositionFilename(header)).toBe(
      "busqueda-derecho laboral.pdf",
    );
  });

  it("parses filename* with non-ASCII characters", () => {
    // "perú" encoded
    const header =
      "attachment; filename*=UTF-8''consulta-per%C3%BA.pdf";
    expect(parseContentDispositionFilename(header)).toBe(
      "consulta-perú.pdf",
    );
  });

  it("prefers filename* over plain filename when both present", () => {
    const header =
      'attachment; filename="fallback.pdf"; filename*=UTF-8\'\'star.pdf';
    expect(parseContentDispositionFilename(header)).toBe("star.pdf");
  });

  it("falls back to plain filename when filename* decoding fails", () => {
    // Malformed percent encoding — decodeURIComponent will throw
    const header =
      "attachment; filename*=UTF-8''%ZZ-invalid; filename=\"fallback.pdf\"";
    expect(parseContentDispositionFilename(header)).toBe("fallback.pdf");
  });
});

// ---------------------------------------------------------------------------
// downloadBlob
// ---------------------------------------------------------------------------

describe("downloadBlob", () => {
  const FAKE_URL = "blob:http://localhost/fake-id";

  // Minimal anchor stub — just what downloadBlob needs
  const anchorStub = {
    href: "",
    download: "",
    click: vi.fn(),
  };

  beforeEach(() => {
    vi.spyOn(URL, "createObjectURL").mockReturnValue(FAKE_URL);
    vi.spyOn(URL, "revokeObjectURL").mockImplementation(() => {});
    vi.spyOn(document, "createElement").mockReturnValue(
      anchorStub as unknown as HTMLElement,
    );
    vi.spyOn(document.body, "appendChild").mockReturnValue(
      anchorStub as unknown as Node,
    );
    vi.spyOn(document.body, "removeChild").mockReturnValue(
      anchorStub as unknown as Node,
    );
    anchorStub.click.mockClear();
    anchorStub.href = "";
    anchorStub.download = "";
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("creates an object URL from the blob", () => {
    const blob = new Blob(["data"], { type: "application/pdf" });
    downloadBlob(blob, "fallback.pdf");
    expect(URL.createObjectURL).toHaveBeenCalledWith(blob);
    expect(anchorStub.href).toBe(FAKE_URL);
  });

  it("uses Content-Disposition filename when provided", () => {
    const blob = new Blob(["data"], { type: "application/pdf" });
    downloadBlob(blob, "fallback.pdf", 'attachment; filename="real.pdf"');
    expect(anchorStub.download).toBe("real.pdf");
  });

  it("falls back to fallbackFilename when no header provided", () => {
    const blob = new Blob(["data"], { type: "application/pdf" });
    downloadBlob(blob, "fallback.pdf");
    expect(anchorStub.download).toBe("fallback.pdf");
  });

  it("falls back to fallbackFilename when header is null", () => {
    const blob = new Blob(["data"], { type: "application/pdf" });
    downloadBlob(blob, "fallback.pdf", null);
    expect(anchorStub.download).toBe("fallback.pdf");
  });

  it("clicks the anchor to trigger the download", () => {
    const blob = new Blob(["data"], { type: "application/pdf" });
    downloadBlob(blob, "test.pdf");
    expect(anchorStub.click).toHaveBeenCalledOnce();
  });

  it("revokes the object URL after clicking", () => {
    const blob = new Blob(["data"], { type: "application/pdf" });
    downloadBlob(blob, "test.pdf");
    expect(URL.revokeObjectURL).toHaveBeenCalledWith(FAKE_URL);
  });

  it("appends then removes the anchor from the document body", () => {
    const blob = new Blob(["data"], { type: "application/pdf" });
    downloadBlob(blob, "test.pdf");
    expect(document.body.appendChild).toHaveBeenCalled();
    expect(document.body.removeChild).toHaveBeenCalled();
  });
});
