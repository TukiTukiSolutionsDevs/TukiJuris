import Link from "next/link";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Terminos y Condiciones | TukiJuris",
  description: "Terminos y condiciones de uso de la plataforma TukiJuris.",
};

// ─────────────────────────────────────────────
// Legal header/footer shared between terms/privacy
// ─────────────────────────────────────────────
function LegalHeader() {
  return (
    <header
      className="fixed top-0 left-0 right-0 z-50 bg-surface/80 backdrop-blur-md"
      style={{ borderBottom: "1px solid rgba(79, 70, 51, 0.15)" }}
    >
      <div className="max-w-7xl mx-auto px-4 lg:px-8 h-16 flex items-center justify-between">
        <Link href="/landing" className="flex items-center">
          <img src="/brand/logo-full.png" alt="TukiJuris" className="h-10 w-auto" />
        </Link>
        <div className="flex items-center gap-3">
          <Link
            href="/auth/login"
            className="text-sm text-on-surface/60 hover:text-on-surface transition-colors px-3 py-2"
          >
            Iniciar Sesion
          </Link>
          <Link
            href="/auth/register"
            className="text-sm font-bold rounded-lg h-11 px-6 flex items-center transition-opacity hover:opacity-90 whitespace-nowrap text-on-primary"
            style={{ background: "linear-gradient(135deg, var(--gold-gradient-from) 0%, var(--gold-gradient-to) 100%)" }}
          >
            Comenzar Gratis
          </Link>
        </div>
      </div>
    </header>
  );
}

function LegalFooter() {
  return (
    <footer
      className="bg-background py-8 px-4 lg:px-8"
      style={{ borderTop: "1px solid rgba(79, 70, 51, 0.15)" }}
    >
      <div className="max-w-4xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-on-surface/60 uppercase tracking-widest">
        <span>&copy; 2026 TukiJuris — TukiTuki Solutions SAC. Todos los derechos reservados.</span>
        <nav className="flex gap-4">
          <Link href="/terms" className="hover:text-primary transition-colors">Terminos</Link>
          <Link href="/privacy" className="hover:text-primary transition-colors">Privacidad</Link>
          <Link href="/landing" className="hover:text-primary transition-colors">Inicio</Link>
        </nav>
      </div>
    </footer>
  );
}

// ─────────────────────────────────────────────
// Section helpers
// ─────────────────────────────────────────────
function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="mb-10">
      <h2 className="font-['Newsreader'] text-xl font-bold text-primary mb-3">{title}</h2>
      <div className="space-y-3 text-on-surface-variant text-sm leading-relaxed">{children}</div>
    </section>
  );
}

