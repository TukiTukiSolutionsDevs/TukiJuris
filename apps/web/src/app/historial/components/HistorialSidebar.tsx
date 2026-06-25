"use client";

import { useState } from "react";
import {
  MessageSquare,
  Pin,
  Archive,
  Plus,
  ChevronRight,
  type LucideIcon,
} from "lucide-react";

// ---------------------------------------------------------------------------
// HistorialSidebar — inner column (260px) with: quick filters + folder tree
// + tags list. Pure visual: every callback is optional.
// ---------------------------------------------------------------------------

export interface FolderNode {
  id: string;
  name: string;
  color?: string | null;
  conversation_count: number;
  children?: FolderNode[];
}

export interface TagItem {
  id: string;
  name: string;
  slug?: string;
  color?: string | null;
  conversation_count: number;
}

export type QuickFilter = "todas" | "fijadas" | "archivadas";

interface HistorialSidebarProps {
  activeFilter: QuickFilter;
  onFilterChange: (filter: QuickFilter) => void;
  folders: FolderNode[];
  activeFolderId: string | null;
  dropTargetFolderId?: string | null;
  onFolderClick: (id: string | null) => void;
  onNewFolder?: () => void;
  tags: TagItem[];
  activeTagId: string | null;
  onTagClick: (id: string | null) => void;
  onNewTag?: () => void;
  counts: { todas: number; fijadas: number; archivadas: number };
}

function cx(...parts: (string | false | null | undefined)[]): string {
  return parts.filter(Boolean).join(" ");
}

function SectionLabel({
  children,
  action,
}: {
  children: React.ReactNode;
  action?: React.ReactNode;
}) {
  return (
    <div className="hst-section__head">
      <span className="hst-section__label">{children}</span>
      {action}
    </div>
  );
}

function NavRow({
  icon: Icon,
  label,
  count,
  active,
  onClick,
}: {
  icon: LucideIcon;
  label: string;
  count: number;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      className={cx("hst-nav", active && "is-active")}
      onClick={onClick}
      aria-current={active ? "page" : undefined}
    >
      <span className="hst-nav__icon">
        <Icon size={15} strokeWidth={1.6} />
      </span>
      <span className="hst-nav__text">{label}</span>
      <span className="hst-nav__count">{count}</span>
    </button>
  );
}

function FolderRow({
  folder,
  depth,
  open,
  onToggle,
  active,
  dropTarget,
  onClick,
}: {
  folder: FolderNode;
  depth: number;
  open: boolean;
  onToggle: (id: string) => void;
  active: boolean;
  dropTarget: boolean;
  onClick: (id: string) => void;
}) {
  const hasChildren = (folder.children?.length ?? 0) > 0;
  return (
    <>
      <button
        type="button"
        className={cx(
          "hst-folder",
          depth > 0 && "hst-folder--child",
          active && "is-active",
          dropTarget && "is-drop"
        )}
        onClick={() => {
          if (hasChildren) onToggle(folder.id);
          onClick(folder.id);
        }}
      >
        {hasChildren ? (
          <ChevronRight
            size={12}
            strokeWidth={2}
            className={cx("hst-folder__chev", open && "is-open")}
          />
        ) : (
          <span className="hst-folder__chev--empty" aria-hidden="true" />
        )}
        <span
          className="hst-folder__dot"
          style={{ background: folder.color || "var(--n-text-subtle)" }}
          aria-hidden="true"
        />
        <span className="hst-folder__name" title={folder.name}>
          {folder.name}
        </span>
        <span className="hst-folder__count">{folder.conversation_count}</span>
      </button>
      {hasChildren && open &&
        folder.children!.map((child) => (
          <FolderRow
            key={child.id}
            folder={child}
            depth={depth + 1}
            open={false}
            onToggle={onToggle}
            active={active}
            dropTarget={false}
            onClick={onClick}
          />
        ))}
    </>
  );
}

