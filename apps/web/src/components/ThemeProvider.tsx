"use client";

import { createContext, useContext, useEffect, useState, useCallback } from "react";

type Theme = "light" | "dark";

interface ThemeContextValue {
  theme: Theme;
  toggleTheme: () => void;
  setTheme: (t: Theme) => void;
}

const ThemeContext = createContext<ThemeContextValue>({
  theme: "dark",
  toggleTheme: () => {},
  setTheme: () => {},
});

export function useTheme() {
  return useContext(ThemeContext);
}

/**
 * Resolves the initial theme synchronously from localStorage or system preference.
 * Called once during SSR-safe hydration.
 */
function getInitialTheme(): Theme {
  if (typeof window === "undefined") return "dark";
  const stored = localStorage.getItem("tukijuris-theme") as Theme | null;
  if (stored === "light" || stored === "dark") return stored;
  // Respect system preference
  if (window.matchMedia("(prefers-color-scheme: light)").matches) return "light";
  return "dark";
}

/**
 * Apply theme class to <html> — called both during init and on toggle.
 */
function applyTheme(theme: Theme) {
  const html = document.documentElement;
  html.classList.remove("light", "dark");
  html.classList.add(theme);
  // Update meta theme-color for mobile browsers
  const meta = document.querySelector('meta[name="theme-color"]');
  if (meta) {
    meta.setAttribute("content", theme === "dark" ? "#0C0E14" : "#F5F2EB");
  }
}

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setThemeState] = useState<Theme>("dark"); // SSR default
  const [mounted, setMounted] = useState(false);

  // Hydrate from client
  useEffect(() => {
    const resolved = getInitialTheme();
    setThemeState(resolved);
    applyTheme(resolved);
    setMounted(true);
  }, []);

  const setTheme = useCallback((t: Theme) => {
    setThemeState(t);
    applyTheme(t);
    localStorage.setItem("tukijuris-theme", t);
  }, []);

  const toggleTheme = useCallback(() => {
    setTheme(theme === "dark" ? "light" : "dark");
  }, [theme, setTheme]);

  // Listen for system preference changes
  useEffect(() => {
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    const handler = (e: MediaQueryListEvent) => {
      // Only auto-switch if user hasn't explicitly chosen
      const stored = localStorage.getItem("tukijuris-theme");
      if (!stored) {
        setTheme(e.matches ? "dark" : "light");
      }
    };
    mq.addEventListener("change", handler);
    return () => mq.removeEventListener("change", handler);
  }, [setTheme]);

  // Sync across tabs
  useEffect(() => {
    const handler = (e: StorageEvent) => {
      if (e.key === "tukijuris-theme" && (e.newValue === "light" || e.newValue === "dark")) {
        setThemeState(e.newValue);
        applyTheme(e.newValue);
      }
    };
    window.addEventListener("storage", handler);
    return () => window.removeEventListener("storage", handler);
  }, []);

  // Prevent FOUC — don't render children until theme is resolved
  if (!mounted) return null;

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}
