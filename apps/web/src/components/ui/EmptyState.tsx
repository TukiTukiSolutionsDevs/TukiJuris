"use client";

import Image from "next/image";

interface EmptyStateProps {
  /** Either provide a Lucide icon node OR set mascot=true to use the brand logo */
  icon?: React.ReactNode;
  mascot?: boolean;
  title: string;
  description?: string;
  action?: React.ReactNode;
  className?: string;
}

/**
 * Canonical empty state — used when a list/page has zero items.
 * Centered, max-w-md, py-20. Either an icon in a soft circle or the brand
 * mascot at 20% opacity. Always offer a CTA when the action is recoverable.
 */
export function EmptyState({
  icon,
  mascot = false,
  title,
  description,
  action,
  className = "",
}: EmptyStateProps) {
  return (
    <div
      className={`mx-auto flex max-w-md flex-col items-center px-6 py-20 text-center ${className}`}
    >
      {mascot ? (
        <Image
          src="/brand/logo-tj-full.png"
          alt="TukiJuris"
          width={120}
          height={36}
          className="mb-5 opacity-20"
        />
      ) : icon ? (
        <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-[rgba(201,168,76,0.1)] text-primary">
          {icon}
        </div>
      ) : null}

      <h2 className="font-['Newsreader'] text-[22px] font-semibold text-on-surface-strong">
        {title}
      </h2>
      {description ? (
        <p className="mt-2 max-w-sm text-[13.5px] leading-6 text-on-surface-variant">
          {description}
        </p>
      ) : null}
      {action ? <div className="mt-6">{action}</div> : null}
    </div>
  );
}
