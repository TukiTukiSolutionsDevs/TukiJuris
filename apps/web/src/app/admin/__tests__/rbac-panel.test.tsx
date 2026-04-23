/**
 * UserRolesPanel tests.
 *
 * Spec IDs: FE-RBAC-EXPAND, FE-ADMIN-TESTS
 * Tests: expand fetch, assign, revoke, self-row protection, super_admin confirm.
 */
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi, beforeEach } from "vitest";
import React from "react";

// ---------------------------------------------------------------------------
// Hoisted mocks
// ---------------------------------------------------------------------------

const { mockAuthFetch } = vi.hoisted(() => ({
  mockAuthFetch: vi.fn(),
}));

vi.mock("@/lib/auth/AuthContext", () => ({
  useAuth: () => ({ authFetch: mockAuthFetch }),
}));

vi.mock("@/lib/api/admin", () => ({
  fetchUserRoles:  vi.fn(),
  assignUserRole:  vi.fn(),
  revokeUserRole:  vi.fn(),
}));

vi.mock("sonner", () => ({
  toast: { success: vi.fn(), error: vi.fn() },
}));

import { fetchUserRoles, assignUserRole, revokeUserRole } from "@/lib/api/admin";
import { toast } from "sonner";
import { UserRolesPanel } from "../_components/UserRolesPanel";

const mockFetch  = fetchUserRoles  as ReturnType<typeof vi.fn>;
const mockAssign = assignUserRole  as ReturnType<typeof vi.fn>;
const mockRevoke = revokeUserRole  as ReturnType<typeof vi.fn>;
const mockToast  = toast as unknown as { success: ReturnType<typeof vi.fn>; error: ReturnType<typeof vi.fn> };

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

const SUPPORT_ROLE = {
  id: "role-support",
  name: "support",
  display_name: "Soporte",
  description: null,
  is_system: true,
};

const SUPER_ADMIN_ROLE = {
  id: "role-super-admin",
  name: "super_admin",
  display_name: "Super Admin",
  description: null,
  is_system: true,
};

const ALL_ROLES = [SUPPORT_ROLE, SUPER_ADMIN_ROLE];

function makeRolesEndpointOk(roles = ALL_ROLES): Response {
  return { ok: true, json: async () => roles } as unknown as Response;
}

beforeEach(() => {
  vi.clearAllMocks();
  // Default: user has no roles; all system roles returned
  mockFetch.mockResolvedValue([]);
  mockAuthFetch.mockResolvedValue(makeRolesEndpointOk());
  mockAssign.mockResolvedValue(undefined);
  mockRevoke.mockResolvedValue(undefined);
  vi.spyOn(window, "confirm").mockReturnValue(true);
});

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("UserRolesPanel — fetch and display", () => {
  it("shows loading state initially", () => {
    mockFetch.mockReturnValue(new Promise(() => {}));
    render(
      <UserRolesPanel userId="user-1" currentUserId="admin-1" canWrite={true} />
    );
    expect(screen.getByText(/Cargando roles/)).toBeInTheDocument();
  });

  it("shows 'Sin roles asignados' when user has no roles", async () => {
    mockFetch.mockResolvedValue([]);
    render(
      <UserRolesPanel userId="user-1" currentUserId="admin-1" canWrite={true} />
    );
    await waitFor(() =>
      expect(screen.getByText(/Sin roles asignados/)).toBeInTheDocument()
    );
  });

  it("renders current role chips", async () => {
    mockFetch.mockResolvedValue([SUPPORT_ROLE]);
    render(
      <UserRolesPanel userId="user-1" currentUserId="admin-1" canWrite={true} />
    );
    await waitFor(() =>
      expect(screen.getByText("Soporte")).toBeInTheDocument()
    );
  });

  it("hides revoke buttons when canWrite=false", async () => {
    mockFetch.mockResolvedValue([SUPPORT_ROLE]);
    render(
      <UserRolesPanel userId="user-1" currentUserId="admin-1" canWrite={false} />
    );
    await waitFor(() => screen.getByText("Soporte"));
    expect(screen.queryByLabelText(/Revocar Soporte/)).toBeNull();
  });
});

