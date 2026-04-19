import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import React from "react";
import AdminRouteLayout from "../layout";
import { ROUTE_AFTER_LOGIN_USER, ROUTE_LOGIN } from "@/lib/constants";

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

const mockReplace = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: mockReplace }),
}));

// We control what AuthContext returns per test via this ref.
let mockAuthValue = {
  user: null as { isAdmin: boolean } | null,
  isLoading: false,
};

vi.mock("@/lib/auth/AuthContext", () => ({
  useAuth: () => mockAuthValue,
}));

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function renderLayout(children = <div data-testid="child">Protected</div>) {
  return render(<AdminRouteLayout>{children}</AdminRouteLayout>);
}

beforeEach(() => {
  mockReplace.mockClear();
  mockAuthValue = { user: null, isLoading: false };
});

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("AdminRouteLayout", () => {
  it("renders a loading skeleton (aria-busy) while isLoading=true", () => {
    mockAuthValue = { user: null, isLoading: true };
    renderLayout();
    expect(
      screen.getByLabelText("Cargando panel de administración"),
    ).toHaveAttribute("aria-busy", "true");
    expect(screen.queryByTestId("child")).toBeNull();
  });

  it("renders the skeleton and redirects to /auth/login when unauthenticated", async () => {
    mockAuthValue = { user: null, isLoading: false };
    renderLayout();

    await waitFor(() => {
      expect(mockReplace).toHaveBeenCalledWith(
        expect.stringContaining(ROUTE_LOGIN),
      );
    });
    expect(screen.queryByTestId("child")).toBeNull();
  });

  it("redirects to / when authenticated but not admin", async () => {
    mockAuthValue = { user: { isAdmin: false }, isLoading: false };
    renderLayout();

    await waitFor(() => {
      expect(mockReplace).toHaveBeenCalledWith(ROUTE_AFTER_LOGIN_USER);
    });
    expect(screen.queryByTestId("child")).toBeNull();
  });

  it("renders children when authenticated and isAdmin=true", () => {
    mockAuthValue = { user: { isAdmin: true }, isLoading: false };
    renderLayout();

    expect(screen.getByTestId("child")).toBeInTheDocument();
    expect(mockReplace).not.toHaveBeenCalled();
  });

  it("does not redirect while still loading, even if user is null", async () => {
    mockAuthValue = { user: null, isLoading: true };
    renderLayout();

    // Give any effects a tick to fire
    await new Promise((r) => setTimeout(r, 10));
    expect(mockReplace).not.toHaveBeenCalled();
  });
});
