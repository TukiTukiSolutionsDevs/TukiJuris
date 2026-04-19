import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import React from "react";
import { BYOKBadge } from "../BYOKBadge";

describe("BYOKBadge", () => {
  it("renders nothing when count is 0", () => {
    const { container } = render(<BYOKBadge count={0} />);
    expect(container.firstChild).toBeNull();
  });

  it("renders badge with count when count > 0", () => {
    render(<BYOKBadge count={3} />);
    expect(screen.getByText("3")).toBeInTheDocument();
  });

  it("renders badge for count=1", () => {
    render(<BYOKBadge count={1} />);
    expect(screen.getByText("1")).toBeInTheDocument();
  });

  it("has singular title for count=1", () => {
    render(<BYOKBadge count={1} />);
    const badge = screen.getByTitle(/clave BYOK activa/);
    expect(badge).toBeInTheDocument();
    expect(badge.getAttribute("title")).toBe("1 clave BYOK activa");
  });

  it("has plural title for count > 1", () => {
    render(<BYOKBadge count={5} />);
    const badge = screen.getByTitle(/claves BYOK activas/);
    expect(badge.getAttribute("title")).toBe("5 claves BYOK activas");
  });
});