describe("UserRolesPanel — assign flow", () => {
  it("assigns a role and shows success toast", async () => {
    const user = userEvent.setup();
    mockFetch.mockResolvedValue([]);
    render(
      <UserRolesPanel userId="user-1" currentUserId="admin-1" canWrite={true} />
    );

    await waitFor(() => screen.getByTestId("role-select"));

    // Select the support role
    await user.selectOptions(screen.getByTestId("role-select"), "role-support");
    await user.click(screen.getByTestId("assign-btn"));

    await waitFor(() =>
      expect(mockAssign).toHaveBeenCalledWith(
        mockAuthFetch,
        "user-1",
        "role-support"
      )
    );
    expect(mockToast.success).toHaveBeenCalledWith("Rol asignado");
  });

  it("shows confirm dialog before assigning super_admin and aborts if cancelled", async () => {
    const user = userEvent.setup();
    vi.spyOn(window, "confirm").mockReturnValue(false); // user cancels
    mockFetch.mockResolvedValue([]);
    render(
      <UserRolesPanel userId="user-1" currentUserId="admin-1" canWrite={true} />
    );

    await waitFor(() => screen.getByTestId("role-select"));

    await user.selectOptions(screen.getByTestId("role-select"), "role-super-admin");
    await user.click(screen.getByTestId("assign-btn"));

    expect(window.confirm).toHaveBeenCalled();
    expect(mockAssign).not.toHaveBeenCalled();
  });

  it("calls confirm and assigns super_admin when user confirms", async () => {
    const user = userEvent.setup();
    vi.spyOn(window, "confirm").mockReturnValue(true);
    mockFetch.mockResolvedValue([]);
    render(
      <UserRolesPanel userId="user-1" currentUserId="admin-1" canWrite={true} />
    );

    await waitFor(() => screen.getByTestId("role-select"));

    await user.selectOptions(screen.getByTestId("role-select"), "role-super-admin");
    await user.click(screen.getByTestId("assign-btn"));

    await waitFor(() =>
      expect(mockAssign).toHaveBeenCalledWith(
        mockAuthFetch,
        "user-1",
        "role-super-admin"
      )
    );
  });

  it("shows error toast and rolls back on assign failure", async () => {
    const user = userEvent.setup();
    mockFetch.mockResolvedValue([]);
    mockAssign.mockRejectedValue(new Error("500"));
    render(
      <UserRolesPanel userId="user-1" currentUserId="admin-1" canWrite={true} />
    );

    await waitFor(() => screen.getByTestId("role-select"));
    await user.selectOptions(screen.getByTestId("role-select"), "role-support");
    await user.click(screen.getByTestId("assign-btn"));

    await waitFor(() =>
      expect(mockToast.error).toHaveBeenCalledWith("No se pudo modificar los roles")
    );
    // Chip should be gone after rollback — check the chips container specifically
    // (the text "Soporte" may still appear in the dropdown option after rollback)
    await waitFor(() => {
      const chips = screen.getByTestId("role-chips");
      expect(within(chips).queryByText("Soporte")).toBeNull();
    });
  });
});

describe("UserRolesPanel — revoke flow", () => {
  it("revokes a role and shows success toast", async () => {
    const user = userEvent.setup();
    mockFetch.mockResolvedValue([SUPPORT_ROLE]);
    render(
      <UserRolesPanel userId="user-1" currentUserId="admin-1" canWrite={true} />
    );

    await waitFor(() => screen.getByText("Soporte"));
    await user.click(screen.getByTestId("revoke-btn-role-support"));

    await waitFor(() =>
      expect(mockRevoke).toHaveBeenCalledWith(
        mockAuthFetch,
        "user-1",
        "role-support"
      )
    );
    expect(mockToast.success).toHaveBeenCalledWith("Rol revocado");
  });

  it("shows error toast and restores chip on revoke failure", async () => {
    const user = userEvent.setup();
    mockFetch.mockResolvedValue([SUPPORT_ROLE]);
    mockRevoke.mockRejectedValue(new Error("500"));
    render(
      <UserRolesPanel userId="user-1" currentUserId="admin-1" canWrite={true} />
    );

    await waitFor(() => screen.getByText("Soporte"));
    await user.click(screen.getByTestId("revoke-btn-role-support"));

    await waitFor(() =>
      expect(mockToast.error).toHaveBeenCalledWith("No se pudo modificar los roles")
    );
    // Chip restored after rollback
    await waitFor(() =>
      expect(screen.getByText("Soporte")).toBeInTheDocument()
    );
  });
});

