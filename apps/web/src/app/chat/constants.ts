import type React from "react";
import {
  Banknote,
  BookOpen,
  Briefcase,
  Building2,
  Calculator,
  ClipboardSignature,
  FileCheck,
  Fuel,
  Globe,
  Heart,
  HeartPulse,
  Landmark,
  Leaf,
  Lightbulb,
  Lock,
  Pickaxe,
  Scale,
  Shield,
  ShieldCheck,
  ShoppingCart,
  Stamp,
  Store,
  TrendingUp,
  TreePine,
  Truck,
  Users,
  Wifi,
} from "lucide-react";

// ---------------------------------------------------------------------------
// Query templates
// ---------------------------------------------------------------------------
export const QUERY_TEMPLATES: Record<string, { label: string; query: string }[]> = {
  laboral: [
    { label: "Despido justificado", query: "Cuales son los requisitos legales para un despido justificado segun el DS 003-97-TR?" },
    { label: "Calculo CTS", query: "Como se calcula la Compensacion por Tiempo de Servicios en Peru?" },
    { label: "Vacaciones", query: "Cuales son los derechos de vacaciones segun el DL 713?" },
    { label: "Horas extras", query: "Como se calcula el pago de horas extras en Peru?" },
  ],
  penal: [
    { label: "Prescripcion", query: "Cuales son los plazos de prescripcion en materia penal?" },
    { label: "Legitima defensa", query: "Requisitos de la legitima defensa en el Codigo Penal peruano" },
    { label: "Medidas cautelares", query: "Cuando procede la detencion preventiva segun el CPP peruano?" },
    { label: "Principio de legalidad", query: "Como se aplica el principio de legalidad en el derecho penal peruano?" },
  ],
  civil: [
    { label: "Responsabilidad civil", query: "Que establece el Art. 1969 del Codigo Civil sobre responsabilidad extracontractual?" },
    { label: "Contratos", query: "Requisitos de validez de un contrato segun el Codigo Civil peruano" },
    { label: "Prescripcion civil", query: "Cuales son los plazos de prescripcion en materia civil?" },
    { label: "Daños y perjuicios", query: "Como se determina la indemnizacion por danos y perjuicios en Peru?" },
  ],
  tributario: [
    { label: "Impuesto a la Renta", query: "Cuales son las categorias del Impuesto a la Renta en Peru?" },
    { label: "IGV", query: "Que operaciones estan gravadas con el IGV?" },
    { label: "Infracciones SUNAT", query: "Cuales son las principales infracciones tributarias y sus multas?" },
    { label: "Regimenes tributarios", query: "Que regimenes tributarios existen para empresas en Peru?" },
  ],
  constitucional: [
    { label: "Habeas corpus", query: "Cuando procede el habeas corpus segun el Tribunal Constitucional?" },
    { label: "Derechos fundamentales", query: "Cuales son los derechos fundamentales en la Constitucion peruana?" },
    { label: "Amparo", query: "Que es la accion de amparo y cuando procede en Peru?" },
    { label: "Bloque constitucional", query: "Que comprende el bloque de constitucionalidad en Peru?" },
  ],
  administrativo: [
    { label: "Silencio administrativo", query: "Que es el silencio administrativo positivo y negativo en Peru?" },
    { label: "Recursos administrativos", query: "Cuales son los recursos administrativos en la LPAG?" },
    { label: "Acto administrativo", query: "Cuales son los requisitos de validez de un acto administrativo?" },
    { label: "Contrataciones Estado", query: "Cuales son las modalidades de contratacion del Estado peruano?" },
  ],
  general: [
    // Scenario-style starters: describe a real situation so the agent can
    // ask follow-ups and build a case analysis. NOT one-shot legal lookups.
    {
      label: "Despido injustificado",
      query: "Hace 3 años trabajo en una empresa privada con contrato firmado. Hoy me despidieron sin causa y sin pagarme nada. ¿Qué puedo hacer?",
    },
    {
      label: "Acoso laboral",
      query: "Mi jefe me grita y discrimina hace meses delante de mis compañeros. Tengo capturas de WhatsApp y hay testigos. ¿Cómo procedo?",
    },
    {
      label: "Conflicto vecinal",
      query: "Mi vecino construyó una pared invadiendo parte de mi terreno. Tengo escritura inscrita en SUNARP. ¿Qué pasos sigo?",
    },
    {
      label: "Multa SUNAT",
      query: "Recibí una resolución de SUNAT con una multa que no entiendo y tengo 20 días para responder. Ayúdame a evaluar mi caso.",
    },
  ],
};

