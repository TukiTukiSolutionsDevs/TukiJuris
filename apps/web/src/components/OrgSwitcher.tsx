"use client";

// ---------------------------------------------------------------------------
// OrgSwitcher — purely presentational organization selector.
// Hidden when orgs.length <= 1 (single-org users see no change).
// Does NOT handle its own data fetching or persistence.
// ---------------------------------------------------------------------------

interface OrgOption {
  id: string;
  name: string;
}

interface OrgSwitcherProps {
  orgs: OrgOption[];
  selectedOrgId: string;
  onChange: (orgId: string) => void;
}

export function OrgSwitcher({ orgs, selectedOrgId, onChange }: OrgSwitcherProps) {
  if (orgs.length <= 1) return null;

  return (
    <select
      aria-label="Cambiar organización"
      value={selectedOrgId}
      onChange={(e) => onChange(e.target.value)}
      className="text-xs bg-surface-container-low border border-on-surface/20 rounded-lg px-3 py-1.5 text-on-surface cursor-pointer focus:outline-none focus:ring-1 focus:ring-primary"
    >
      {orgs.map((org) => (
        <option key={org.id} value={org.id}>
          {org.name}
        </option>
      ))}
    </select>
  );
}
