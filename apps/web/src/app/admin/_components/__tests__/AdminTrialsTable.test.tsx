import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi, beforeEach } from "vitest";
import React from "react";
import { AdminTrialsTable } from "../AdminTrialsTable";

// ---------------------------------------------------------------------------
// Mocks — vi.hoisted() ensures refs are available before vi.mock() hoisting
// ---------------------------------------------------------------------------

const { mockAuthFetch } = vi.hoisted(() => ({
  mockAuthFetch: vi.fn(),
}));

vi.mock("@/lib/auth/AuthContext", () => ({
  useAuth: () => ({ authFetch: mockAuthFetch }),
}));

vi.mock("@/lib/api/admin", () => ({
  fetchAdminTrials: vi.fn(),
  patchAdminTrial: vi.fn(),
}));

vi.mock("@/components/trials/TrialStatusBadge", () => ({
  TrialStatusBadge: ({ status }: { status: string }) => (
    <span data-testid="trial-status-badge">{status}</span>
  ),
}));

import { fetchAdminTrials, patchAdminTrial } from "@/lib/api/admin";

const mockFetch = fetchAdminTrials as ReturnType<typeof vi.fn>;
const mockPatch = patchAdminTrial as ReturnType<typeof vi.fn>;

const TRIAL: import("@/lib/api/admin").TrialAdminRow = {
  id: "trial-1",
  user_id: "user-abc",
  plan_code: "pro",
  status: "active",
  started_at: "2026-04-01T00:00:00Z",
  ends_at: "2026-05-01T00:00:00Z",
  provider: "culqi",
  charge_id: null,
  charged_at: null,
  created_at: "2026-04-01T00:00:00Z",
};

const PAGE_ONE = { items: [TRIAL], total: 1, page: 1, per_page: 20 };

beforeEach(() => {
  vi.clearAllMocks();
});

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("AdminTrialsTable", () => {
  it("shows loading state initially", () => {
    mockFetch.mockReturnValue(new Promise(() => {}));
    render(<AdminTrialsTable />);
    expect(screen.getByText(/Cargando trials/)).toBeInTheDocument();
  });

  it("renders trial rows after successful fetch", async () => {
    mockFetch.mockResolvedValue(PAGE_ONE);
    render(<AdminTrialsTable />);

    await waitFor(() => {
      expect(screen.getByText("user-abc")).toBeInTheDocument();
      expect(screen.getByText("pro")).toBeInTheDocument();
      expect(screen.getByText("culqi")).toBeInTheDocument();
    });
  });

  it("shows empty state when no trials", async () => {
    mockFetch.mockResolvedValue({ items: [], total: 0, page: 1, per_page: 20 });
    render(<AdminTrialsTable />);

    await waitFor(() => {
      expect(screen.getByText(/No hay trials registrados/)).toBeInTheDocument();
    });
  });

  it("shows error message on fetch failure", async () => {
    mockFetch.mockRejectedValue(new Error("Server error"));
    render(<AdminTrialsTable />);

    await waitFor(() => {
      expect(screen.getByText(/No se pudieron cargar los trials/)).toBeInTheDocument();
    });
  });

  it("silently unmounts on 403", async () => {
    const err = Object.assign(new Error("Forbidden"), { status: 403 });
    mockFetch.mockRejectedValue(err);
    const { container } = render(<AdminTrialsTable />);

    await waitFor(() => {
      expect(container.firstChild).toBeNull();
    });
  });

  it("shows total count in header", async () => {
    mockFetch.mockResolvedValue({ ...PAGE_ONE, total: 7 });
    render(<AdminTrialsTable />);

    await waitFor(() => {
      expect(screen.getByText("7 total")).toBeInTheDocument();
    });
  });

  it("shows cancel button for active trial", async () => {
    mockFetch.mockResolvedValue(PAGE_ONE);
    render(<AdminTrialsTable />);

    await waitFor(() => {
      expect(screen.getByTestId("cancel-trial-trial-1")).toBeInTheDocument();
    });
  });

  it("does not show cancel button for non-active trial", async () => {
    mockFetch.mockResolvedValue({
      ...PAGE_ONE,
      items: [{ ...TRIAL, status: "downgraded" }],
    });
    render(<AdminTrialsTable />);

    await waitFor(() => {
      expect(screen.queryByTestId("cancel-trial-trial-1")).not.toBeInTheDocument();
    });
  });

  it("calls patchAdminTrial and updates row on cancel", async () => {
    const downgraded = { ...TRIAL, status: "downgraded" };
    mockFetch.mockResolvedValue(PAGE_ONE);
    mockPatch.mockResolvedValue(downgraded);
    const user = userEvent.setup();
    render(<AdminTrialsTable />);

    await waitFor(() => screen.getByTestId("cancel-trial-trial-1"));
    await user.click(screen.getByTestId("cancel-trial-trial-1"));

    await waitFor(() => {
      expect(mockPatch).toHaveBeenCalledWith(mockAuthFetch, "trial-1", {
        action: "force_downgrade",
        reason: "Admin cancelled trial",
      });
      expect(screen.queryByTestId("cancel-trial-trial-1")).not.toBeInTheDocument();
    });
  });

  it("calls fetchAdminTrials with page 1 on mount", async () => {
    mockFetch.mockResolvedValue(PAGE_ONE);
    render(<AdminTrialsTable />);

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(mockAuthFetch, 1, 20);
    });
  });
});
