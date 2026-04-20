import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import React from "react";
import { TrialStatusBadge } from "../TrialStatusBadge";

describe("TrialStatusBadge", () => {
  it('renders "Activa" for active status', () => {
    render(<TrialStatusBadge status="active" />);
    expect(screen.getByTestId("trial-status-badge")).toHaveTextContent("Activa");
  });

  it('renders "Vencida" for downgraded status', () => {
    render(<TrialStatusBadge status="downgraded" />);
    expect(screen.getByTestId("trial-status-badge")).toHaveTextContent("Vencida");
  });

  it('renders "Cancelada" for canceled status', () => {
    render(<TrialStatusBadge status="canceled" />);
    expect(screen.getByTestId("trial-status-badge")).toHaveTextContent("Cancelada");
  });

  it('renders "Cancelando" for canceled_pending status', () => {
    render(<TrialStatusBadge status="canceled_pending" />);
    expect(screen.getByTestId("trial-status-badge")).toHaveTextContent("Cancelando");
  });

  it('renders "Cobrada" for charged status', () => {
    render(<TrialStatusBadge status="charged" />);
    expect(screen.getByTestId("trial-status-badge")).toHaveTextContent("Cobrada");
  });

  it('renders "Cobro fallido" for charge_failed status', () => {
    render(<TrialStatusBadge status="charge_failed" />);
    expect(screen.getByTestId("trial-status-badge")).toHaveTextContent("Cobro fallido");
  });

  it("renders unknown status as-is", () => {
    render(<TrialStatusBadge status="unknown_state" />);
    expect(screen.getByTestId("trial-status-badge")).toHaveTextContent("unknown_state");
  });
});