function TagRow({
  tag,
  active,
  onClick,
}: {
  tag: TagItem;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      className={cx("hst-tag", active && "is-active")}
      onClick={onClick}
    >
      <span
        className="hst-tag__dot"
        style={{ color: tag.color || "var(--n-text-subtle)" }}
        aria-hidden="true"
      />
      <span className="hst-tag__hash">#</span>
      <span className="hst-tag__name">{tag.name}</span>
      <span className="hst-tag__count">{tag.conversation_count}</span>
    </button>
  );
}

export function HistorialSidebar({
  activeFilter,
  onFilterChange,
  folders,
  activeFolderId,
  dropTargetFolderId = null,
  onFolderClick,
  onNewFolder,
  tags,
  activeTagId,
  onTagClick,
  onNewTag,
  counts,
}: HistorialSidebarProps) {
  const [openFolderIds, setOpenFolderIds] = useState<Set<string>>(new Set());

  const toggleFolder = (id: string) => {
    setOpenFolderIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  return (
    <aside className="hst-inner" aria-label="Navegación del historial">
      <div className="hst-section">
        <NavRow
          icon={MessageSquare}
          label="Todas"
          count={counts.todas}
          active={activeFilter === "todas"}
          onClick={() => onFilterChange("todas")}
        />
        <NavRow
          icon={Pin}
          label="Fijadas"
          count={counts.fijadas}
          active={activeFilter === "fijadas"}
          onClick={() => onFilterChange("fijadas")}
        />
        <NavRow
          icon={Archive}
          label="Archivadas"
          count={counts.archivadas}
          active={activeFilter === "archivadas"}
          onClick={() => onFilterChange("archivadas")}
        />
      </div>

      <div className="hst-section">
        <SectionLabel
          action={
            onNewFolder && (
              <button
                type="button"
                className="hst-section__btn"
                onClick={onNewFolder}
                aria-label="Nueva carpeta"
              >
                <Plus size={12} strokeWidth={2} />
              </button>
            )
          }
        >
          Carpetas
        </SectionLabel>
        <div className="hst-tree">
          {folders.length === 0 && (
            <div
              style={{
                padding: "10px 12px",
                fontSize: 12,
                color: "var(--n-text-subtle)",
              }}
            >
              Todavía no creaste carpetas.
            </div>
          )}
          {folders.map((folder) => (
            <FolderRow
              key={folder.id}
              folder={folder}
              depth={0}
              open={openFolderIds.has(folder.id)}
              onToggle={toggleFolder}
              active={activeFolderId === folder.id}
              dropTarget={dropTargetFolderId === folder.id}
              onClick={(id) => onFolderClick(id === activeFolderId ? null : id)}
            />
          ))}
        </div>
        {onNewFolder && (
          <button type="button" className="hst-addbtn" onClick={onNewFolder}>
            <Plus size={12} strokeWidth={2} />
            Nueva carpeta
          </button>
        )}
      </div>

      <div className="hst-section">
        <SectionLabel
          action={
            onNewTag && (
              <button
                type="button"
                className="hst-section__btn"
                onClick={onNewTag}
                aria-label="Nueva etiqueta"
              >
                <Plus size={12} strokeWidth={2} />
              </button>
            )
          }
        >
          Etiquetas
        </SectionLabel>
        {tags.length === 0 && (
          <div
            style={{
              padding: "10px 12px",
              fontSize: 12,
              color: "var(--n-text-subtle)",
            }}
          >
            Sin etiquetas todavía.
          </div>
        )}
        {tags.map((tag) => (
          <TagRow
            key={tag.id}
            tag={tag}
            active={activeTagId === tag.id}
            onClick={() => onTagClick(tag.id === activeTagId ? null : tag.id)}
          />
        ))}
        {onNewTag && (
          <button type="button" className="hst-addbtn" onClick={onNewTag}>
            <Plus size={12} strokeWidth={2} />
            Nueva etiqueta
          </button>
        )}
      </div>
    </aside>
  );
}
