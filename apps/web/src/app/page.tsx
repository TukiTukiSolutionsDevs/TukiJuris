// Root entry point — redirects straight to the unified case-analysis flow.
// The legacy streaming chat at this path was retired in favour of /analizar,
// which uses the intake → investigation → analysis state machine.
import { redirect } from "next/navigation";

export default function RootPage() {
  redirect("/analizar");
}
