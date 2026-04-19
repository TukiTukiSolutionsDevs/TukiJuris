import { AlertCircle, Lightbulb, AlertTriangle, Info } from "lucide-react";

type CalloutVariant = "tip" | "warning" | "info" | "danger";

interface CalloutProps {
  variant?: CalloutVariant;
  title?: string;
  children: React.ReactNode;
}

const VARIANTS: Record<CalloutVariant, { icon: typeof AlertCircle; border: string; bg: string; iconColor: string; titleColor: string }> = {
  tip: {
    icon: Lightbulb,
    border: "rgba(255,209,101,0.25)",
    bg: "bg-primary/5",
    iconColor: "text-primary",
    titleColor: "text-primary",
  },
  warning: {
    icon: AlertTriangle,
    border: "rgba(245,158,11,0.25)",
    bg: "bg-amber-500/5",
    iconColor: "text-amber-400",
    titleColor: "text-amber-400",
  },
  info: {
    icon: Info,
    border: "rgba(59,130,246,0.25)",
    bg: "bg-blue-500/5",
    iconColor: "text-blue-400",
    titleColor: "text-blue-400",
  },
  danger: {
    icon: AlertCircle,
    border: "rgba(239,68,68,0.25)",
    bg: "bg-red-500/5",
    iconColor: "text-red-400",
    titleColor: "text-red-400",
  },
};

export function Callout({ variant = "info", title, children }: CalloutProps) {
  const v = VARIANTS[variant];
  const Icon = v.icon;

  return (
    <div
      className={`flex items-start gap-3 p-4 rounded-lg ${v.bg}`}
      style={{ border: `1px solid ${v.border}` }}
    >
      <Icon className={`w-4 h-4 ${v.iconColor} shrink-0 mt-0.5`} />
      <div className="text-sm text-on-surface/60">
        {title && <strong className={`${v.titleColor} block mb-1`}>{title}</strong>}
        {children}
      </div>
    </div>
  );
}
