import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import React from "react";
import { TrialStatusBadge } from "../TrialStatusBadge";

describe("TrialStatusBadge", () => {
  it('renders "Activa" for active status', () => {
    render(<TrialStatusBadge status="active" />);
    expect(screen.getByTestId("trial-status-badge")).toHaveTextContent("Activa");
  });

  it('renders "Vencida" for expired status', () => {
    render(<TrialStatusBadge status="expired" />);
    expect(screen.getByTestId("trial-status-badge")).toHaveTextContent("Vencida");
  });

  it('renders "Cancelada" for cancelled status', () => {
    render(<TrialStatusBadge status="cancelled" />);
    expect(screen.getByTestId("trial-status-badge")).toHaveTextContent("Cancelada");
  });

  it('renders "Convertida" for converted status', () => {
    render(<TrialStatusBadge status="converted" />);
    expect(screen.getByTestId("trial-status-badge")).toHaveTextContent("Convertida");
  });

  it('renders "Cobrada" for charged status', () => {
    render(<TrialStatusBadge status="charged" />);
    expect(screen.getByTestId("trial-status-badge")).toHaveTextContent("Cobrada");
  });

  it("renders unknown status as-is", () => {
    render(<TrialStatusBadge status="unknown_state" />);
    expect(screen.getByTestId("trial-status-badge")).toHaveTextContent("unknown_state");
  });
});
