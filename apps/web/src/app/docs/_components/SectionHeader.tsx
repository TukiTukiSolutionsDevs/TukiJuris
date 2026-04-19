interface SectionHeaderProps {
  title: string;
  subtitle?: string;
}

export function SectionHeader({ title, subtitle }: SectionHeaderProps) {
  return (
    <div className="mb-6">
      <h2 className="font-['Newsreader'] text-2xl font-bold text-on-surface mb-1">{title}</h2>
      {subtitle && <p className="text-on-surface/50 text-sm">{subtitle}</p>}
      <div className="mt-3 h-px bg-gradient-to-r from-primary/30 to-transparent" />
    </div>
  );
}
