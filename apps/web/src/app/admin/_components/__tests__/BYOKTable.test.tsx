import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi, beforeEach } from "vitest";
import React from "react";
import { BYOKTable } from "../BYOKTable";

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

const mockAuthFetch = vi.fn();

vi.mock("@/lib/auth/AuthContext", () => ({
  useAuth: () => ({ authFetch: mockAuthFetch }),
}));

vi.mock("@/lib/api/admin", () => ({
  fetchBYOK: vi.fn(),
}));

import { fetchBYOK } from "@/lib/api/admin";

const mockFetchBYOK = fetchBYOK as ReturnType<typeof vi.fn>;

const BYOK_ITEM = {
  user_id: "u1",
  user_email: "alice@example.com",
  provider: "openai",
  api_key_hint: "sk-...abc",
  is_active: true,
  last_rotation_at: "2025-01-15T00:00:00Z",
};

const BYOK_PAGE = {
  items: [BYOK_ITEM],
  total: 1,
  page: 1,
  per_page: 20,
};

beforeEach(() => {
  vi.clearAllMocks();
});

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("BYOKTable", () => {
  it("shows loading state initially", () => {
    mockFetchBYOK.mockReturnValue(new Promise(() => {}));
    render(<BYOKTable />);
    expect(screen.getByText(/Cargando claves/)).toBeInTheDocument();
  });

  it("renders BYOK items after successful fetch", async () => {
    mockFetchBYOK.mockResolvedValue(BYOK_PAGE);
    render(<BYOKTable />);

    await waitFor(() => {
      expect(screen.getByText("alice@example.com")).toBeInTheDocument();
      expect(screen.getByText("openai")).toBeInTheDocument();
      expect(screen.getByText("sk-...abc")).toBeInTheDocument();
    });
  });

  it("does NOT render encrypted key material (only hint)", async () => {
    mockFetchBYOK.mockResolvedValue({
      ...BYOK_PAGE,
      items: [{ ...BYOK_ITEM, api_key_hint: "sk-...xyz" }],
    });
    render(<BYOKTable />);

    await waitFor(() => {
      expect(screen.getByText("sk-...xyz")).toBeInTheDocument();
      // Full key is never present in the DOM
      expect(screen.queryByText(/sk-[A-Za-z0-9]{30,}/)).toBeNull();
    });
  });

  it("shows empty state when no items", async () => {
    mockFetchBYOK.mockResolvedValue({ items: [], total: 0, page: 1, per_page: 20 });
    render(<BYOKTable />);

    await waitFor(() => {
      expect(screen.getByText(/No hay claves BYOK registradas/)).toBeInTheDocument();
    });
  });

  it("silently unmounts (returns null) when API returns 403", async () => {
    const err = Object.assign(new Error("Forbidden"), { status: 403 });
    mockFetchBYOK.mockRejectedValue(err);

    const { container } = render(<BYOKTable />);

    await waitFor(() => {
      expect(container.firstChild).toBeNull();
    });
  });

  it("shows error message on non-403 failure", async () => {
    const err = Object.assign(new Error("Internal Server Error"), { status: 500 });
    mockFetchBYOK.mockRejectedValue(err);

    render(<BYOKTable />);

    await waitFor(() => {
      expect(screen.getByText(/No se pudieron cargar las claves BYOK/)).toBeInTheDocument();
    });
  });

  it("shows pagination when total > perPage", async () => {
    mockFetchBYOK.mockResolvedValue({
      items: [BYOK_ITEM],
      total: 50,
      page: 1,
      per_page: 20,
    });
    render(<BYOKTable />);

    await waitFor(() => {
      expect(screen.getByLabelText("Página siguiente")).toBeInTheDocument();
    });
  });

  it("calls fetchBYOK with page 2 when Next is clicked", async () => {
    mockFetchBYOK.mockResolvedValue({
      items: [BYOK_ITEM],
      total: 50,
      page: 1,
      per_page: 20,
    });
    render(<BYOKTable />);

    await waitFor(() => screen.getByLabelText("Página siguiente"));
    await userEvent.click(screen.getByLabelText("Página siguiente"));

    await waitFor(() => {
      // Second call should be for page 2
      expect(mockFetchBYOK).toHaveBeenCalledWith(mockAuthFetch, 2, 20);
    });
  });

  it("shows total count in header", async () => {
    mockFetchBYOK.mockResolvedValue({ items: [BYOK_ITEM], total: 7, page: 1, per_page: 20 });
    render(<BYOKTable />);

    await waitFor(() => {
      expect(screen.getByText(/7 configuraciones/)).toBeInTheDocument();
    });
  });
});
