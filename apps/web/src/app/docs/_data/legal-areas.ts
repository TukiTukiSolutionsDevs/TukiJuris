import {
  BookOpen,
  Shield,
  Briefcase,
  Landmark,
  Building2,
  ScrollText,
  FileCheck,
  Globe,
  Lock,
  BadgeCheck,
  Gavel,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

export interface LegalArea {
  id: string;
  name: string;
  icon: LucideIcon;
  color: string;
  desc: string;
}

export const LEGAL_AREAS: LegalArea[] = [
  { id: "civil", name: "Derecho Civil", icon: BookOpen, color: "text-blue-400", desc: "Código Civil, CPC, Familia, Sucesiones, Contratos, Obligaciones" },
  { id: "penal", name: "Derecho Penal", icon: Shield, color: "text-red-400", desc: "Código Penal, NCPP, Ejecución Penal" },
  { id: "laboral", name: "Derecho Laboral", icon: Briefcase, color: "text-green-400", desc: "LPCL, Seguridad y Salud, Relaciones Colectivas, CTS, Vacaciones" },
  { id: "tributario", name: "Derecho Tributario", icon: Landmark, color: "text-yellow-400", desc: "Código Tributario, IR, IGV, SUNAT, Procedimientos" },
  { id: "administrativo", name: "Derecho Administrativo", icon: Building2, color: "text-orange-400", desc: "LPAG, Contrataciones del Estado, Procedimientos Sancionadores" },
  { id: "corporativo", name: "Derecho Corporativo", icon: ScrollText, color: "text-cyan-400", desc: "LGS, Mercado de Valores, MYPE, Fusiones y Adquisiciones" },
  { id: "constitucional", name: "Derecho Constitucional", icon: Gavel, color: "text-purple-400", desc: "Constitución 1993, Procesos Constitucionales, TC" },
  { id: "registral", name: "Derecho Registral", icon: FileCheck, color: "text-pink-400", desc: "SUNARP, Registros Públicos, Inscripciones" },
  { id: "competencia", name: "Competencia y PI", icon: BadgeCheck, color: "text-primary", desc: "INDECOPI, Marcas, Patentes, Consumidor, Libre Competencia" },
  { id: "compliance", name: "Compliance", icon: Lock, color: "text-indigo-400", desc: "Datos Personales, Anticorrupción, Lavado de Activos, LAFT" },
  { id: "comercio_exterior", name: "Comercio Exterior", icon: Globe, color: "text-teal-400", desc: "Aduanas, TLC, MINCETUR, Regímenes Aduaneros" },
];
