import Link from "next/link";
import Image from "next/image";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Libro de Reclamaciones | TukiJuris",
  description:
    "Libro de Reclamaciones virtual de TukiJuris — TukiTuki Solutions SAC (RUC 20613614509), conforme a la Ley 29571.",
};

function LegalHeader() {
  return (
    <header
      className="fixed top-0 left-0 right-0 z-50 bg-surface/80 backdrop-blur-md"
      style={{ borderBottom: "1px solid rgba(79, 70, 51, 0.15)" }}
    >
      <div className="max-w-7xl mx-auto px-4 lg:px-8 h-16 flex items-center justify-between">
        <Link href="/landing" className="flex items-center">
          <Image src="/brand/logo-tj-full.png" alt="TukiJuris" width={120} height={40} className="h-10 w-auto" />
        </Link>
        <div className="flex items-center gap-3">
          <Link
            href="/auth/login"
            className="text-sm text-on-surface/60 hover:text-on-surface transition-colors px-3 py-2"
          >
            Iniciar sesión
          </Link>
        </div>
      </div>
    </header>
  );
}

export default function LibroReclamacionesPage() {
  return (
    <div className="min-h-screen bg-background text-on-surface font-['Manrope']">
      <LegalHeader />

      <main className="max-w-3xl mx-auto px-4 lg:px-8 pt-28 pb-20">
        <div className="mb-10">
          <span className="block text-primary text-xs uppercase tracking-[0.2em] font-bold mb-4">
            Atención al consumidor
          </span>
          <h1 className="font-['Newsreader'] text-3xl sm:text-4xl font-bold text-on-surface mb-3">
            Libro de Reclamaciones
          </h1>
          <p className="text-sm text-on-surface/60">
            Conforme al Código de Protección y Defensa del Consumidor (Ley 29571) y su Reglamento
            (D.S. N° 011-2011-PCM).
          </p>
        </div>

        <section className="mb-10 text-on-surface-variant text-sm leading-relaxed space-y-3">
          <p>
            <strong className="text-on-surface">Proveedor:</strong> TukiTuki Solutions SAC
          </p>
          <p>
            <strong className="text-on-surface">RUC:</strong> 20613614509
          </p>
          <p>
            <strong className="text-on-surface">Servicio reclamado:</strong> TukiJuris
            (plataforma SaaS de asistencia jurídica)
          </p>
        </section>

        <section className="mb-10">
          <h2 className="font-['Newsreader'] text-xl font-bold text-primary mb-3">
            ¿Cómo presentar tu reclamo?
          </h2>
          <p className="text-sm text-on-surface-variant leading-relaxed mb-4">
            Envíanos un correo a{" "}
            <a href="mailto:reclamos@tukijuris.com.pe" className="text-primary hover:underline">
              reclamos@tukijuris.com.pe
            </a>{" "}
            con la siguiente información:
          </p>
          <ul className="list-disc list-inside space-y-1 ml-2 text-sm text-on-surface-variant">
            <li>Nombre completo y documento de identidad</li>
            <li>Dirección y datos de contacto (teléfono y correo)</li>
            <li>
              Tipo: <strong className="text-on-surface">Reclamo</strong> (disconformidad relacionada
              al servicio) o <strong className="text-on-surface">Queja</strong> (malestar respecto
              a la atención).
            </li>
            <li>Detalle de los hechos y fecha en la que ocurrieron</li>
            <li>Tu pedido o pretensión concreta</li>
          </ul>
        </section>

        <section className="mb-10">
          <h2 className="font-['Newsreader'] text-xl font-bold text-primary mb-3">
            Plazo de respuesta
          </h2>
          <p className="text-sm text-on-surface-variant leading-relaxed">
            Tu reclamo o queja será atendido por escrito en un plazo máximo de{" "}
            <strong className="text-on-surface">30 días calendario</strong> desde su recepción, de
            conformidad con el artículo 24 del Código del Consumidor.
          </p>
        </section>

        <section className="mb-10">
          <h2 className="font-['Newsreader'] text-xl font-bold text-primary mb-3">
            ¿No quedaste satisfecho con la respuesta?
          </h2>
          <p className="text-sm text-on-surface-variant leading-relaxed">
            Puedes acudir a INDECOPI, autoridad nacional de protección al consumidor del Perú, a
            través de su portal:{" "}
            <a
              href="https://www.consumidor.gob.pe/"
              target="_blank"
              rel="noopener noreferrer"
              className="text-primary hover:underline"
            >
              consumidor.gob.pe
            </a>
            .
          </p>
        </section>

        <div
          className="p-4 rounded-lg bg-primary/5 mb-10"
          style={{ border: "1px solid rgba(255,209,101,0.15)" }}
        >
          <p className="text-on-surface-variant text-xs">
            Nota: este Libro de Reclamaciones cumple la función del Libro físico exigido por la Ley
            29571. La presentación electrónica tiene plena validez legal según el artículo 8 del
            D.S. N° 011-2011-PCM.
          </p>
        </div>
      </main>
    </div>
  );
}
