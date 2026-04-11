"use client";

import Image from "next/image";
import { useState, useEffect, useCallback } from "react";
import {
  History,
  Search,
  Pin,
  Archive,
  Share2,
  Trash2,
  MessageSquare,
  CheckSquare,
  Square,
  ChevronDown,
  Loader2,
  RotateCcw,
  Check,
  Tag,
  Folder,
  FolderOpen,
  Plus,
  X,
  ChevronRight,
  Edit2,
  FolderInput,
} from "lucide-react";
import { useRouter } from "next/navigation";
import { getToken } from "@/lib/auth";
import { AppLayout } from "@/components/AppLayout";
import { InternalPageHeader } from "@/components/shell/InternalPageHeader";
import { ShellUtilityActions } from "@/components/shell/ShellUtilityActions";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const APP_URL = process.env.NEXT_PUBLIC_APP_URL || "https://tukijuris.net.pe";

type ConversationStatus = "active" | "pinned" | "archived";
type SortKey = "date_desc" | "date_asc" | "area" | "messages";

interface TagItem {
  id: string;
  name: string;
  color: string;
}

interface FolderItem {
  id: string;
  name: string;
  icon: string;
  position: number;
  conversation_count: number;
}

interface ConversationItem {
  id: string;
  title: string | null;
  legal_area: string | null;
  model_used: string;
  is_pinned: boolean;
  is_archived: boolean;
  is_shared: boolean;
  folder_id: string | null;
  folder_name: string | null;
  tags: TagItem[];
  message_count: number;
  created_at: string;
  updated_at: string;
}

const AREA_LABELS: Record<string, string> = {
  civil: "Civil",
  penal: "Penal",
  laboral: "Laboral",
  tributario: "Tributario",
  constitucional: "Constitucional",
  administrativo: "Administrativo",
  corporativo: "Corporativo",
  registral: "Registral",
  competencia: "Competencia",
  compliance: "Compliance",
  comercio_exterior: "Comercio Ext.",
};

const TAG_COLOR_PRESETS = [
  "#3b82f6",
  "#ef4444",
  "#22c55e",
  "#f59e0b",
  "#8b5cf6",
  "#ec4899",
  "#06b6d4",
  "#f97316",
];

