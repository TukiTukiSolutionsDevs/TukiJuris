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
    <header className="sticky top-0 z-10 border-b border-[rgba(79,70,51,0.15)] bg-surface-container-lowest/95 backdrop-blur-sm">
      <div className={`flex w-full flex-col px-4 sm:px-6 lg:px-6 xl:px-8 ${compact ? "gap-2 py-3" : "gap-3 py-4"}`}>
        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0">
            <div className="flex items-center gap-3">
              <div className={`panel-base flex shrink-0 items-center justify-center rounded-2xl ${compact ? "h-9 w-9" : "h-10 w-10"}`}>
                {icon}
              </div>
              <div className="min-w-0">
                {eyebrow ? (
                  <p className="section-eyebrow text-primary">{eyebrow}</p>
                ) : null}
                <h1 className={`truncate font-[\'Newsreader\'] font-bold text-on-surface tracking-[-0.02em] ${compact ? "text-[2rem] leading-none sm:text-[2.3rem]" : "text-2xl sm:text-3xl"}`}>
                  {title}
                </h1>
              </div>
            </div>
            {description ? <p className={`max-w-3xl text-on-surface/50 ${compact ? "mt-1 text-[13px] leading-5" : "mt-2 text-sm leading-6"}`}>{description}</p> : null}
          </div>

          {utilitySlot || actions ? (
            <div className="flex shrink-0 flex-wrap items-center justify-end gap-2">
              {utilitySlot}
              {actions}
            </div>
          ) : null}
        </div>
      </div>
    </header>
  );
}