// ---------------------------------------------------------------------------
// Legal areas
// ---------------------------------------------------------------------------
export interface LegalArea {
  id: string;
  name: string;
  label: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
  color: string;
}

export const LEGAL_AREAS: LegalArea[] = [
  // Núcleo
  { id: "civil", name: "Civil", label: "Derecho Civil", description: "Contratos, daños, bienes y obligaciones", icon: BookOpen, color: "text-blue-400" },
  { id: "familia", name: "Familia", label: "Derecho de Familia", description: "Divorcio, alimentos, tenencia, violencia familiar", icon: Users, color: "text-rose-400" },
  { id: "penal", name: "Penal", label: "Derecho Penal", description: "Delitos, denuncias y responsabilidad penal", icon: Shield, color: "text-red-400" },
  { id: "procesal", name: "Procesal", label: "Derecho Procesal", description: "Procesos judiciales, recursos y cautelares", icon: Scale, color: "text-slate-400" },
  { id: "laboral", name: "Laboral", label: "Derecho Laboral", description: "Trabajo, despidos e indemnizaciones", icon: Briefcase, color: "text-green-400" },
  { id: "seguridad_social", name: "Seg. Social", label: "Seguridad Social", description: "ONP, AFP, EsSalud y pensiones", icon: ShieldCheck, color: "text-emerald-400" },
  { id: "tributario", name: "Tributario", label: "Derecho Tributario", description: "Impuestos y obligaciones fiscales", icon: Calculator, color: "text-yellow-400" },
  { id: "constitucional", name: "Constitucional", label: "Derecho Constitucional", description: "Derechos fundamentales y garantías", icon: Landmark, color: "text-purple-400" },
  { id: "administrativo", name: "Administrativo", label: "Derecho Administrativo", description: "Trámites, sanciones y organismos públicos", icon: Building2, color: "text-orange-400" },
  { id: "corporativo", name: "Corporativo", label: "Derecho Corporativo", description: "Empresas, sociedades y M&A", icon: Store, color: "text-cyan-400" },
  { id: "comercial", name: "Comercial", label: "Derecho Comercial", description: "Títulos valores, arbitraje, sistema concursal", icon: Store, color: "text-sky-400" },
  { id: "registral", name: "Registral", label: "Derecho Registral", description: "Inscripciones, títulos y registros", icon: FileCheck, color: "text-pink-400" },
  { id: "notarial", name: "Notarial", label: "Derecho Notarial", description: "Escrituras públicas y fe pública", icon: Stamp, color: "text-fuchsia-400" },
  // Económico-regulatorio
  { id: "competencia", name: "Competencia", label: "Libre Competencia", description: "Antitrust, competencia desleal y fusiones", icon: Heart, color: "text-amber-400" },
  { id: "consumidor", name: "Consumidor", label: "Protección al Consumidor", description: "Código de Consumo (29571) e INDECOPI", icon: ShoppingCart, color: "text-lime-400" },
  { id: "propiedad_intelectual", name: "PI", label: "Propiedad Intelectual", description: "Marcas, patentes, derechos de autor", icon: Lightbulb, color: "text-yellow-300" },
  { id: "datos_personales", name: "Datos", label: "Datos Personales", description: "Ley 29733, ANPDP y privacidad", icon: Lock, color: "text-indigo-400" },
  { id: "compliance", name: "Compliance", label: "Compliance / Anticorrupción", description: "PLAFT, anticorrupción y Ley 30424", icon: TreePine, color: "text-violet-400" },
  // Económico
  { id: "comercio_exterior", name: "Com. Ext.", label: "Comercio Exterior", description: "Operaciones internacionales y aduanas", icon: Globe, color: "text-teal-400" },
  { id: "financiero", name: "Financiero", label: "Financiero / Banca", description: "SBS, sistema financiero, créditos", icon: Banknote, color: "text-emerald-300" },
  { id: "mercado_valores", name: "Mercado Val.", label: "Mercado de Valores", description: "SMV, ofertas públicas, bolsa", icon: TrendingUp, color: "text-blue-300" },
  { id: "seguros", name: "Seguros", label: "Seguros", description: "Contrato de seguro y régimen SBS", icon: ShieldCheck, color: "text-cyan-300" },
  // Sectoriales
  { id: "ambiental", name: "Ambiental", label: "Ambiental", description: "MINAM, OEFA, SEIA, recursos hídricos", icon: Leaf, color: "text-green-500" },
  { id: "minero", name: "Minero", label: "Minero", description: "Concesiones, cierre de minas, MAPE", icon: Pickaxe, color: "text-stone-400" },
  { id: "hidrocarburos", name: "Hidroc.", label: "Hidrocarburos y Energía", description: "Gas, petróleo, eléctrico, OSINERGMIN", icon: Fuel, color: "text-orange-300" },
  { id: "telecom", name: "Telecom", label: "Telecomunicaciones", description: "OSIPTEL, espectro y banda ancha", icon: Wifi, color: "text-blue-500" },
  { id: "transporte", name: "Transporte", label: "Transporte y Tránsito", description: "MTC, ATU, SUTRAN, licencias", icon: Truck, color: "text-yellow-500" },
  { id: "salud", name: "Salud", label: "Derecho Sanitario", description: "MINSA, DIGEMID, SUSALUD, farmacéuticos", icon: HeartPulse, color: "text-red-300" },
  // Estado
  { id: "contrataciones_estado", name: "Contrat. Estado", label: "Contrataciones del Estado", description: "Nueva LCE (32069), OSCE/OECE, TCE", icon: ClipboardSignature, color: "text-orange-500" },
];

