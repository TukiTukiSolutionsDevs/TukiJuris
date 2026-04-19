"use client";

import Image from "next/image";
import Link from "next/link";
import { Menu } from "lucide-react";

interface ShellTopbarProps {
  title: string;
  logoHref?: string;
  logoSrc?: string;
  onOpenMenu?: () => void;
  endSlot?: React.ReactNode;
}

export function ShellTopbar({
  title,
  logoHref = "/",
  logoSrc,
  onOpenMenu,
  endSlot,
}: ShellTopbarProps) {
  return (
    <header className="sticky top-0 z-40 border-b border-[rgba(79,70,51,0.12)] bg-surface/95 backdrop-blur md:hidden">
      <div className="flex h-14 items-center gap-3 px-3">
        <button
          type="button"
          onClick={onOpenMenu}
          aria-label="Abrir menu"
          className="control-surface inline-flex h-9 w-9 items-center justify-center rounded-xl text-on-surface/70 hover:text-on-surface"
        >
          <Menu className="h-4 w-4" />
        </button>

        <Link href={logoHref} className="flex min-w-0 items-center gap-2 rounded-xl px-1.5 py-1 transition hover:bg-surface-container-low/60">
          {logoSrc ? <Image src={logoSrc} alt={title} className="h-7 w-auto object-contain" width={120} height={28} /> : null}
          <span className="truncate text-sm font-semibold text-on-surface">{title}</span>
        </Link>

        <div className="ml-auto flex items-center gap-2">{endSlot}</div>
      </div>
    </header>
  );
}
