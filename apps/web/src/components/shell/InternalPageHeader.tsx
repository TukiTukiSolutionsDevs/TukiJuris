"use client";

interface InternalPageHeaderProps {
  icon: React.ReactNode;
  eyebrow?: string;
  title: string;
  description?: string;
  utilitySlot?: React.ReactNode;
  actions?: React.ReactNode;
}

export function InternalPageHeader({
  icon,
  eyebrow,
  title,
  description,
  utilitySlot,
  actions,
}: InternalPageHeaderProps) {
  return (
    <header className="sticky top-0 z-10 border-b border-[rgba(79,70,51,0.15)] bg-surface-container-lowest/95 backdrop-blur-sm">
      <div className="flex w-full flex-col gap-3 px-4 py-4 sm:px-6 lg:px-6 xl:px-8">
        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0">
            <div className="flex items-center gap-3">
              <div className="panel-base flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl">
                {icon}
              </div>
              <div className="min-w-0">
                {eyebrow ? (
                  <p className="section-eyebrow text-primary">{eyebrow}</p>
                ) : null}
                <h1 className="truncate font-[\'Newsreader\'] text-2xl font-bold text-on-surface sm:text-3xl tracking-[-0.02em]">
                  {title}
                </h1>
              </div>
            </div>
            {description ? <p className="mt-2 max-w-3xl text-sm leading-6 text-on-surface/50">{description}</p> : null}
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
