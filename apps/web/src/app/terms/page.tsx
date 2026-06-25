import Link from "next/link";
import Image from "next/image";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Términos y Condiciones | TukiJuris",
  description: "Términos y condiciones de uso de la plataforma TukiJuris.",
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
          <Image src="/brand/logo-tj-full.png" alt="TukiJuris" width={120} height={40} className="h-10 w-auto" />
        </Link>
        <div className="flex items-center gap-3">
          <Link
            href="/auth/login"
            className="text-sm text-on-surface/60 hover:text-on-surface transition-colors px-3 py-2"
          >
            Iniciar sesión
          </Link>
          <Link
            href="/auth/register"
            className="text-sm font-bold rounded-lg h-11 px-6 flex items-center transition-opacity hover:opacity-90 whitespace-nowrap text-on-primary"
            style={{ background: "linear-gradient(135deg, var(--gold-gradient-from) 0%, var(--gold-gradient-to) 100%)" }}
          >
            Comenzar gratis
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
          <Link href="/terms" className="hover:text-primary transition-colors">Términos</Link>
          <Link href="/privacy" className="hover:text-primary transition-colors">Privacidad</Link>
          <Link href="/libro-reclamaciones" className="hover:text-primary transition-colors">Libro de Reclamaciones</Link>
          <Link href="/landing" className="hover:text-primary transition-colors">Inicio</Link>
        </nav>
      </div>
    </footer>
  );
}

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
            Términos y Condiciones de Uso
          </h1>
          <p className="text-sm text-on-surface/50">
            Última actualización: 31 de mayo de 2026
          </p>
          <div className="mt-4 h-px bg-gradient-to-r from-primary/30 to-transparent" />
        </div>

        <Section title="1. Identificación del prestador">
          <p>
            La plataforma <strong className="text-on-surface">TukiJuris</strong> es operada por{" "}
            <strong className="text-on-surface">TukiTuki Solutions SAC</strong>, identificada con RUC{" "}
            <strong className="text-on-surface">20613614509</strong>, sociedad anónima cerrada con
            domicilio fiscal en la República del Perú.
          </p>
          <p>
            Contacto: <a href="mailto:soporte@tukijuris.com.pe" className="text-primary hover:underline">soporte@tukijuris.com.pe</a>
          </p>
        </Section>

        <Section title="2. Aceptación de los términos">
          <p>
            Al registrarte, acceder o utilizar TukiJuris, aceptas estos términos en su totalidad.
            Si no estás de acuerdo, debes abstenerte de usar la plataforma.
          </p>
          <p>
            TukiTuki Solutions SAC se reserva el derecho de modificar estos términos. Los cambios
            materiales se notificarán con al menos <strong className="text-on-surface">30 días</strong>{" "}
            de anticipación a través de la plataforma o por correo electrónico. La fecha de
            actualización siempre estará visible al inicio de este documento. El uso continuado
            tras el plazo de aviso implica la aceptación de los cambios.
          </p>
        </Section>

        <Section title="3. Descripción del servicio">
          <p>
            TukiJuris es una plataforma de asistencia jurídica basada en inteligencia artificial,
            especializada en derecho peruano. Ofrece:
          </p>
          <ul className="list-disc list-inside space-y-1 ml-2">
            <li>Consultas legales asistidas por IA en 29 áreas del derecho peruano</li>
            <li>Búsqueda normativa y jurisprudencial con citas directas</li>
            <li>Análisis de documentos legales</li>
            <li>API para integraciones de terceros (plan Profesional y Estudio)</li>
          </ul>
        </Section>

        <Section title="4. Naturaleza de las respuestas — exclusión de responsabilidad">
          <div
            className="p-4 rounded-lg bg-primary/5 mb-4"
            style={{ border: "1px solid rgba(255,209,101,0.15)" }}
          >
            <p className="text-primary font-medium text-sm">
              TukiJuris NO constituye un estudio de abogados, NO presta asesoría legal vinculante,
              y NO reemplaza la consulta con un abogado colegiado.
            </p>
          </div>
          <p>
            Las respuestas generadas por la plataforma son <strong className="text-on-surface">orientativas y de
            carácter informativo</strong>. Pueden contener errores, omisiones o información desactualizada.
            El usuario es el único responsable de las decisiones legales que tome basándose en la
            información proporcionada.
          </p>
          <p>
            TukiTuki Solutions SAC no será responsable por daños directos, indirectos, incidentales
            o consecuentes derivados del uso o la imposibilidad de uso de la plataforma.
          </p>
        </Section>

        <Section title="5. Modelo BYOK (Bring Your Own Key)">
          <p>
            TukiJuris permite el modelo BYOK: el usuario puede proporcionar sus propias claves de
            API de proveedores de inteligencia artificial (OpenAI, Google, Anthropic, entre otros).
          </p>
          <ul className="list-disc list-inside space-y-1 ml-2">
            <li>Las claves son cifradas en reposo con Fernet (AES) y jamás son expuestas a terceros.</li>
            <li>
              El costo de uso de los modelos de IA bajo BYOK corre por cuenta exclusiva del
              usuario, según las tarifas de cada proveedor.
            </li>
            <li>
              TukiTuki Solutions SAC no es responsable por cargos generados en las cuentas de
              proveedores de IA del usuario.
            </li>
          </ul>
        </Section>

        <Section title="6. Registro y cuentas">
          <p>
            Para utilizar TukiJuris, el usuario debe crear una cuenta proporcionando información
            veraz y completa. El usuario es responsable de:
          </p>
          <ul className="list-disc list-inside space-y-1 ml-2">
            <li>Mantener la confidencialidad de sus credenciales de acceso</li>
            <li>Toda actividad realizada bajo su cuenta</li>
            <li>Notificar inmediatamente cualquier uso no autorizado</li>
          </ul>
          <p>
            TukiTuki Solutions SAC se reserva el derecho de suspender o cancelar cuentas que
            violen estos términos o que presenten actividad sospechosa.
          </p>
        </Section>

        <Section title="7. Planes, pagos y cancelación">
          <p>
            TukiJuris ofrece un plan gratuito y planes de pago (Profesional y Estudio). Los detalles
            de cada plan están disponibles en{" "}
            <Link href="/precios" className="text-primary hover:underline">/precios</Link>.
          </p>
          <ul className="list-disc list-inside space-y-1 ml-2">
            <li>
              Los pagos del plan Profesional se procesan a través de la pasarela{" "}
              <strong className="text-on-surface">Culqi</strong> (Perú). El plan Estudio se acuerda
              de forma personalizada con el equipo de ventas.
            </li>
            <li>
              Las suscripciones se renuevan automáticamente cada mes salvo cancelación expresa por
              parte del usuario.
            </li>
            <li>
              <strong className="text-on-surface">Cancelación:</strong> el usuario puede cancelar
              la renovación automática en cualquier momento desde{" "}
              <Link href="/billing" className="text-primary hover:underline">/billing</Link>.
              La cancelación es efectiva al final del período facturado: el servicio se mantiene
              hasta esa fecha y no se realizan nuevos cargos.
            </li>
            <li>
              <strong className="text-on-surface">Reembolsos:</strong> al tratarse de un servicio
              digital prestado de forma continua, no se realizan reembolsos por períodos
              parcialmente utilizados. Si hubiera un cargo erróneo (cobro duplicado, falla técnica
              imputable a TukiJuris), se devolverá íntegramente vía Culqi.
            </li>
            <li>
              Los precios pueden ser modificados con al menos 30 días de aviso previo. El usuario
              tiene derecho a cancelar antes de que la modificación entre en vigor.
            </li>
          </ul>
        </Section>

        <Section title="8. Uso aceptable">
          <p>El usuario se compromete a NO utilizar TukiJuris para:</p>
          <ul className="list-disc list-inside space-y-1 ml-2">
            <li>Actividades ilegales o fraudulentas</li>
            <li>Intentar acceder a datos de otros usuarios</li>
            <li>Realizar ingeniería inversa, descompilar o desensamblar la plataforma</li>
            <li>Sobrecargar intencionalmente los servidores o la API</li>
            <li>Revender el acceso a la plataforma sin autorización</li>
            <li>Generar contenido que viole derechos de terceros</li>
          </ul>
        </Section>

        <Section title="9. Propiedad intelectual">
          <p>
            Todo el software, diseño, marcas, logotipos, textos y contenido de TukiJuris son
            propiedad exclusiva de TukiTuki Solutions SAC o sus licenciantes.
          </p>
          <p>
            El código fuente de TukiJuris está protegido por derechos de autor. Su uso,
            reproducción, distribución o modificación sin autorización expresa está prohibido.
          </p>
          <p>
            El contenido generado por la IA a partir de las consultas del usuario puede ser
            utilizado libremente por el usuario, bajo su propia responsabilidad.
          </p>
        </Section>

        <Section title="10. Disponibilidad del servicio">
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

        <Section title="11. Limitación de responsabilidad">
          <p>
            En la máxima medida permitida por la ley peruana, la responsabilidad total de TukiTuki
            Solutions SAC frente al usuario por cualquier concepto no excederá el monto total
            pagado por el usuario en los 12 meses anteriores al evento que genere la reclamación.
          </p>
        </Section>

        <Section title="12. Libro de Reclamaciones">
          <p>
            En cumplimiento del Código de Protección y Defensa del Consumidor (Ley 29571), TukiJuris
            pone a disposición del usuario su Libro de Reclamaciones virtual en{" "}
            <Link href="/libro-reclamaciones" className="text-primary hover:underline">
              /libro-reclamaciones
            </Link>.
          </p>
          <p>
            Cualquier reclamo o queja será atendido por el área de Atención al Cliente en un plazo
            máximo de 30 días calendario desde su presentación, conforme a la ley.
          </p>
        </Section>

        <Section title="13. Legislación aplicable y jurisdicción">
          <p>
            Estos términos se rigen por las leyes de la República del Perú. Para cualquier
            controversia derivada del uso de TukiJuris, las partes se someten a la jurisdicción
            de los juzgados y tribunales de Lima, Perú.
          </p>
        </Section>

        <Section title="14. Contacto">
          <p>
            Para consultas sobre estos términos:{" "}
            <a href="mailto:legal@tukijuris.com.pe" className="text-primary hover:underline">
              legal@tukijuris.com.pe
            </a>
          </p>
          <p>
            Para soporte general:{" "}
            <a href="mailto:soporte@tukijuris.com.pe" className="text-primary hover:underline">
              soporte@tukijuris.com.pe
            </a>
          </p>
        </Section>
      </main>

      <LegalFooter />
    </div>
  );
}
