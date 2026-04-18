import { PublicLayout } from "@/components/public/PublicLayout";

export default function OnboardingLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <PublicLayout hideFooter>{children}</PublicLayout>;
}