// ─────────────────────────────────────────────
// Page
// ─────────────────────────────────────────────
export default function TermsPage() {
  return (
    <div className="min-h-screen bg-background text-on-surface font-['Manrope']">
      <LegalHeader />

      <main className="max-w-4xl mx-auto px-4 lg:px-8 pt-28 pb-20">
        {/* Title */}
        <div className="mb-12">
          <span className="block text-primary text-xs uppercase tracking-[0.2em] font-bold mb-4">
            Legal
          </span>
          <h1 className="font-['Newsreader'] text-3xl sm:text-4xl font-bold text-on-surface mb-3">
            Terminos y Condiciones de Uso
          </h1>
          <p className="text-sm text-on-surface/50">
            Ultima actualizacion: 9 de abril de 2026
          </p>
          <div className="mt-4 h-px bg-gradient-to-r from-primary/30 to-transparent" />
        </div>

        {/* Content */}
        <Section title="1. Identificacion del Prestador">
          <p>
            La plataforma <strong className="text-on-surface">TukiJuris</strong> es operada por{" "}
            <strong className="text-on-surface">TukiTuki Solutions SAC</strong>, identificada con RUC{" "}
            <strong className="text-on-surface">20613614509</strong>, consultora de software con
            domicilio en la Republica del Peru.
          </p>
          <p>
            Contacto: <a href="mailto:soporte@tukijuris.net.pe" className="text-primary hover:underline">soporte@tukijuris.net.pe</a>
          </p>
        </Section>

        <Section title="2. Aceptacion de los Terminos">
          <p>
            Al registrarse, acceder o utilizar TukiJuris, el usuario acepta estos terminos en su
            totalidad. Si no esta de acuerdo, debe abstenerse de usar la plataforma.
          </p>
          <p>
            TukiTuki Solutions SAC se reserva el derecho de modificar estos terminos en cualquier
            momento. Los cambios seran publicados en esta pagina con la fecha de actualizacion. El uso
            continuado de la plataforma implica la aceptacion de las modificaciones.
          </p>
        </Section>

        <Section title="3. Descripcion del Servicio">
          <p>
            TukiJuris es una plataforma de asistencia juridica basada en inteligencia artificial,
            especializada en derecho peruano. Ofrece:
          </p>
          <ul className="list-disc list-inside space-y-1 ml-2">
            <li>Consultas legales asistidas por IA en 11 areas del derecho peruano</li>
            <li>Busqueda normativa y jurisprudencial con citas directas</li>
            <li>Analisis de casos legales</li>
            <li>API para integraciones de terceros</li>
          </ul>
        </Section>

        <Section title="4. Naturaleza de las Respuestas — Exclusion de Responsabilidad">
          <div
            className="p-4 rounded-lg bg-primary/5 mb-4"
            style={{ border: "1px solid rgba(255,209,101,0.15)" }}
          >
            <p className="text-primary font-medium text-sm">
              TukiJuris NO constituye un estudio de abogados, NO presta asesoria legal, y NO
              reemplaza la consulta con un abogado colegiado.
            </p>
          </div>
          <p>
            Las respuestas generadas por la plataforma son orientativas y de caracter informativo.
            Pueden contener errores, omisiones o informacion desactualizada. El usuario es el unico
            responsable de las decisiones legales que tome basandose en la informacion proporcionada.
          </p>
          <p>
            TukiTuki Solutions SAC no sera responsable por danos directos, indirectos, incidentales
            o consecuentes derivados del uso o la imposibilidad de uso de la plataforma.
          </p>
        </Section>

        <Section title="5. Modelo BYOK (Bring Your Own Key)">
          <p>
            TukiJuris opera bajo el modelo BYOK: el usuario proporciona sus propias claves de API
            de proveedores de inteligencia artificial (OpenAI, Google, Anthropic, entre otros).
          </p>
          <ul className="list-disc list-inside space-y-1 ml-2">
            <li>Las claves son cifradas en reposo y jamas son expuestas a terceros.</li>
            <li>
              El costo de uso de los modelos de IA corre por cuenta exclusiva del usuario, segun
              las tarifas de cada proveedor.
            </li>
            <li>
              TukiTuki Solutions SAC no es responsable por cargos generados en las cuentas de
              proveedores de IA del usuario.
            </li>
          </ul>
        </Section>

        <Section title="6. Registro y Cuentas">
          <p>
            Para utilizar TukiJuris, el usuario debe crear una cuenta proporcionando informacion
            veraz y completa. El usuario es responsable de:
          </p>
          <ul className="list-disc list-inside space-y-1 ml-2">
            <li>Mantener la confidencialidad de sus credenciales de acceso</li>
            <li>Toda actividad realizada bajo su cuenta</li>
            <li>Notificar inmediatamente cualquier uso no autorizado</li>
          </ul>
          <p>
            TukiTuki Solutions SAC se reserva el derecho de suspender o cancelar cuentas que
            violen estos terminos o que presenten actividad sospechosa.
          </p>
        </Section>

        <Section title="7. Planes y Pagos">
          <p>
            TukiJuris ofrece planes gratuitos y de pago. Los detalles de cada plan, incluyendo
            precios, limites y funcionalidades, estan disponibles en la seccion de precios de la
            plataforma.
          </p>
          <ul className="list-disc list-inside space-y-1 ml-2">
            <li>Los pagos se procesan a traves de pasarelas de pago seguras.</li>
            <li>Las suscripciones se renuevan automaticamente salvo cancelacion expresa.</li>
            <li>No se realizan reembolsos por periodos parcialmente utilizados.</li>
            <li>Los precios pueden ser modificados con 30 dias de aviso previo.</li>
          </ul>
        </Section>

        <Section title="8. Uso Aceptable">
          <p>El usuario se compromete a NO utilizar TukiJuris para:</p>
          <ul className="list-disc list-inside space-y-1 ml-2">
            <li>Actividades ilegales o fraudulentas</li>
            <li>Intentar acceder a datos de otros usuarios</li>
            <li>Realizar ingenieria inversa, descompilar o desensamblar la plataforma</li>
            <li>Sobrecargar intencionalmente los servidores o la API</li>
            <li>Revender el acceso a la plataforma sin autorizacion</li>
            <li>Generar contenido que viole derechos de terceros</li>
          </ul>
        </Section>

        <Section title="9. Propiedad Intelectual">
          <p>
            Todo el software, diseno, marcas, logotipos, textos y contenido de TukiJuris son
            propiedad exclusiva de TukiTuki Solutions SAC o sus licenciantes.
          </p>
          <p>
            El codigo fuente de TukiJuris esta protegido por derechos de autor. Su uso,
            reproduccion, distribucion o modificacion sin autorizacion expresa esta prohibido.
          </p>
          <p>
            El contenido generado por la IA a partir de las consultas del usuario puede ser
            utilizado libremente por el usuario, bajo su propia responsabilidad.
          </p>
        </Section>

        <Section title="10. Disponibilidad del Servicio">
          <p>
            TukiTuki Solutions SAC se esfuerza por mantener la plataforma disponible de forma
            continua, pero no garantiza disponibilidad ininterrumpida. El servicio puede verse
            afectado por:
          </p>
          <ul className="list-disc list-inside space-y-1 ml-2">
            <li>Mantenimiento programado o de emergencia</li>
            <li>Fallas en proveedores de infraestructura o de IA</li>
            <li>Eventos de fuerza mayor</li>
          </ul>
        </Section>

        <Section title="11. Limitacion de Responsabilidad">
          <p>
            En la maxima medida permitida por la ley peruana, la responsabilidad total de TukiTuki
            Solutions SAC frente al usuario por cualquier concepto no excedera el monto total pagado
            por el usuario en los 12 meses anteriores al evento que genere la reclamacion.
          </p>
        </Section>

        <Section title="12. Legislacion Aplicable y Jurisdiccion">
          <p>
            Estos terminos se rigen por las leyes de la Republica del Peru. Para cualquier
            controversia derivada del uso de TukiJuris, las partes se someten a la jurisdiccion
            de los juzgados y tribunales de Lima, Peru.
          </p>
        </Section>

        <Section title="13. Contacto">
          <p>
            Para consultas sobre estos terminos, contactar a:{" "}
            <a href="mailto:legal@tukijuris.net.pe" className="text-primary hover:underline">
              legal@tukijuris.net.pe
            </a>
          </p>
        </Section>
      </main>

      <LegalFooter />
    </div>
  );
}
