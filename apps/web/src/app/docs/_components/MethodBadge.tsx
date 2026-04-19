import type { EndpointMethod } from "../_data/endpoints";

const METHOD_COLORS: Record<EndpointMethod, string> = {
  GET:    "bg-[#10B981]/20 text-[#10B981]",
  POST:   "bg-[#3B82F6]/20 text-[#3B82F6]",
  PUT:    "bg-primary-container/20 text-primary-container",
  DELETE: "bg-[#EF4444]/20 text-[#EF4444]",
};

export function MethodBadge({ method }: { method: EndpointMethod }) {
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-mono font-bold ${METHOD_COLORS[method]}`}>
      {method}
    </span>
  );
}