function formatDate(iso: string): string {
  const date = new Date(iso);
  return date.toLocaleDateString("es-PE", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export default function HistorialPage() {
  const router = useRouter();
  const [tab, setTab] = useState<ConversationStatus>("active");
  const [conversations, setConversations] = useState<ConversationItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [sortKey, setSortKey] = useState<SortKey>("date_desc");
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [bulkLoading, setBulkLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  // Tags state
  const [tags, setTags] = useState<TagItem[]>([]);
  const [activeTagFilter, setActiveTagFilter] = useState<string | null>(null);
  const [tagsExpanded, setTagsExpanded] = useState(true);
  const [showNewTagForm, setShowNewTagForm] = useState(false);
  const [newTagName, setNewTagName] = useState("");
  const [newTagColor, setNewTagColor] = useState(TAG_COLOR_PRESETS[0]);
  const [tagActionLoading, setTagActionLoading] = useState<string | null>(null);
  const [editingTag, setEditingTag] = useState<TagItem | null>(null);

  // Folders state
  const [folders, setFolders] = useState<FolderItem[]>([]);
  const [activeFolderFilter, setActiveFolderFilter] = useState<string | null>(null);
  const [foldersExpanded, setFoldersExpanded] = useState(true);
  const [showNewFolderForm, setShowNewFolderForm] = useState(false);
  const [newFolderName, setNewFolderName] = useState("");
  const [folderActionLoading, setFolderActionLoading] = useState<string | null>(null);

  // Tag dropdown per conversation
  const [tagDropdownConv, setTagDropdownConv] = useState<string | null>(null);
  // Folder submenu per conversation
  const [folderMenuConv, setFolderMenuConv] = useState<string | null>(null);

  const authHeaders = useCallback((): HeadersInit => {
    const token = getToken();
    return token
      ? { Authorization: `Bearer ${token}`, "Content-Type": "application/json" }
      : { "Content-Type": "application/json" };
  }, []);

  const fetchConversations = useCallback(async () => {
    setLoading(true);
    setSelected(new Set());
    try {
      const statusParam = tab === "pinned" ? "pinned" : tab;
      const res = await fetch(
        `${API_URL}/api/conversations/?status=${statusParam}`,
        { headers: authHeaders() }
      );
      if (!res.ok) throw new Error("Error");
      const data: ConversationItem[] = await res.json();
      setConversations(data);
    } catch {
      setConversations([]);
    } finally {
      setLoading(false);
    }
  }, [tab, authHeaders]);

  const fetchTags = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/api/tags/`, { headers: authHeaders() });
      if (!res.ok) return;
      const data: TagItem[] = await res.json();
      setTags(data);
    } catch {
      // ignore
    }
  }, [authHeaders]);

  const fetchFolders = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/api/folders/`, { headers: authHeaders() });
      if (!res.ok) return;
      const data: FolderItem[] = await res.json();
      setFolders(data);
    } catch {
      // ignore
    }
  }, [authHeaders]);

  useEffect(() => {
    fetchConversations();
  }, [fetchConversations]);

  useEffect(() => {
    fetchTags();
    fetchFolders();
  }, [fetchTags, fetchFolders]);

  useEffect(() => {
    const handler = () => {
      setTagDropdownConv(null);
      setFolderMenuConv(null);
    };
    document.addEventListener("click", handler);
    return () => document.removeEventListener("click", handler);
  }, []);

  // ---------- Filtering + Sorting ----------

  const filtered = conversations
    .filter((c) => {
      if (activeTagFilter && !c.tags.some((t) => t.id === activeTagFilter)) return false;
      if (activeFolderFilter && c.folder_id !== activeFolderFilter) return false;
      if (!search.trim()) return true;
      const q = search.toLowerCase();
      return (
        c.title?.toLowerCase().includes(q) ||
        (c.legal_area && AREA_LABELS[c.legal_area]?.toLowerCase().includes(q))
      );
    })
    .sort((a, b) => {
      if (sortKey === "date_desc")
        return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime();
      if (sortKey === "date_asc")
        return new Date(a.updated_at).getTime() - new Date(b.updated_at).getTime();
      if (sortKey === "area")
        return (a.legal_area ?? "").localeCompare(b.legal_area ?? "");
      if (sortKey === "messages") return b.message_count - a.message_count;
      return 0;
    });

  // ---------- Selection ----------

  const toggleSelect = (id: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const selectAll = () => {
    if (selected.size === filtered.length) {
      setSelected(new Set());
    } else {
      setSelected(new Set(filtered.map((c) => c.id)));
    }
  };

  // ---------- Single actions ----------

  const apiAction = async (id: string, endpoint: string, method = "PUT") => {
    setActionLoading(id + endpoint);
    try {
      const res = await fetch(
        `${API_URL}/api/conversations/${id}/${endpoint}`,
        { method, headers: authHeaders() }
      );
      if (!res.ok) return;
      fetchConversations();
    } finally {
      setActionLoading(null);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Eliminar esta conversacion permanentemente?")) return;
    await apiAction(id, "", "DELETE");
  };

  const handleShare = async (id: string) => {
    setActionLoading(id + "share");
    try {
      const res = await fetch(
        `${API_URL}/api/conversations/${id}/share`,
        { method: "POST", headers: authHeaders() }
      );
      if (!res.ok) return;
      const data = await res.json();
      const url = data.url ?? `${APP_URL}/compartido/${data.share_id}`;
      await navigator.clipboard.writeText(url);
      setCopiedId(id);
      fetchConversations();
      setTimeout(() => setCopiedId(null), 2500);
    } finally {
      setActionLoading(null);
    }
  };

  // ---------- Bulk actions ----------

  const bulkAction = async (action: "archive" | "delete") => {
    if (selected.size === 0) return;
    if (action === "delete") {
      if (!confirm(`Eliminar ${selected.size} conversaciones permanentemente?`)) return;
    }
    setBulkLoading(true);
    try {
      await Promise.all(
        Array.from(selected).map((id) => {
          const method = action === "delete" ? "DELETE" : "PUT";
          const endpoint = action === "delete" ? "" : "archive";
          return fetch(`${API_URL}/api/conversations/${id}/${endpoint}`, {
            method,
            headers: authHeaders(),
          });
        })
      );
      fetchConversations();
    } finally {
      setBulkLoading(false);
    }
  };

  // ---------- Tag management ----------

  const handleCreateTag = async () => {
    if (!newTagName.trim()) return;
    setTagActionLoading("create");
    try {
      const res = await fetch(`${API_URL}/api/tags/`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({ name: newTagName.trim(), color: newTagColor }),
      });
      if (!res.ok) return;
      setNewTagName("");
      setNewTagColor(TAG_COLOR_PRESETS[0]);
      setShowNewTagForm(false);
      fetchTags();
    } finally {
      setTagActionLoading(null);
    }
  };

  const handleDeleteTag = async (tagId: string) => {
    if (!confirm("Eliminar esta etiqueta?")) return;
    setTagActionLoading(tagId);
    try {
      await fetch(`${API_URL}/api/tags/${tagId}`, {
        method: "DELETE",
        headers: authHeaders(),
      });
      if (activeTagFilter === tagId) setActiveTagFilter(null);
      fetchTags();
      fetchConversations();
    } finally {
      setTagActionLoading(null);
    }
  };

  const handleUpdateTag = async (tag: TagItem) => {
    setTagActionLoading(tag.id);
    try {
      const res = await fetch(`${API_URL}/api/tags/${tag.id}`, {
        method: "PUT",
        headers: authHeaders(),
        body: JSON.stringify({ name: tag.name, color: tag.color }),
      });
      if (!res.ok) return;
      setEditingTag(null);
      fetchTags();
      fetchConversations();
    } finally {
      setTagActionLoading(null);
    }
  };

  const handleAssignTag = async (convId: string, tagId: string) => {
    await fetch(`${API_URL}/api/conversations/${convId}/tags/${tagId}`, {
      method: "POST",
      headers: authHeaders(),
    });
    setTagDropdownConv(null);
    fetchConversations();
  };

  const handleRemoveTag = async (convId: string, tagId: string) => {
    await fetch(`${API_URL}/api/conversations/${convId}/tags/${tagId}`, {
      method: "DELETE",
      headers: authHeaders(),
    });
    fetchConversations();
  };

  // ---------- Folder management ----------

  const handleCreateFolder = async () => {
    if (!newFolderName.trim()) return;
    setFolderActionLoading("create");
    try {
      const res = await fetch(`${API_URL}/api/folders/`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({ name: newFolderName.trim(), icon: "folder" }),
      });
      if (!res.ok) return;
      setNewFolderName("");
      setShowNewFolderForm(false);
      fetchFolders();
    } finally {
      setFolderActionLoading(null);
    }
  };

  const handleDeleteFolder = async (folderId: string) => {
    if (!confirm("Eliminar esta carpeta? Las conversaciones no se eliminaran.")) return;
    setFolderActionLoading(folderId);
    try {
      await fetch(`${API_URL}/api/folders/${folderId}`, {
        method: "DELETE",
        headers: authHeaders(),
      });
      if (activeFolderFilter === folderId) setActiveFolderFilter(null);
      fetchFolders();
      fetchConversations();
    } finally {
      setFolderActionLoading(null);
    }
  };

  const handleMoveToFolder = async (convId: string, folderId: string | null) => {
    if (folderId) {
      await fetch(`${API_URL}/api/conversations/${convId}/folder/${folderId}`, {
        method: "PUT",
        headers: authHeaders(),
      });
    } else {
      await fetch(`${API_URL}/api/conversations/${convId}/folder`, {
        method: "DELETE",
        headers: authHeaders(),
      });
    }
    setFolderMenuConv(null);
    fetchConversations();
    fetchFolders();
  };

  // ---------- Render ----------

  const tabItems: { key: ConversationStatus; label: string }[] = [
    { key: "active", label: "Activas" },
    { key: "pinned", label: "Fijadas" },
    { key: "archived", label: "Archivadas" },
  ];

  return (
    <AppLayout>
      <div className="flex min-h-full flex-col text-on-surface">
        <InternalPageHeader
          icon={<History className="w-5 h-5 text-primary" />}
          eyebrow="Consultas"
          title="Historial"
          description="Revisá conversaciones, carpetas y estados sin romper la jerarquía del shell privado."
          utilitySlot={<div className="hidden md:flex"><ShellUtilityActions /></div>}
        />

        <div className="w-full px-4 py-6 sm:px-6 xl:px-8 flex gap-5 xl:gap-6">
          {/* Sidebar */}
          <aside className="w-60 shrink-0 space-y-3 xl:w-64">
            {/* Folders section */}
            <div className="panel-base rounded-xl overflow-hidden">
              <button
                onClick={() => setFoldersExpanded((v) => !v)}
                className="w-full flex items-center justify-between px-3 py-2.5 text-sm font-medium text-on-surface hover:bg-surface-container transition-colors"
              >
                <span className="flex items-center gap-2">
                  <Folder className="w-3.5 h-3.5 text-primary" />
                  Carpetas
                </span>
                <ChevronRight
                  className={`w-3.5 h-3.5 text-on-surface/30 transition-transform ${foldersExpanded ? "rotate-90" : ""}`}
                />
              </button>

              {foldersExpanded && (
                <div className="pb-2">
                  <button
                    onClick={() => setActiveFolderFilter(null)}
                    className={`w-full flex items-center gap-2 px-3 py-1.5 text-sm transition-colors ${
                      activeFolderFilter === null
                        ? "text-primary bg-primary/10"
                        : "text-on-surface/60 hover:text-on-surface hover:bg-surface-container"
                    }`}
                  >
                    <FolderOpen className="w-3.5 h-3.5 shrink-0" />
                    <span className="truncate">Todas</span>
                  </button>

                  {folders.map((folder) => (
                    <div key={folder.id} className="group flex items-center gap-1 px-1">
                      <button
                        onClick={() =>
                          setActiveFolderFilter(
                            activeFolderFilter === folder.id ? null : folder.id
                          )
                        }
                        className={`flex-1 flex items-center gap-2 px-2 py-1.5 rounded-lg text-sm transition-colors ${
                          activeFolderFilter === folder.id
                            ? "text-primary bg-primary/10"
                            : "text-on-surface/60 hover:text-on-surface hover:bg-surface-container"
                        }`}
                      >
                        <Folder className="w-3.5 h-3.5 shrink-0" />
                        <span className="truncate flex-1 text-left">{folder.name}</span>
                        <span className="text-xs text-on-surface/30">{folder.conversation_count}</span>
                      </button>
                      <button
                        onClick={() => handleDeleteFolder(folder.id)}
                        disabled={folderActionLoading === folder.id}
                        className="opacity-0 group-hover:opacity-100 p-1 rounded text-on-surface/30 hover:text-[#ffb4ab] transition-all"
                      >
                        {folderActionLoading === folder.id ? (
                          <Loader2 className="w-3 h-3 animate-spin" />
                        ) : (
                          <X className="w-3 h-3" />
                        )}
                      </button>
                    </div>
                  ))}

                  {showNewFolderForm ? (
                    <div className="px-3 pt-1 pb-2 space-y-1.5">
                      <input
                        autoFocus
                        type="text"
                        value={newFolderName}
                        onChange={(e) => setNewFolderName(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === "Enter") handleCreateFolder();
                          if (e.key === "Escape") setShowNewFolderForm(false);
                        }}
                        placeholder="Nombre de carpeta"
                        className="w-full bg-[#35343a] border border-transparent rounded-lg px-2 py-1 text-xs text-on-surface placeholder-on-surface/30 focus:outline-none focus:border-primary transition-colors"
                      />
                      <div className="flex gap-1.5">
                        <button
                          onClick={handleCreateFolder}
                          disabled={folderActionLoading === "create"}
                          className="flex-1 py-1 rounded-lg text-xs bg-primary/15 text-primary hover:bg-primary/25 transition-colors"
                        >
                          {folderActionLoading === "create" ? (
                            <Loader2 className="w-3 h-3 animate-spin mx-auto" />
                          ) : (
                            "Crear"
                          )}
                        </button>
                        <button
                          onClick={() => setShowNewFolderForm(false)}
                          className="px-2 py-1 rounded-lg text-xs text-on-surface/40 hover:text-on-surface transition-colors"
                        >
                          Cancelar
                        </button>
                      </div>
                    </div>
                  ) : (
                    <button
                      onClick={() => setShowNewFolderForm(true)}
                      className="w-full flex items-center gap-2 px-3 py-1.5 text-xs text-on-surface/30 hover:text-on-surface/60 transition-colors"
                    >
                      <Plus className="w-3 h-3" />
                      Nueva carpeta
                    </button>
                  )}
                </div>
              )}
            </div>

            {/* Tags section */}
            <div className="panel-base rounded-xl overflow-hidden">
              <button
                onClick={() => setTagsExpanded((v) => !v)}
                className="w-full flex items-center justify-between px-3 py-2.5 text-sm font-medium text-on-surface hover:bg-surface-container transition-colors"
              >
                <span className="flex items-center gap-2">
                  <Tag className="w-3.5 h-3.5 text-secondary" />
                  Etiquetas
                </span>
                <ChevronRight
                  className={`w-3.5 h-3.5 text-on-surface/30 transition-transform ${tagsExpanded ? "rotate-90" : ""}`}
                />
              </button>

              {tagsExpanded && (
                <div className="pb-2">
                  {activeTagFilter && (
                    <button
                      onClick={() => setActiveTagFilter(null)}
                      className="w-full flex items-center gap-2 px-3 py-1.5 text-sm text-on-surface/60 hover:text-on-surface hover:bg-surface-container transition-colors"
                    >
                      <X className="w-3.5 h-3.5" />
                      Limpiar filtro
                    </button>
                  )}

                  {tags.map((t) =>
                    editingTag?.id === t.id ? (
                      <div key={t.id} className="px-3 py-1.5 space-y-1.5">
                        <input
                          autoFocus
                          type="text"
                          value={editingTag.name}
                          onChange={(e) =>
                            setEditingTag({ ...editingTag, name: e.target.value })
                          }
                          onKeyDown={(e) => {
                            if (e.key === "Enter") handleUpdateTag(editingTag);
                            if (e.key === "Escape") setEditingTag(null);
                          }}
                          className="w-full bg-[#35343a] border border-transparent rounded px-2 py-0.5 text-xs text-on-surface focus:outline-none focus:border-primary transition-colors"
                        />
                        <div className="flex gap-1 flex-wrap">
                          {TAG_COLOR_PRESETS.map((c) => (
                            <button
                              key={c}
                              onClick={() => setEditingTag({ ...editingTag, color: c })}
                              style={{ backgroundColor: c }}
                              className={`w-4 h-4 rounded-full transition-transform ${
                                editingTag.color === c ? "ring-2 ring-white/50 scale-110" : ""
                              }`}
                            />
                          ))}
                        </div>
                        <div className="flex gap-1">
                          <button
                            onClick={() => handleUpdateTag(editingTag)}
                            disabled={tagActionLoading === t.id}
                            className="flex-1 py-0.5 rounded text-xs bg-primary/15 text-primary hover:bg-primary/25"
                          >
                            {tagActionLoading === t.id ? (
                              <Loader2 className="w-3 h-3 animate-spin mx-auto" />
                            ) : (
                              "Guardar"
                            )}
                          </button>
                          <button
                            onClick={() => setEditingTag(null)}
                            className="px-2 py-0.5 rounded text-xs text-on-surface/40 hover:text-on-surface"
                          >
                            X
                          </button>
                        </div>
                      </div>
                    ) : (
                      <div key={t.id} className="group flex items-center gap-1 px-1">
                        <button
                          onClick={() =>
                            setActiveTagFilter(activeTagFilter === t.id ? null : t.id)
                          }
                          className={`flex-1 flex items-center gap-2 px-2 py-1.5 rounded-lg text-sm transition-colors ${
                            activeTagFilter === t.id
                              ? "bg-surface-container"
                              : "hover:bg-surface-container"
                          }`}
                        >
                          <span
                            className="w-2.5 h-2.5 rounded-full shrink-0"
                            style={{ backgroundColor: t.color }}
                          />
                          <span className="truncate text-on-surface">{t.name}</span>
                        </button>
                        <button
                          onClick={() => setEditingTag({ ...t })}
                          className="opacity-0 group-hover:opacity-100 p-1 rounded text-on-surface/30 hover:text-on-surface transition-all"
                        >
                          <Edit2 className="w-3 h-3" />
                        </button>
                        <button
                          onClick={() => handleDeleteTag(t.id)}
                          disabled={tagActionLoading === t.id}
                          className="opacity-0 group-hover:opacity-100 p-1 rounded text-on-surface/30 hover:text-[#ffb4ab] transition-all"
                        >
                          {tagActionLoading === t.id ? (
                            <Loader2 className="w-3 h-3 animate-spin" />
                          ) : (
                            <X className="w-3 h-3" />
                          )}
                        </button>
                      </div>
                    )
                  )}

                  {showNewTagForm ? (
                    <div className="px-3 pt-1 pb-2 space-y-1.5">
                      <input
                        autoFocus
                        type="text"
                        value={newTagName}
                        onChange={(e) => setNewTagName(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === "Enter") handleCreateTag();
                          if (e.key === "Escape") setShowNewTagForm(false);
                        }}
                        placeholder="Nombre de etiqueta"
                        className="w-full bg-[#35343a] border border-transparent rounded-lg px-2 py-1 text-xs text-on-surface placeholder-on-surface/30 focus:outline-none focus:border-primary transition-colors"
                      />
                      <div className="flex gap-1.5 flex-wrap">
                        {TAG_COLOR_PRESETS.map((c) => (
                          <button
                            key={c}
                            onClick={() => setNewTagColor(c)}
                            style={{ backgroundColor: c }}
                            className={`w-5 h-5 rounded-full transition-transform ${
                              newTagColor === c ? "ring-2 ring-white/50 scale-110" : ""
                            }`}
                          />
                        ))}
                      </div>
                      <div className="flex gap-1.5">
                        <button
                          onClick={handleCreateTag}
                          disabled={tagActionLoading === "create"}
                          className="flex-1 py-1 rounded-lg text-xs bg-primary/15 text-primary hover:bg-primary/25 transition-colors"
                        >
                          {tagActionLoading === "create" ? (
                            <Loader2 className="w-3 h-3 animate-spin mx-auto" />
                          ) : (
                            "Crear"
                          )}
                        </button>
                        <button
                          onClick={() => setShowNewTagForm(false)}
                          className="px-2 py-1 rounded-lg text-xs text-on-surface/40 hover:text-on-surface transition-colors"
                        >
                          Cancelar
                        </button>
                      </div>
                    </div>
                  ) : (
                    <button
                      onClick={() => setShowNewTagForm(true)}
                      className="w-full flex items-center gap-2 px-3 py-1.5 text-xs text-on-surface/30 hover:text-on-surface/60 transition-colors"
                    >
                      <Plus className="w-3 h-3" />
                      Nueva etiqueta
                    </button>
                  )}
                </div>
              )}
            </div>
          </aside>

          {/* Main content */}
          <div className="flex-1 min-w-0 space-y-4">
            {/* Search + Sort row */}
            <div className="flex flex-col sm:flex-row gap-3">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-on-surface/30" />
                <input
                  type="text"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Buscar conversaciones..."
                  className="w-full bg-surface-container-low border border-[rgba(79,70,51,0.15)] rounded-lg pl-9 pr-4 py-2.5 text-sm text-on-surface placeholder-on-surface/30 focus:outline-none focus:border-primary transition-colors"
                />
              </div>
              <div className="relative">
                <select
                  value={sortKey}
                  onChange={(e) => setSortKey(e.target.value as SortKey)}
                  className="appearance-none bg-surface-container-low border border-[rgba(79,70,51,0.15)] rounded-lg px-3 py-2.5 pr-8 text-sm text-on-surface focus:outline-none focus:border-primary cursor-pointer transition-colors"
                >
                  <option value="date_desc">Mas recientes</option>
                  <option value="date_asc">Mas antiguas</option>
                  <option value="area">Por area</option>
                  <option value="messages">Por mensajes</option>
                </select>
                <ChevronDown className="absolute right-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-on-surface/30 pointer-events-none" />
              </div>
            </div>

            {/* Active filters indicator */}
            {(activeTagFilter || activeFolderFilter) && (
              <div className="flex items-center gap-2 text-xs text-on-surface/40">
                <span>Filtrando por:</span>
                {activeTagFilter && (
                  <span
                    className="flex items-center gap-1 px-2 py-0.5 rounded-lg bg-surface-container-low border border-[rgba(79,70,51,0.15)] cursor-pointer hover:bg-surface-container transition-colors"
                    onClick={() => setActiveTagFilter(null)}
                  >
                    <span
                      className="w-2 h-2 rounded-full"
                      style={{
                        backgroundColor: tags.find((t) => t.id === activeTagFilter)?.color,
                      }}
                    />
                    {tags.find((t) => t.id === activeTagFilter)?.name}
                    <X className="w-3 h-3" />
                  </span>
                )}
                {activeFolderFilter && (
                  <span
                    className="flex items-center gap-1 px-2 py-0.5 rounded-lg bg-surface-container-low border border-[rgba(79,70,51,0.15)] cursor-pointer hover:bg-surface-container transition-colors"
                    onClick={() => setActiveFolderFilter(null)}
                  >
                    <Folder className="w-3 h-3" />
                    {folders.find((f) => f.id === activeFolderFilter)?.name}
                    <X className="w-3 h-3" />
                  </span>
                )}
              </div>
            )}

            {/* Tabs */}
            <div className="flex gap-0 border-b border-[rgba(79,70,51,0.15)]">
              {tabItems.map(({ key, label }) => (
                <button
                  key={key}
                  onClick={() => setTab(key)}
                  className={`px-5 py-2.5 text-sm font-medium transition-colors relative ${
                    tab === key
                      ? "text-primary border-b-2 border-primary -mb-px"
                      : "text-on-surface/60 hover:text-on-surface border-b-2 border-transparent -mb-px"
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>

            {/* Bulk action bar */}
            {filtered.length > 0 && (
              <div className="flex items-center gap-3 text-sm">
                <button
                  onClick={selectAll}
                  className="flex items-center gap-1.5 text-on-surface/40 hover:text-on-surface transition-colors"
                >
                  {selected.size === filtered.length && filtered.length > 0 ? (
                    <CheckSquare className="w-4 h-4 text-primary" />
                  ) : (
                    <Square className="w-4 h-4" />
                  )}
                  {selected.size > 0 ? `${selected.size} seleccionadas` : "Seleccionar todas"}
                </button>

                {selected.size > 0 && (
                  <div className="flex items-center gap-2 ml-2 px-3 py-1.5 bg-surface-container-low border border-[rgba(79,70,51,0.15)] rounded-lg">
                    <button
                      onClick={() => bulkAction("archive")}
                      disabled={bulkLoading}
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-surface hover:bg-surface-container text-on-surface transition-colors disabled:opacity-50"
                    >
                      {bulkLoading ? (
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      ) : (
                        <Archive className="w-3.5 h-3.5" />
                      )}
                      Archivar
                    </button>
                    <button
                      onClick={() => bulkAction("delete")}
                      disabled={bulkLoading}
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-[#ffb4ab]/30 text-[#ffb4ab] hover:bg-[#93000a]/20 transition-colors disabled:opacity-50"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                      Eliminar
                    </button>
                  </div>
                )}
              </div>
            )}

            {/* Conversation list */}
            {loading ? (
              <div className="flex items-center justify-center py-20">
                <Loader2 className="w-6 h-6 text-primary animate-spin" />
              </div>
            ) : filtered.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-20 text-center">
                <Image
                  src="/brand/logo-full.png"
                  className="w-24 mx-auto mb-4 opacity-20"
                  alt="Logo"
                  width={96}
                  height={96}
                />
                <p className="text-on-surface/40 text-sm">
                  {search || activeTagFilter || activeFolderFilter
                    ? "No hay resultados para tu busqueda."
                    : "No hay conversaciones aqui."}
                </p>
                {tab === "archived" && (
                  <button
                    onClick={() => setTab("active")}
                    className="mt-3 text-primary text-sm hover:text-primary-container flex items-center gap-1 transition-colors"
                  >
                    <RotateCcw className="w-3.5 h-3.5" />
                    Ver conversaciones activas
                  </button>
                )}
              </div>
            ) : (
              <div className="space-y-0">
                {filtered.map((conv, idx) => {
                  const isSelected = selected.has(conv.id);
                  const areaLabel = conv.legal_area
                    ? AREA_LABELS[conv.legal_area] ?? conv.legal_area
                    : null;
                  const unassignedTags = tags.filter(
                    (t) => !conv.tags.some((ct) => ct.id === t.id)
                  );

                  return (
                    <div
                      key={conv.id}
                      className={`group relative flex items-start gap-3 p-4 transition-all cursor-pointer ${
                        isSelected
                          ? "bg-primary/5"
                          : idx % 2 === 0 ? "bg-surface" : "bg-surface-container-low"
                      } hover:bg-surface-container`}
                      onClick={() => router.push(`/?conversation=${conv.id}`)}
                    >
                      {/* Checkbox */}
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          toggleSelect(conv.id);
                        }}
                        className="mt-0.5 text-on-surface/20 hover:text-primary transition-colors shrink-0"
                      >
                        {isSelected ? (
                          <CheckSquare className="w-4 h-4 text-primary" />
                        ) : (
                          <Square className="w-4 h-4" />
                        )}
                      </button>

                      {/* Content */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-start justify-between gap-3">
                          <div className="min-w-0 flex-1">
                            <div className="flex items-center gap-2 flex-wrap">
                              {conv.is_pinned && (
                                <Pin className="w-3 h-3 text-primary shrink-0" />
                              )}
                              {conv.folder_name && (
                                <span className="flex items-center gap-1 text-xs text-on-surface/30">
                                  <Folder className="w-3 h-3" />
                                  {conv.folder_name}
                                </span>
                              )}
                              <h3 className="text-sm font-medium text-on-surface truncate">
                                {conv.title ?? "Consulta sin titulo"}
                              </h3>
                            </div>
                            <div className="flex items-center gap-3 mt-1.5 flex-wrap">
                              {areaLabel && (
                                <span className="bg-secondary-container text-secondary text-[10px] uppercase tracking-widest rounded px-2 py-0.5">
                                  {areaLabel}
                                </span>
                              )}
                              <span className="text-xs text-on-surface/30 flex items-center gap-1">
                                <MessageSquare className="w-3 h-3" />
                                {conv.message_count} mensajes
                              </span>
                              <span className="text-xs text-on-surface/30">
                                {formatDate(conv.updated_at)}
                              </span>
                              {conv.is_shared && (
                                <span className="text-xs text-secondary/50">Compartida</span>
                              )}
                            </div>

                            {/* Tag pills on card */}
                            {(conv.tags.length > 0 || true) && (
                              <div
                                className="flex items-center gap-1.5 mt-2 flex-wrap"
                                onClick={(e) => e.stopPropagation()}
                              >
                                {conv.tags.map((t) => (
                                  <span
                                    key={t.id}
                                    className="flex items-center gap-1 px-1.5 py-0.5 rounded text-xs cursor-pointer hover:opacity-75 transition-opacity"
                                    style={{
                                      backgroundColor: t.color + "22",
                                      color: t.color,
                                      border: `1px solid ${t.color}55`,
                                    }}
                                    onClick={() => handleRemoveTag(conv.id, t.id)}
                                    title="Click para quitar"
                                  >
                                    {t.name}
                                    <X className="w-2.5 h-2.5" />
                                  </span>
                                ))}

                                {unassignedTags.length > 0 && (
                                  <div className="relative">
                                    <button
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        setTagDropdownConv(
                                          tagDropdownConv === conv.id ? null : conv.id
                                        );
                                      }}
                                      className="flex items-center gap-0.5 px-1.5 py-0.5 rounded text-xs text-on-surface/30 border border-[rgba(79,70,51,0.15)] hover:text-on-surface/60 hover:border-primary/20 transition-colors opacity-0 group-hover:opacity-100"
                                    >
                                      <Tag className="w-2.5 h-2.5" />
                                      <Plus className="w-2.5 h-2.5" />
                                    </button>
                                    {tagDropdownConv === conv.id && (
                                      <div
                                        className="absolute left-0 top-6 z-20 bg-surface-container-low border border-[rgba(79,70,51,0.15)] rounded-lg shadow-lg shadow-black/40 min-w-[140px] py-1"
                                        onClick={(e) => e.stopPropagation()}
                                      >
                                        {unassignedTags.map((t) => (
                                          <button
                                            key={t.id}
                                            onClick={() => handleAssignTag(conv.id, t.id)}
                                            className="w-full flex items-center gap-2 px-3 py-1.5 text-sm text-on-surface hover:bg-surface-container transition-colors"
                                          >
                                            <span
                                              className="w-2.5 h-2.5 rounded-full shrink-0"
                                              style={{ backgroundColor: t.color }}
                                            />
                                            {t.name}
                                          </button>
                                        ))}
                                      </div>
                                    )}
                                  </div>
                                )}
                              </div>
                            )}
                          </div>

                          {/* Actions */}
                          <div
                            className="flex items-center gap-1 shrink-0 opacity-0 group-hover:opacity-100 transition-opacity"
                            onClick={(e) => e.stopPropagation()}
                          >
                            <ActionButton
                              title={conv.is_pinned ? "Desfijar" : "Fijar"}
                              loading={actionLoading === conv.id + "pin"}
                              onClick={() => apiAction(conv.id, "pin")}
                              icon={<Pin className={`w-3.5 h-3.5 ${conv.is_pinned ? "text-primary" : ""}`} />}
                            />
                            <ActionButton
                              title={conv.is_archived ? "Desarchivar" : "Archivar"}
                              loading={actionLoading === conv.id + "archive"}
                              onClick={() => apiAction(conv.id, "archive")}
                              icon={<Archive className="w-3.5 h-3.5" />}
                            />

                            {/* Move to folder button */}
                            <div className="relative">
                              <ActionButton
                                title="Mover a carpeta"
                                loading={false}
                                onClick={() =>
                                  setFolderMenuConv(
                                    folderMenuConv === conv.id ? null : conv.id
                                  )
                                }
                                icon={<FolderInput className="w-3.5 h-3.5" />}
                              />
                              {folderMenuConv === conv.id && (
                                <div
                                  className="absolute right-0 top-7 z-20 bg-surface-container-low border border-[rgba(79,70,51,0.15)] rounded-lg shadow-lg shadow-black/40 min-w-[160px] py-1"
                                  onClick={(e) => e.stopPropagation()}
                                >
                                  <p className="px-3 py-1 text-xs text-on-surface/30 font-medium">
                                    Mover a carpeta
                                  </p>
                                  {conv.folder_id && (
                                    <button
                                      onClick={() => handleMoveToFolder(conv.id, null)}
                                      className="w-full flex items-center gap-2 px-3 py-1.5 text-sm text-on-surface/60 hover:bg-surface-container transition-colors"
                                    >
                                      <X className="w-3.5 h-3.5" />
                                      Quitar de carpeta
                                    </button>
                                  )}
                                  {folders.map((f) => (
                                    <button
                                      key={f.id}
                                      onClick={() => handleMoveToFolder(conv.id, f.id)}
                                      className={`w-full flex items-center gap-2 px-3 py-1.5 text-sm hover:bg-surface-container transition-colors ${
                                        conv.folder_id === f.id
                                          ? "text-primary"
                                          : "text-on-surface"
                                      }`}
                                    >
                                      <Folder className="w-3.5 h-3.5 shrink-0" />
                                      <span className="truncate">{f.name}</span>
                                      {conv.folder_id === f.id && (
                                        <Check className="w-3 h-3 ml-auto text-primary" />
                                      )}
                                    </button>
                                  ))}
                                  {folders.length === 0 && (
                                    <p className="px-3 py-2 text-xs text-on-surface/30">
                                      No hay carpetas creadas
                                    </p>
                                  )}
                                </div>
                              )}
                            </div>

                            <ActionButton
                              title={copiedId === conv.id ? "Enlace copiado" : "Compartir"}
                              loading={actionLoading === conv.id + "share"}
                              onClick={() => handleShare(conv.id)}
                              icon={
                                copiedId === conv.id ? (
                                  <Check className="w-3.5 h-3.5 text-[#6ee7b7]" />
                                ) : (
                                  <Share2 className="w-3.5 h-3.5" />
                                )
                              }
                            />
                            <ActionButton
                              title="Eliminar"
                              loading={actionLoading === conv.id + ""}
                              onClick={() => handleDelete(conv.id)}
                              icon={<Trash2 className="w-3.5 h-3.5 text-[#ffb4ab]" />}
                              danger
                            />
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </div>
    </AppLayout>
  );
}

interface ActionButtonProps {
  title: string;
  loading: boolean;
  onClick: () => void;
  icon: React.ReactNode;
  danger?: boolean;
}

function ActionButton({ title, loading, onClick, icon, danger }: ActionButtonProps) {
  return (
    <button
      title={title}
      onClick={onClick}
      disabled={loading}
      className={`p-1.5 rounded-lg transition-colors disabled:opacity-50 ${
        danger
          ? "hover:bg-[#93000a]/20 text-on-surface/30 hover:text-[#ffb4ab]"
          : "hover:bg-[#35343a] text-on-surface/30 hover:text-on-surface"
      }`}
    >
      {loading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : icon}
    </button>
  );
}
