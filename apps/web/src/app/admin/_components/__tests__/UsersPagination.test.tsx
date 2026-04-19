import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import React from "react";
import { UsersPagination } from "../UsersPagination";

describe("UsersPagination", () => {
  it("shows 'Sin resultados' when total is 0", () => {
    render(
      <UsersPagination page={1} perPage={20} total={0} onPageChange={vi.fn()} />
    );
    expect(screen.getByText("Sin resultados")).toBeInTheDocument();
  });

  it("shows from–to range for a mid-set page", () => {
    render(
      <UsersPagination page={2} perPage={20} total={55} onPageChange={vi.fn()} />
    );
    // page 2: items 21–40
    expect(screen.getByText(/21/)).toBeInTheDocument();
    expect(screen.getByText(/40/)).toBeInTheDocument();
  });

  it("clamps 'to' at total on the last page", () => {
    render(
      <UsersPagination page={3} perPage={20} total={55} onPageChange={vi.fn()} />
    );
    // page 3: items 41–55
    expect(screen.getByText(/41/)).toBeInTheDocument();
    expect(screen.getByText(/55/)).toBeInTheDocument();
  });

  it("disables Prev button on page 1", () => {
    render(
      <UsersPagination page={1} perPage={20} total={40} onPageChange={vi.fn()} />
    );
    expect(screen.getByLabelText("Página anterior")).toBeDisabled();
  });

  it("disables Next button on last page", () => {
    render(
      <UsersPagination page={2} perPage={20} total={40} onPageChange={vi.fn()} />
    );
    expect(screen.getByLabelText("Página siguiente")).toBeDisabled();
  });

  it("enables both buttons on a middle page", () => {
    render(
      <UsersPagination page={2} perPage={10} total={50} onPageChange={vi.fn()} />
    );
    expect(screen.getByLabelText("Página anterior")).not.toBeDisabled();
    expect(screen.getByLabelText("Página siguiente")).not.toBeDisabled();
  });

  it("calls onPageChange with page-1 when Prev is clicked", async () => {
    const onChange = vi.fn();
    render(
      <UsersPagination page={3} perPage={20} total={100} onPageChange={onChange} />
    );
    await userEvent.click(screen.getByLabelText("Página anterior"));
    expect(onChange).toHaveBeenCalledWith(2);
  });

  it("calls onPageChange with page+1 when Next is clicked", async () => {
    const onChange = vi.fn();
    render(
      <UsersPagination page={1} perPage={20} total={100} onPageChange={onChange} />
    );
    await userEvent.click(screen.getByLabelText("Página siguiente"));
    expect(onChange).toHaveBeenCalledWith(2);
  });

  it("does not render per-page selector when onPerPageChange is omitted", () => {
    render(
      <UsersPagination page={1} perPage={20} total={100} onPageChange={vi.fn()} />
    );
    expect(screen.queryByText("por pág.")).toBeNull();
  });

  it("renders per-page selector and calls onPerPageChange when provided", async () => {
    const onPerPage = vi.fn();
    render(
      <UsersPagination
        page={1}
        perPage={20}
        total={100}
        onPageChange={vi.fn()}
        onPerPageChange={onPerPage}
      />
    );
    expect(screen.getByText("por pág.")).toBeInTheDocument();
    const select = screen.getByRole("combobox");
    await userEvent.selectOptions(select, "50");
    expect(onPerPage).toHaveBeenCalledWith(50);
  });
});
