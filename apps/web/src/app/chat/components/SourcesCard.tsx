"use client";

import type { Citation } from "../types";

// ---------------------------------------------------------------------------
// SourcesCard — numbered citations list, Notion-editorial style.
// Uses `.c-sources` CSS namespace. Maps our existing Citation shape
// (`{ type, text, reference }`) to the design shape (`{ tag, label, kind }`).
// ---------------------------------------------------------------------------

type Kind = "norma" | "jurisprudencia" | "doctrina";

function normalizeKind(type: string | undefined): Kind {
  if (!type) return "norma";
  const t = type.toLowerCase();
  if (t.includes("juris") || t.includes("cas") || t.includes("sentenc")) return "jurisprudencia";
  if (t.includes("doctrin")) return "doctrina";
  return "norma";
}

function deriveTag(citation: Citation): string {
  // Prefer a short code from `reference`, fall back to first word of `text`.
  const ref = citation.reference?.trim();
  if (ref) {
    // If it looks like "Art. 36" or "D.S. 003-97-TR" keep the prefix.
    const firstToken = ref.split(/\s+/)[0].replace(/[.,:;]$/, "");
    if (firstToken.length <= 8) return firstToken;
    return ref.slice(0, 8);
  }
  const first = citation.text?.trim().split(/\s+/)[0];
  return first ? first.slice(0, 8) : "Doc.";
}

interface SourcesCardProps {
  citations: Citation[];
  /** Max sources to render inline; remainder shown under a "+N más" affordance. */
  limit?: number;
}

export function SourcesCard({ citations, limit = 20 }: SourcesCardProps) {
  if (!citations || citations.length === 0) return null;
  const visible = citations.slice(0, limit);

  return (
    <aside className="c-sources">
      <div className="c-sources__label">Fuentes citadas</div>
      <ol className="c-sources__list">
        {visible.map((cit, idx) => {
          const kind = normalizeKind(cit.type);
          const tag = deriveTag(cit);
          const label = cit.text || cit.reference || "Fuente";
          return (
            <li key={idx} className={`c-source c-source--${kind}`}>
              <span className="c-source__num">{idx + 1}</span>
              <span className="c-source__tag">{tag}</span>
              <span className="c-source__label" title={cit.text}>
                {label}
              </span>
              <span className="c-source__kind">{kind}</span>
            </li>
          );
        })}
      </ol>
    </aside>
  );
}
