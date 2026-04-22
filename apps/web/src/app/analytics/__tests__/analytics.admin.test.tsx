/**
 * Analytics page — admin defense-in-depth test (FAT-6)
 *
 * Tests the useEffect guard added per FAH-6 that calls router.replace('/')
 * for non-admin users and does NOT redirect when user is null (loading) or
 * when user is a confirmed admin.
 *
 * Pattern:
 *  - vi.hoisted() declares mocks BEFORE vi.mock hoisting runs, making them
 *    accessible inside vi.mock factory AND in test bodies.
 *  - mockUseAuth.mockReturnValue(...) is set per-test in beforeEach.
 *  - Import page AFTER mocks so the module factory captures the stubs.
 */

import { render, act } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

// ---------------------------------------------------------------------------
// Hoist mock refs so vi.mock factories can reference them
// ---------------------------------------------------------------------------

const { mockUseAuth, mockReplace, mockAuthFetch } = vi.hoisted(() => ({
  mockUseAuth: vi.fn(),
  mockReplace: vi.fn(),
  mockAuthFetch: vi.fn(),
}));

// ---------------------------------------------------------------------------
// Mock AuthContext — controlled per-test via mockReturnValue
// ---------------------------------------------------------------------------

vi.mock("@/lib/auth/AuthContext", () => ({
  useAuth: mockUseAuth,
}));

// ---------------------------------------------------------------------------
// Mock next/navigation
// ---------------------------------------------------------------------------

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: mockReplace, push: vi.fn() }),
  usePathname: () => "/analytics",
  useSearchParams: () => ({ get: () => null }),
}));

// ---------------------------------------------------------------------------
// Import page AFTER mocks
// ---------------------------------------------------------------------------

import AnalyticsPage from "../page";

// ---------------------------------------------------------------------------
// Setup
// ---------------------------------------------------------------------------

beforeEach(() => {
  mockReplace.mockReset();
  mockAuthFetch.mockResolvedValue({
    ok: true,
    json: () => Promise.resolve([]),
  });
  // Default: non-admin resolved user
  mockUseAuth.mockReturnValue({
    user: { id: "user-1", email: "user@test.com", isAdmin: false },
    authFetch: mockAuthFetch,
  });
});

// ---------------------------------------------------------------------------
// FAT-6 suite
// ---------------------------------------------------------------------------

describe("AnalyticsPage — admin defense-in-depth (FAT-6)", () => {
  it("FAT-6: calls router.replace('/') when non-admin user is resolved", async () => {
    await act(async () => {
      render(<AnalyticsPage />);
    });

    expect(mockReplace).toHaveBeenCalledWith("/");
  });

  it("FAT-6b: does NOT redirect when user is null (auth still loading)", async () => {
    mockUseAuth.mockReturnValue({
      user: null,
      authFetch: mockAuthFetch,
    });

    await act(async () => {
      render(<AnalyticsPage />);
    });

    expect(mockReplace).not.toHaveBeenCalled();
  });

  it("FAT-6c: does NOT redirect when user is a confirmed admin", async () => {
    mockUseAuth.mockReturnValue({
      user: { id: "admin-1", email: "admin@test.com", isAdmin: true },
      authFetch: mockAuthFetch,
    });

    await act(async () => {
      render(<AnalyticsPage />);
    });

    expect(mockReplace).not.toHaveBeenCalled();
  });
});
