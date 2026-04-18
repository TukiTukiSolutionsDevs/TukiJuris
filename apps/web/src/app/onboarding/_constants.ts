import {
  BookOpen,
  Shield,
  Briefcase,
  Landmark,
  Gavel,
  Building2,
  ScrollText,
  FileCheck,
  Globe,
  Lock,
  BadgeCheck,
} from "lucide-react";

export const TOTAL_STEPS = 5;

export const STEP_LABELS = [
  "Bienvenida",
  "Perfil",
  "Organización",
  "API Key",
  "Listo",
];

export const STEP_ILLUSTRATIONS = [
  "/onboarding/welcome.png",
  "/onboarding/profile.png",
  "/onboarding/organization.png",
  "/onboarding/apikey.png",
  "/onboarding/complete.png",
];

export const ROLES = [
  { id: "abogado", label: "Abogado" },
  { id: "paralegal", label: "Paralegal" },
  { id: "estudiante", label: "Estudiante de Derecho" },
  { id: "corporativo", label: "Equipo Legal Corporativo" },
  { id: "otro", label: "Otro" },
];

export const LEGAL_AREAS = [
  { id: "civil", name: "Civil", icon: BookOpen },
  { id: "penal", name: "Penal", icon: Shield },
  { id: "laboral", name: "Laboral", icon: Briefcase },
  { id: "tributario", name: "Tributario", icon: Landmark },
  { id: "constitucional", name: "Constitucional", icon: Gavel },
  { id: "administrativo", name: "Administrativo", icon: Building2 },
  { id: "corporativo", name: "Corporativo", icon: ScrollText },
  { id: "registral", name: "Registral", icon: FileCheck },
  { id: "comercio_exterior", name: "Comercio Exterior", icon: Globe },
  { id: "compliance", name: "Compliance", icon: Lock },
  { id: "competencia", name: "Competencia / PI", icon: BadgeCheck },
];

export interface AIProvider {
  id: string;
  name: string;
  models: string[];
  placeholder: string;
  dashboardUrl: string;
}

export const AI_PROVIDERS: AIProvider[] = [
  {
    id: "openai",
    name: "OpenAI",
    models: ["GPT-4o", "GPT-4o Mini"],
    placeholder: "sk-...",
    dashboardUrl: "https://platform.openai.com/api-keys",
  },
  {
    id: "anthropic",
    name: "Anthropic",
    models: ["Claude Sonnet 4", "Claude 3.5 Haiku"],
    placeholder: "sk-ant-...",
    dashboardUrl: "https://console.anthropic.com/settings/keys",
  },
  {
    id: "google",
    name: "Google AI",
    models: ["Gemini 2.5 Flash", "Gemini 3.1 Pro Preview"],
    placeholder: "AIza...",
    dashboardUrl: "https://aistudio.google.com/app/apikey",
  },
  {
    id: "deepseek",
    name: "DeepSeek",
    models: ["DeepSeek V3", "DeepSeek Reasoner"],
    placeholder: "sk-...",
    dashboardUrl: "https://platform.deepseek.com/api_keys",
  },
];

export const SUGGESTED_QUERIES_BY_AREA: Record<string, string> = {
  civil: "Que dice el Art. 1969 del Codigo Civil sobre responsabilidad civil?",
  penal: "Cuales son los elementos del delito de estafa en Peru?",
  laboral: "Como se calcula la CTS para un trabajador a tiempo completo?",
  tributario:
    "Cuales son los regimenes tributarios disponibles para una MYPE?",
  constitucional: "Cuando procede interponer un recurso de habeas corpus?",
  administrativo: "Que es el silencio administrativo positivo y negativo?",
  corporativo: "Cuales son los requisitos para constituir una SAC en Peru?",
  registral: "Como se inscribe una hipoteca en Registros Publicos?",
  comercio_exterior: "En que consiste el regimen de drawback en aduanas?",
  compliance: "Que empresas estan obligadas a tener un sistema SPLAFT?",
  competencia: "Como se registra una marca ante INDECOPI?",
};

export function slugify(text: string): string {
  return text
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
}
