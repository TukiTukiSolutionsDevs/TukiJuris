"use client";

/**
 * FeatureGate — declarative wrapper for entitlement-gated UI.
 *
 * Usage patterns:
 *
 * 1. Simple hide/show:
 *    <FeatureGate feature="pdf_export">
 *      <ExportButton />
 *    </FeatureGate>
 *
 * 2. Locked visible preview that opens upsell on click:
 *    <FeatureGate feature="file_upload" lockedVariant={<DisabledUploadButton />}>
 *      <UploadButton />
 *    </FeatureGate>
 *
 * 3. Custom fallback (no upsell):
 *    <FeatureGate feature="team_seats" fallback={<p>Solo en planes de equipo</p>}>
 *      <TeamSettings />
 *    </FeatureGate>
 *
 * Design decisions:
 * - Default behaviour with no access: render nothing (null).
 * - lockedVariant: rendered with reduced opacity + click-to-upsell wrapper.
 * - Never REMOVES locked content entirely when lockedVariant is provided —
 *   users see what they're missing, not a blank space.
 */

import { ReactNode, useState } from "react";
import { useHasFeature } from "@/lib/auth/AuthContext";
import { UpsellModal } from "@/components/UpsellModal";

interface FeatureGateProps {
  /** Feature key to check (e.g. 'pdf_export', 'byok_enabled'). */
  feature: string;
  /** Content shown when the user has access. */
  children: ReactNode;
  /**
   * Optional fallback rendered when access is denied AND no lockedVariant.
   * Defaults to null (render nothing).
   */
  fallback?: ReactNode;
  /**
   * When provided, rendered in locked state (dimmed + click opens upsell).
   * Use this to show a disabled preview of the gated feature.
   */
  lockedVariant?: ReactNode;
}

export function FeatureGate({
  feature,
  children,
  fallback = null,
  lockedVariant,
}: FeatureGateProps) {
  const allowed = useHasFeature(feature);
  const [upsellOpen, setUpsellOpen] = useState(false);

  if (allowed) return <>{children}</>;

  if (lockedVariant) {
    return (
      <>
        <div
          onClick={() => setUpsellOpen(true)}
          className="cursor-pointer opacity-50 select-none"
          title="Función de plan superior — click para más info"
          role="button"
          tabIndex={0}
          onKeyDown={(e) => e.key === "Enter" && setUpsellOpen(true)}
        >
          {lockedVariant}
        </div>
        {upsellOpen && (
          <UpsellModal feature={feature} onClose={() => setUpsellOpen(false)} />
        )}
      </>
    );
  }

  return <>{fallback}</>;
}
