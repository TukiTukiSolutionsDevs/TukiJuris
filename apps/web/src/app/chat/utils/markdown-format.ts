// ---------------------------------------------------------------------------
// Formatting toolbar helpers
// ---------------------------------------------------------------------------
export function insertMarkdownSyntax(
  textarea: HTMLTextAreaElement,
  prefix: string,
  suffix: string,
  placeholder: string,
  setter: (v: string) => void
) {
  const start = textarea.selectionStart;
  const end = textarea.selectionEnd;
  const selected = textarea.value.slice(start, end) || placeholder;
  const before = textarea.value.slice(0, start);
  const after = textarea.value.slice(end);
  const newValue = `${before}${prefix}${selected}${suffix}${after}`;
  setter(newValue);

  // Restore focus and selection after React re-render
  requestAnimationFrame(() => {
    textarea.focus();
    const newStart = start + prefix.length;
    const newEnd = newStart + selected.length;
    textarea.setSelectionRange(newStart, newEnd);
  });
}
