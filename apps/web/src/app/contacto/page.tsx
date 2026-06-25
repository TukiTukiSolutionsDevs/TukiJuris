import Link from "next/link";
import type { Metadata } from "next";
import { PublicLayout } from "@/components/public/PublicLayout";

export const metadata: Metadata = {
  title: "Contacto | TukiJuris",
  description: "Contacta con el equipo de TukiJuris — TukiTuki Solutions SAC.",
};

const CHANNELS = [
  {
    label: "Soporte general",
    email: "soporte@tukijuris.com.pe",
    description: "Dudas de producto, ayuda con tu cuenta, problemas técnicos.",
  },
  {
    label: "Ventas — plan Estudio",
    email: "ventas@tukijuris.com.pe",
    description: "Plan empresarial personalizado para estudios y áreas legales corporativas.",
  },
  {
    label: "Privacidad y datos personales",
    email: "privacidad@tukijuris.com.pe",
    description: "Ejercer derechos ARCO conforme a la Ley 29733.",
  },
  {
    label: "Asuntos legales",
    email: "legal@tukijuris.com.pe",
    description: "Términos, propiedad intelectual, requerimientos formales.",
  },
  {
    label: "Reclamos",
    email: "reclamos@tukijuris.com.pe",
    description: "Libro de Reclamaciones — respuesta en máximo 30 días calendario.",
  },
];

export default function ContactoPage() {
  return (
    <PublicLayout>
      <section className="py-16 sm:py-24 px-4 lg:px-8">
        <div className="max-w-3xl mx-auto">
          <span className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-primary/20 bg-primary/5 text-primary text-xs font-medium uppercase tracking-wider mb-6">
            Contacto
          </span>
          <h1 className="font-headline text-3xl sm:text-5xl font-bold text-on-surface mb-4">
            ¿En qué podemos ayudarte?
          </h1>
          <p className="text-on-surface-variant text-base sm:text-lg mb-10 max-w-2xl">
            Escríbenos al canal más adecuado para tu consulta. Respondemos en horario de oficina
            (lunes a viernes de 9:00 a 18:00, hora de Lima).
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {CHANNELS.map((c) => (
              <div
                key={c.email}
                className="rounded-xl border border-ghost-border bg-surface-container-low p-5 flex flex-col gap-2"
              >
                <span className="text-primary text-xs font-bold uppercase tracking-widest">
                  {c.label}
                </span>
                <a
                  href={`mailto:${c.email}`}
                  className="text-on-surface font-medium hover:text-primary transition-colors text-sm break-all"
                >
                  {c.email}
                </a>
                <p className="text-on-surface-variant text-xs leading-relaxed">{c.description}</p>
              </div>
            ))}
          </div>

          <div className="mt-12 p-6 rounded-xl border border-ghost-border bg-surface-container-low">
            <h2 className="font-headline text-xl font-bold text-on-surface mb-3">
              Datos del prestador
            </h2>
            <p className="text-sm text-on-surface-variant leading-relaxed">
              <strong className="text-on-surface">TukiTuki Solutions SAC</strong>
              <br />
              RUC 20613614509
              <br />
              República del Perú
            </p>
            <p className="mt-4 text-xs text-on-surface/60">
              Para reclamos formales conforme a la Ley 29571, visita el{" "}
              <Link href="/libro-reclamaciones" className="text-primary hover:underline">
                Libro de Reclamaciones
              </Link>
              .
            </p>
          </div>
        </div>
      </section>
    </PublicLayout>
  );
}
