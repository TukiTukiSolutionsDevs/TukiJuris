"use client";

interface InternalPageHeaderProps {
  icon: React.ReactNode;
  eyebrow?: string;
  title: string;
  description?: string;
  utilitySlot?: React.ReactNode;
  actions?: React.ReactNode;
  compact?: boolean;
}

export function InternalPageHeader({
  icon,
  eyebrow,
  title,
  description,
  utilitySlot,
  actions,
  compact = false,
}: InternalPageHeaderProps) {
  return (
    <header className="page-header-sticky sticky top-0 z-10">
      <div
        className={`flex w-full items-start gap-4 px-4 sm:px-6 lg:px-6 xl:px-8 ${
          compact ? "py-3" : "py-[18px]"
        }`}
      >
        <div className="page-icon">{icon}</div>

        <div className="min-w-0 flex-1">
          {eyebrow ? <div className="page-eyebrow">{eyebrow}</div> : null}
          <h1
            className={`h1-page mt-0.5 truncate ${
              compact ? "!text-2xl sm:!text-[1.625rem]" : ""
            }`}
          >
            {title}
          </h1>
          {description ? (
            <p className="mt-1.5 max-w-[560px] text-[13px] leading-5 text-on-surface/50">
              {description}
            </p>
          ) : null}
        </div>

        {utilitySlot || actions ? (
          <div className="flex shrink-0 flex-wrap items-center justify-end gap-2">
            {utilitySlot}
            {actions}
          </div>
        ) : null}
      </div>
    </header>
  );
}
