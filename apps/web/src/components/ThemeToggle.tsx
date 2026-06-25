"use client";

import { Sun, Moon } from "lucide-react";
import { useTheme } from "./ThemeProvider";

interface ThemeToggleProps {
  /** Show label text next to the icon */
  showLabel?: boolean;
  /**
   * Additional CSS classes. When provided, the default button container
   * styling is REPLACED (not appended) so callers can fully control look.
   * Pass empty string "" to use defaults.
   */
  className?: string;
}

export function ThemeToggle({ showLabel = false, className }: ThemeToggleProps) {
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === "dark";

  const defaultClass = `flex items-center gap-2 rounded-lg transition-all duration-200 ${
    showLabel
      ? "px-3 py-2 text-sm text-on-surface-variant hover:text-primary hover:bg-surface-container-high"
      : "p-2 text-on-surface-variant hover:text-primary hover:bg-surface-container-high"
  }`;

  return (
    <button
      onClick={toggleTheme}
      title={isDark ? "Cambiar a modo claro" : "Cambiar a modo oscuro"}
      aria-label={isDark ? "Cambiar a modo claro" : "Cambiar a modo oscuro"}
      className={className ?? defaultClass}
    >
      {isDark ? (
        <Sun className="h-4 w-4" strokeWidth={1.8} />
      ) : (
        <Moon className="h-4 w-4" strokeWidth={1.8} />
      )}
      {showLabel && <span>{isDark ? "Modo claro" : "Modo oscuro"}</span>}
    </button>
  );
}
