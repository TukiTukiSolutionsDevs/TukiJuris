/**
 * Unit tests for CopyOnceModal
 *
 * Covers AC3.1–AC3.4:
 *  - Secret visible only when open=true
 *  - navigator.clipboard.writeText called with the secret
 *  - Transient "Copiado" state after copy
 *  - Escape does NOT call onClose
 *  - Click-outside does NOT call onClose
 *  - Only explicit "Cerrar" button calls onClose
 */

import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { CopyOnceModal } from "../CopyOnceModal";

const mockClose = vi.fn();
// userEvent.setup() installs a clipboard stub on window.navigator.clipboard
// (via attachClipboardStubToView). We must spy on it INSIDE each test, after
// setup() has run — navigator.clipboard is undefined before that point.

beforeEach(() => {
  mockClose.mockReset();
});

describe("CopyOnceModal", () => {
  it("does not render when open=false", () => {
    render(<CopyOnceModal open={false} secret="sk-test" onClose={mockClose} />);
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("renders the secret when open=true", () => {
    render(
      <CopyOnceModal open={true} secret="sk-supersecret-abc123" onClose={mockClose} />,
    );
    expect(screen.getByRole("dialog")).toBeInTheDocument();
    expect(screen.getByTestId("copy-once-secret")).toHaveTextContent(
      "sk-supersecret-abc123",
    );
  });

  it("calls navigator.clipboard.writeText with the secret on copy click", async () => {
    const user = userEvent.setup();
    // userEvent.setup() installs the clipboard stub; spy on it now
    const writeTextSpy = vi.spyOn(navigator.clipboard, "writeText");

    render(
      <CopyOnceModal open={true} secret="sk-copy-me" onClose={mockClose} />,
    );

    await user.click(screen.getByTestId("copy-once-copy-btn"));

    expect(writeTextSpy).toHaveBeenCalledWith("sk-copy-me");
  });

  it("shows transient 'Copiado' state after copy", async () => {
    const user = userEvent.setup();
    render(
      <CopyOnceModal open={true} secret="sk-copy-me" onClose={mockClose} />,
    );

    await user.click(screen.getByTestId("copy-once-copy-btn"));

    await waitFor(() => {
      expect(screen.getByText("Copiado")).toBeInTheDocument();
    });
  });

  it("calls onClose when the explicit close button is clicked", async () => {
    const user = userEvent.setup();
    render(<CopyOnceModal open={true} secret="sk-test" onClose={mockClose} />);

    await user.click(screen.getByTestId("copy-once-close-btn"));

    expect(mockClose).toHaveBeenCalledTimes(1);
  });

  it("does NOT call onClose when Escape is pressed", async () => {
    const user = userEvent.setup();
    render(<CopyOnceModal open={true} secret="sk-test" onClose={mockClose} />);

    await user.keyboard("{Escape}");

    expect(mockClose).not.toHaveBeenCalled();
  });

  it("does NOT call onClose when the backdrop is clicked", async () => {
    const user = userEvent.setup();
    const { container } = render(
      <CopyOnceModal open={true} secret="sk-test" onClose={mockClose} />,
    );

    // The backdrop is the fixed outer container (first child of the render root)
    const backdrop = container.firstChild as HTMLElement;
    await user.click(backdrop);

    expect(mockClose).not.toHaveBeenCalled();
  });
});
