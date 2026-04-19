"use client";

import { useState, useEffect } from "react";
import { Sun, Moon, Menu, X } from "lucide-react";
import Link from "next/link";
import Image from "next/image";
import { useTheme } from "@/components/ThemeProvider";
import { cn } from "@/lib/utils";

const NAV_LINKS = [
  { href: "/caracteristicas", label: "Características" },
  { href: "/precios", label: "Precios" },
  { href: "/docs", label: "Documentación" },
];

export function PublicHeader() {
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === "dark";
  const [mobileOpen, setMobileOpen] = useState(false);

  // Close mobile menu on resize to desktop
  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth >= 768) setMobileOpen(false);
    };
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  // Prevent body scroll when mobile menu is open
  useEffect(() => {
    document.body.style.overflow = mobileOpen ? "hidden" : "";
    return () => { document.body.style.overflow = ""; };
  }, [mobileOpen]);

  return (
    <header className="fixed top-0 left-0 right-0 z-50">
      {/* Backdrop bar */}
      <div className="bg-surface/80 backdrop-blur-md border-b border-ghost-border">
        <div className="max-w-7xl mx-auto px-4 lg:px-8 h-16 sm:h-20 flex items-center justify-between">
          {/* ── Logo ── */}
          <Link
            href="/landing"
            className="flex items-center gap-3 rounded-2xl px-1 py-1 transition-transform duration-200 hover:scale-[1.01]"
          >
            <Image
              src="/brand/logo-icon.png"
              alt="TukiJuris"
              className="h-10 w-10 sm:h-12 sm:w-12 object-contain drop-shadow-[0_4px_12px_rgba(0,0,0,0.10)]"
              width={48}
              height={48}
              priority
            />
            <span className="font-headline text-2xl sm:text-[2rem] leading-none font-bold text-primary tracking-[-0.03em] hidden sm:inline">
              TukiJuris
            </span>
          </Link>

          {/* ── Desktop nav ── */}
          <nav className="hidden md:flex items-center gap-8">
            {NAV_LINKS.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className="text-sm text-on-surface-variant hover:text-primary transition-colors"
              >
                {link.label}
              </Link>
            ))}
          </nav>

          {/* ── Right actions ── */}
          <div className="flex items-center gap-2 sm:gap-3">
            {/* Theme toggle */}
            <button
              onClick={toggleTheme}
              title={isDark ? "Modo claro" : "Modo oscuro"}
              className="p-2 rounded-lg text-on-surface-variant hover:text-primary transition-colors"
            >
              {isDark ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
            </button>

            {/* Desktop auth */}
            <Link
              href="/auth/login"
              className="hidden sm:inline-flex text-sm text-on-surface/60 hover:text-on-surface transition-colors px-3 py-2"
            >
              Iniciar Sesión
            </Link>
            <Link
              href="/auth/register"
              className="hidden sm:inline-flex text-sm font-bold rounded-lg h-10 px-5 items-center transition-opacity hover:opacity-90 whitespace-nowrap text-on-primary gold-gradient"
            >
              Comenzar Gratis
            </Link>

            {/* Mobile hamburger */}
            <button
              onClick={() => setMobileOpen(!mobileOpen)}
              className="md:hidden p-2 rounded-lg text-on-surface-variant hover:text-primary transition-colors"
              aria-label={mobileOpen ? "Cerrar menú" : "Abrir menú"}
            >
              {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>
      </div>

      {/* ── Mobile overlay ── */}
      {mobileOpen && (
        <div
          className="md:hidden fixed inset-0 top-16 bg-black/40 backdrop-blur-sm z-40"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* ── Mobile drawer ── */}
      <div
        className={cn(
          "md:hidden fixed top-16 left-0 right-0 z-50 bg-surface border-b border-ghost-border shadow-lg transition-all duration-300 ease-in-out",
          mobileOpen
            ? "translate-y-0 opacity-100 pointer-events-auto"
            : "-translate-y-4 opacity-0 pointer-events-none"
        )}
      >
        <nav className="flex flex-col px-6 py-4 gap-1">
          {NAV_LINKS.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              onClick={() => setMobileOpen(false)}
              className="text-sm text-on-surface-variant hover:text-primary transition-colors py-3.5 border-b border-ghost-border last:border-b-0"
            >
              {link.label}
            </Link>
          ))}

          {/* Mobile auth */}
          <div className="flex flex-col gap-3 pt-4 mt-2 border-t border-ghost-border">
            <Link
              href="/auth/login"
              onClick={() => setMobileOpen(false)}
              className="text-sm text-center text-on-surface/70 hover:text-on-surface transition-colors py-2.5 rounded-lg border border-ghost-border"
            >
              Iniciar Sesión
            </Link>
            <Link
              href="/auth/register"
              onClick={() => setMobileOpen(false)}
              className="text-sm font-bold text-center rounded-lg h-10 flex items-center justify-center transition-opacity hover:opacity-90 text-on-primary gold-gradient"
            >
              Comenzar Gratis
            </Link>
          </div>
        </nav>
      </div>
    </header>
  );
}