// ---------------------------------------------------------------------------
// Derived map: id → short label (name).
// Use this when you need a `Record<string, string>` instead of the full array
// (e.g. AreaChip, historial, compartido). Keep it derived so it stays in sync.
// ---------------------------------------------------------------------------
export const AREA_LABELS: Record<string, string> = Object.fromEntries(
  LEGAL_AREAS.map((a) => [a.id, a.name])
);

// id → full descriptive label (e.g. for tooltips, headings)
export const AREA_FULL_LABELS: Record<string, string> = Object.fromEntries(
  LEGAL_AREAS.map((a) => [a.id, a.label])
);

// id → hex color (used in chart/analytics surfaces that can't read Tailwind classes).
// Hex chosen to roughly match each area's Tailwind `color` token in `LEGAL_AREAS`.
export const AREA_HEX_COLORS: Record<string, string> = {
  civil: "#60a5fa",            // blue-400
  familia: "#fb7185",           // rose-400
  penal: "#f87171",             // red-400
  procesal: "#94a3b8",          // slate-400
  laboral: "#4ade80",           // green-400
  seguridad_social: "#34d399",  // emerald-400
  tributario: "#facc15",        // yellow-400
  constitucional: "#c084fc",    // purple-400
  administrativo: "#fb923c",    // orange-400
  corporativo: "#22d3ee",       // cyan-400
  comercial: "#38bdf8",         // sky-400
  registral: "#f472b6",         // pink-400
  notarial: "#e879f9",          // fuchsia-400
  competencia: "#fbbf24",       // amber-400
  consumidor: "#a3e635",        // lime-400
  propiedad_intelectual: "#fde047", // yellow-300
  datos_personales: "#818cf8",  // indigo-400
  compliance: "#a78bfa",        // violet-400
  comercio_exterior: "#2dd4bf", // teal-400
  financiero: "#6ee7b7",        // emerald-300
  mercado_valores: "#93c5fd",   // blue-300
  seguros: "#67e8f9",           // cyan-300
  ambiental: "#22c55e",         // green-500
  minero: "#a8a29e",            // stone-400
  hidrocarburos: "#fdba74",     // orange-300
  telecom: "#3b82f6",           // blue-500
  transporte: "#eab308",        // yellow-500
  salud: "#fca5a5",             // red-300
  contrataciones_estado: "#f97316", // orange-500
};
