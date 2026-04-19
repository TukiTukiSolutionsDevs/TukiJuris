import type React from "react";
import {
  BookOpen,
  Shield,
  Briefcase,
  Calculator,
  Landmark,
  Building2,
  Store,
  FileCheck,
  Globe,
  TreePine,
  Heart,
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
    { label: "Despido justificado", query: "Cuales son los requisitos para un despido justificado?" },
    { label: "CTS", query: "Como se calcula la CTS en Peru?" },
    { label: "Art. 1351 CC", query: "Que dice el Art. 1351 del Codigo Civil?" },
    { label: "Prescripcion penal", query: "Plazos de prescripcion en derecho penal" },
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
  { id: "civil", name: "Civil", label: "Derecho Civil", description: "Contratos, daños, bienes y obligaciones", icon: BookOpen, color: "text-blue-400" },
  { id: "penal", name: "Penal", label: "Derecho Penal", description: "Delitos, denuncias y responsabilidad penal", icon: Shield, color: "text-red-400" },
  { id: "laboral", name: "Laboral", label: "Derecho Laboral", description: "Trabajo, despidos e indemnizaciones", icon: Briefcase, color: "text-green-400" },
  { id: "tributario", name: "Tributario", label: "Derecho Tributario", description: "Impuestos y obligaciones fiscales", icon: Calculator, color: "text-yellow-400" },
  { id: "constitucional", name: "Constitucional", label: "Derecho Constitucional", description: "Derechos fundamentales y garantías", icon: Landmark, color: "text-purple-400" },
  { id: "administrativo", name: "Administrativo", label: "Derecho Administrativo", description: "Trámites, sanciones y organismos públicos", icon: Building2, color: "text-orange-400" },
  { id: "corporativo", name: "Corporativo", label: "Derecho Comercial", description: "Empresas, sociedades y actividad comercial", icon: Store, color: "text-cyan-400" },
  { id: "registral", name: "Registral", label: "Derecho Registral", description: "Inscripciones, títulos y registros", icon: FileCheck, color: "text-pink-400" },
  { id: "comercio_exterior", name: "Comercio Ext.", label: "Comercio Exterior", description: "Operaciones internacionales y aduanas", icon: Globe, color: "text-teal-400" },
  { id: "compliance", name: "Compliance", label: "Compliance / Ambiental", description: "Normativas, controles y riesgo regulatorio", icon: TreePine, color: "text-indigo-400" },
  { id: "competencia", name: "Competencia/PI", label: "Competencia / Propiedad Intelectual", description: "Marcas, patentes y competencia desleal", icon: Heart, color: "text-amber-400" },
];
