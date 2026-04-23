/**
 * OrgSwitcher unit tests.
 * Spec: shared/spec.md — Reusable Organization Switcher
 */
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import React from "react";
import { OrgSwitcher } from "../OrgSwitcher";

const ORGS = [
  { id: "org-1", name: "Alpha Legal" },
  { id: "org-2", name: "Beta Corp" },
];

describe("OrgSwitcher — multi-org rendering", () => {
  it("renders a dropdown with the required aria-label when multiple orgs", () => {
    render(<OrgSwitcher orgs={ORGS} selectedOrgId="org-1" onChange={vi.fn()} />);
    expect(
      screen.getByRole("combobox", { name: "Cambiar organización" })
    ).toBeInTheDocument();
  });

  it("renders all org names as options", () => {
    render(<OrgSwitcher orgs={ORGS} selectedOrgId="org-1" onChange={vi.fn()} />);
    expect(screen.getByRole("option", { name: "Alpha Legal" })).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "Beta Corp" })).toBeInTheDocument();
  });

  it("reflects the selectedOrgId as the current value", () => {
    render(<OrgSwitcher orgs={ORGS} selectedOrgId="org-2" onChange={vi.fn()} />);
    const select = screen.getByRole("combobox") as HTMLSelectElement;
    expect(select.value).toBe("org-2");
  });
});

describe("OrgSwitcher — single org hidden", () => {
  it("renders nothing when orgs.length === 1", () => {
    const { container } = render(
      <OrgSwitcher orgs={[ORGS[0]]} selectedOrgId="org-1" onChange={vi.fn()} />
    );
    expect(container.firstChild).toBeNull();
  });

  it("renders nothing when orgs is empty", () => {
    const { container } = render(
      <OrgSwitcher orgs={[]} selectedOrgId="" onChange={vi.fn()} />
    );
    expect(container.firstChild).toBeNull();
  });
});

describe("OrgSwitcher — onChange behavior", () => {
  it("calls onChange with the new org id when user selects a different org", async () => {
    const handleChange = vi.fn();
    const user = userEvent.setup();
    render(<OrgSwitcher orgs={ORGS} selectedOrgId="org-1" onChange={handleChange} />);

    await user.selectOptions(screen.getByRole("combobox"), "org-2");
    expect(handleChange).toHaveBeenCalledWith("org-2");
  });

  it("does NOT call onChange with extra arguments — only the orgId string", async () => {
    const handleChange = vi.fn();
    const user = userEvent.setup();
    render(<OrgSwitcher orgs={ORGS} selectedOrgId="org-1" onChange={handleChange} />);

    await user.selectOptions(screen.getByRole("combobox"), "org-2");
    expect(handleChange).toHaveBeenCalledTimes(1);
    expect(typeof handleChange.mock.calls[0][0]).toBe("string");
  });
});

describe("OrgSwitcher — keyboard navigation", () => {
  it("is focusable via keyboard", () => {
    render(<OrgSwitcher orgs={ORGS} selectedOrgId="org-1" onChange={vi.fn()} />);
    const select = screen.getByRole("combobox", { name: "Cambiar organización" });
    select.focus();
    expect(document.activeElement).toBe(select);
  });
});
