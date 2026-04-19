"use client";

interface WorkspaceShellProps {
  topbar?: React.ReactNode;
  sidebar?: React.ReactNode;
  mobileDrawer?: React.ReactNode;
  rightRail?: React.ReactNode;
  children: React.ReactNode;
  contentClassName?: string;
}

export function WorkspaceShell({
  topbar,
  sidebar,
  mobileDrawer,
  rightRail,
  children,
  contentClassName,
}: WorkspaceShellProps) {
  return (
    <div className="flex h-screen overflow-hidden bg-background">
      {sidebar ? <div className="hidden md:flex h-full shrink-0">{sidebar}</div> : null}

      <div className="flex min-w-0 flex-1 flex-col">
        {topbar ? <div className="shrink-0">{topbar}</div> : null}

        <div className="flex min-h-0 min-w-0 flex-1">
          <main
            className={`flex min-h-0 min-w-0 flex-1 flex-col overflow-y-auto bg-surface-container-lowest ${contentClassName ?? ""}`.trim()}
          >
            {children}
          </main>

          {rightRail ? <aside className="hidden xl:flex h-full shrink-0">{rightRail}</aside> : null}
        </div>
      </div>

      {mobileDrawer}
    </div>
  );
}