describe("UserRolesPanel — self-row protection", () => {
  it("disables revoke button when userId matches currentUserId", async () => {
    mockFetch.mockResolvedValue([SUPPORT_ROLE]);
    render(
      // Same user — self-row
      <UserRolesPanel userId="admin-1" currentUserId="admin-1" canWrite={true} />
    );

    await waitFor(() => screen.getByTestId("revoke-btn-role-support"));
    const revokeBtn = screen.getByTestId("revoke-btn-role-support");
    expect(revokeBtn).toBeDisabled();
  });

  it("shows tooltip text for self-row revoke", async () => {
    mockFetch.mockResolvedValue([SUPPORT_ROLE]);
    render(
      <UserRolesPanel userId="admin-1" currentUserId="admin-1" canWrite={true} />
    );

    await waitFor(() => screen.getByTestId("revoke-btn-role-support"));
    // The tooltip is on the wrapping <span>
    const tooltipWrapper = screen.getByTitle("No podés modificar tus propios roles");
    expect(tooltipWrapper).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// R8 — 409 differentiation + exact copy assertions
// ---------------------------------------------------------------------------

describe("UserRolesPanel — 409 error differentiation", () => {
  it("shows 409-specific toast when assign returns 409", async () => {
    const user = userEvent.setup();
    const err409 = Object.assign(new Error("409"), { status: 409 });
    mockAssign.mockRejectedValue(err409);
    render(
      <UserRolesPanel userId="user-1" currentUserId="admin-1" canWrite={true} />
    );

    await waitFor(() => screen.getByTestId("role-select"));
    await user.selectOptions(screen.getByTestId("role-select"), "role-support");
    await user.click(screen.getByTestId("assign-btn"));

    await waitFor(() =>
      expect(mockToast.error).toHaveBeenCalledWith("No podés modificar tus propios roles")
    );
  });

  it("shows 409-specific toast when revoke returns 409", async () => {
    const user = userEvent.setup();
    mockFetch.mockResolvedValue([SUPPORT_ROLE]);
    const err409 = Object.assign(new Error("409"), { status: 409 });
    mockRevoke.mockRejectedValue(err409);
    render(
      <UserRolesPanel userId="user-1" currentUserId="admin-1" canWrite={true} />
    );

    await waitFor(() => screen.getByText("Soporte"));
    await user.click(screen.getByTestId("revoke-btn-role-support"));

    await waitFor(() =>
      expect(mockToast.error).toHaveBeenCalledWith("No podés modificar tus propios roles")
    );
  });
});

describe("UserRolesPanel — exact spec copy", () => {
  it("super_admin confirm dialog text matches spec exactly", async () => {
    const user = userEvent.setup();
    vi.spyOn(window, "confirm").mockReturnValue(false);
    mockFetch.mockResolvedValue([]);
    render(
      <UserRolesPanel userId="user-1" currentUserId="admin-1" canWrite={true} />
    );

    await waitFor(() => screen.getByTestId("role-select"));
    await user.selectOptions(screen.getByTestId("role-select"), "role-super-admin");
    await user.click(screen.getByTestId("assign-btn"));

    expect(window.confirm).toHaveBeenCalledWith(
      "¿Estás seguro? Asignar super_admin otorga acceso total."
    );
  });

  it("self-row tooltip text matches spec exactly", async () => {
    mockFetch.mockResolvedValue([SUPPORT_ROLE]);
    render(
      <UserRolesPanel userId="admin-1" currentUserId="admin-1" canWrite={true} />
    );

    await waitFor(() => screen.getByTestId("revoke-btn-role-support"));
    expect(
      screen.getByTitle("No podés modificar tus propios roles")
    ).toBeInTheDocument();
  });
});
