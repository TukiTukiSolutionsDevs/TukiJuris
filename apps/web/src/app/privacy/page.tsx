import Link from "next/link";
import Image from "next/image";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Política de Privacidad | TukiJuris",
  description: "Política de privacidad y protección de datos de TukiJuris conforme a la Ley 29733 de Perú.",
};

// ─────────────────────────────────────────────
// Shared legal chrome
// ─────────────────────────────────────────────
function LegalHeader() {
  return (
    <header
      className="fixed top-0 left-0 right-0 z-50 bg-surface/80 backdrop-blur-md"
      style={{ borderBottom: "1px solid rgba(79, 70, 51, 0.15)" }}
    >
      <div className="max-w-7xl mx-auto px-4 lg:px-8 h-16 flex items-center justify-between">
        <Link href="/landing" className="flex items-center">
          <Image src="/brand/logo-full.png" alt="TukiJuris" width={120} height={40} className="h-10 w-auto" />
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
export default function PrivacyPage() {
  return (
    <div className="min-h-screen bg-background text-on-surface font-['Manrope']">
      <LegalHeader />

      <main className="max-w-4xl mx-auto px-4 lg:px-8 pt-28 pb-20">
        {/* Title */}
        <div className="mb-12">
          <span className="block text-primary text-xs uppercase tracking-[0.2em] font-bold mb-4">
            Privacidad
          </span>
          <h1 className="font-['Newsreader'] text-3xl sm:text-4xl font-bold text-on-surface mb-3">
            Política de Privacidad
          </h1>
          <p className="text-sm text-on-surface/50">
            Última actualización: 31 de mayo de 2026
          </p>
          <div className="mt-4 h-px bg-gradient-to-r from-primary/30 to-transparent" />
        </div>

        {/* Intro */}
        <div className="mb-10 text-on-surface-variant text-sm leading-relaxed space-y-3">
          <p>
            <strong className="text-on-surface">TukiTuki Solutions SAC</strong> (RUC 20613614509),
            en su calidad de responsable del tratamiento de datos personales, se compromete a
            proteger la privacidad de los usuarios de la plataforma{" "}
            <strong className="text-on-surface">TukiJuris</strong>.
          </p>
          <p>
            Esta política cumple con la Ley N° 29733 — Ley de Protección de Datos Personales del
            Perú y su Reglamento (D.S. N° 003-2013-JUS).
          </p>
        </div>

        <Section title="1. Datos que recopilamos">
          <p>Recopilamos las siguientes categorías de datos:</p>

          <h3 className="text-on-surface font-semibold text-sm mt-4 mb-2">1.1 Datos de registro</h3>
          <ul className="list-disc list-inside space-y-1 ml-2">
            <li>Nombre completo</li>
            <li>Correo electrónico</li>
            <li>Contraseña (almacenada con hash bcrypt, nunca en texto plano)</li>
          </ul>

          <h3 className="text-on-surface font-semibold text-sm mt-4 mb-2">1.2 Datos de uso</h3>
          <ul className="list-disc list-inside space-y-1 ml-2">
            <li>Consultas realizadas a la plataforma</li>
            <li>Áreas del derecho consultadas</li>
            <li>Frecuencia y patrones de uso</li>
            <li>Dirección IP y datos del navegador (User-Agent)</li>
          </ul>

          <h3 className="text-on-surface font-semibold text-sm mt-4 mb-2">1.3 Claves API de terceros (BYOK)</h3>
          <ul className="list-disc list-inside space-y-1 ml-2">
            <li>Las claves API proporcionadas por el usuario son cifradas en reposo con Fernet (AES-128 en modo CBC + HMAC-SHA256).</li>
            <li>Solo se descifran en memoria durante el procesamiento de cada solicitud.</li>
            <li>Jamás se almacenan en logs, se comparten con terceros ni se exponen en la interfaz.</li>
          </ul>

          <h3 className="text-on-surface font-semibold text-sm mt-4 mb-2">1.4 Datos de pago</h3>
          <ul className="list-disc list-inside space-y-1 ml-2">
            <li>
              Los datos de tarjeta de crédito o débito son procesados directamente por la pasarela
              de pagos <strong className="text-on-surface">Culqi</strong>. TukiJuris NO almacena
              números de tarjeta ni códigos CVV en ningún momento.
            </li>
          </ul>
        </Section>

        <Section title="2. Finalidad del tratamiento">
          <p>Los datos personales son tratados para:</p>
          <ul className="list-disc list-inside space-y-1 ml-2">
            <li>Proveer y mantener el servicio de TukiJuris</li>
            <li>Autenticar y gestionar las cuentas de usuario</li>
            <li>Procesar pagos y gestionar suscripciones</li>
            <li>Mejorar la calidad del servicio y los modelos de búsqueda</li>
            <li>Enviar comunicaciones relacionadas con el servicio (actualizaciones, mantenimiento)</li>
            <li>Cumplir con obligaciones legales y tributarias</li>
          </ul>
          <p className="mt-2">
            <strong className="text-on-surface">No vendemos ni compartimos datos personales con
            terceros para fines publicitarios.</strong>
          </p>
        </Section>

        <Section title="3. Base legal del tratamiento">
          <ul className="list-disc list-inside space-y-1 ml-2">
            <li>
              <strong className="text-on-surface">Ejecución contractual:</strong> El tratamiento es
              necesario para prestar el servicio contratado.
            </li>
            <li>
              <strong className="text-on-surface">Consentimiento:</strong> Otorgado al registrarse
              y aceptar estos términos.
            </li>
            <li>
              <strong className="text-on-surface">Obligación legal:</strong> Cumplimiento de la Ley
              29733 y normativa tributaria peruana.
            </li>
          </ul>
        </Section>

        <Section title="4. Compartición de datos con terceros">
          <p>Los datos del usuario pueden ser compartidos con:</p>
          <ul className="list-disc list-inside space-y-1 ml-2">
            <li>
              <strong className="text-on-surface">Proveedores de IA</strong> (OpenAI, Google,
              Anthropic, Groq, DeepSeek y otros): Reciben únicamente el texto de la consulta del
              usuario para generar respuestas. No reciben datos personales identificables del
              usuario más allá del contenido que este decida incluir en la consulta.
            </li>
            <li>
              <strong className="text-on-surface">Pasarela de pagos Culqi:</strong> Procesa datos
              de pago directamente, bajo sus propias políticas de privacidad y certificación PCI-DSS.
            </li>
            <li>
              <strong className="text-on-surface">Proveedores de infraestructura:</strong>{" "}
              Servicios de hosting y base de datos operan bajo acuerdos de confidencialidad.
            </li>
            <li>
              <strong className="text-on-surface">Autoridades competentes:</strong> Cuando sea
              requerido por ley, orden judicial o solicitud formal de la SUNAT o el Ministerio Público.
            </li>
          </ul>
        </Section>

        <Section title="5. Seguridad de los datos">
          <p>Implementamos las siguientes medidas de seguridad:</p>
          <ul className="list-disc list-inside space-y-1 ml-2">
            <li>Cifrado en tránsito (TLS/HTTPS) para todas las comunicaciones</li>
            <li>Cifrado en reposo para claves API (Fernet/AES) y contraseñas (bcrypt)</li>
            <li>Autenticación basada en JWT con refresh-token rotation y detección de reuso</li>
            <li>Rate limiting por IP y por usuario para prevenir abuso</li>
            <li>Logs de acceso y monitoreo de actividad sospechosa</li>
            <li>Backups cifrados de la base de datos</li>
          </ul>
          <div
            className="mt-4 p-4 rounded-lg bg-primary/5"
            style={{ border: "1px solid rgba(255,209,101,0.15)" }}
          >
            <p className="text-primary font-medium text-sm">
              TukiJuris es un software de asistencia jurídica basado en IA, NO un estudio de abogados.
            </p>
            <p className="text-on-surface-variant text-xs mt-1">
              Las consultas realizadas a través de la plataforma NO están protegidas por el
              secreto profesional abogado-cliente. No ingreses información sensible o confidencial
              que requiera dicha protección.
            </p>
          </div>
        </Section>

        <Section title="6. Conservación de datos">
          <ul className="list-disc list-inside space-y-1 ml-2">
            <li>
              <strong className="text-on-surface">Datos de cuenta:</strong> Se conservan mientras
              la cuenta esté activa. Tras la eliminación de cuenta, se eliminan en un plazo de 30 días.
            </li>
            <li>
              <strong className="text-on-surface">Historial de consultas:</strong> Se conserva
              mientras la cuenta esté activa. El usuario puede eliminarlo manualmente.
            </li>
            <li>
              <strong className="text-on-surface">Datos de facturación:</strong> Se conservan por
              el período requerido por la legislación tributaria peruana (hasta 5 años).
            </li>
            <li>
              <strong className="text-on-surface">Logs de acceso:</strong> Se conservan por un
              máximo de 12 meses.
            </li>
          </ul>
        </Section>

        <Section title="7. Derechos del usuario (ARCO + portabilidad)">
          <p>
            De acuerdo con la Ley 29733 y su Reglamento, el titular de los datos tiene derecho a:
          </p>
          <ul className="list-disc list-inside space-y-1 ml-2">
            <li>
              <strong className="text-on-surface">Acceso:</strong> Solicitar información sobre los
              datos personales que tenemos sobre ti.
            </li>
            <li>
              <strong className="text-on-surface">Rectificación:</strong> Corregir datos inexactos
              o incompletos.
            </li>
            <li>
              <strong className="text-on-surface">Cancelación:</strong> Solicitar la eliminación de
              tus datos personales.
            </li>
            <li>
              <strong className="text-on-surface">Oposición:</strong> Oponerte al tratamiento de
              tus datos para fines específicos.
            </li>
            <li>
              <strong className="text-on-surface">Información y portabilidad:</strong> Recibir tus
              datos en un formato estructurado de uso común.
            </li>
          </ul>
          <p className="mt-3">
            Para ejercer estos derechos, contactar a:{" "}
            <a href="mailto:privacidad@tukijuris.com.pe" className="text-primary hover:underline">
              privacidad@tukijuris.com.pe
            </a>
          </p>
          <p>
            Se responderá en un plazo máximo de 10 días hábiles, conforme a la ley.
          </p>
          <p className="mt-3 text-on-surface/80">
            Si consideras que tus derechos no han sido atendidos adecuadamente, puedes presentar
            una reclamación ante la{" "}
            <strong className="text-on-surface">
              Autoridad Nacional de Protección de Datos Personales (ANPD)
            </strong>{" "}
            del Ministerio de Justicia y Derechos Humanos del Perú (MINJUSDH), a través de su Mesa de
            Partes Virtual o la dirección oficial publicada en{" "}
            <a
              href="https://www.gob.pe/anpd"
              target="_blank"
              rel="noopener noreferrer"
              className="text-primary hover:underline"
            >
              gob.pe/anpd
            </a>.
          </p>
        </Section>

        <Section title="8. Cookies y tecnologías de rastreo">
          <p>TukiJuris utiliza:</p>
          <ul className="list-disc list-inside space-y-1 ml-2">
            <li>
              <strong className="text-on-surface">Cookies esenciales:</strong> Para mantener la
              sesión del usuario (cookies <code>refresh_token</code> y <code>tk_session</code>).
              Son necesarias para el funcionamiento de la plataforma.
            </li>
            <li>
              <strong className="text-on-surface">Almacenamiento local (localStorage):</strong>{" "}
              Para preferencias de interfaz (tema claro/oscuro, organización seleccionada).
            </li>
          </ul>
          <p className="mt-2">
            No utilizamos cookies de terceros para publicidad ni rastreo. No requerimos
            consentimiento previo para las cookies esenciales según la guía interpretativa de la ANPD.
          </p>
        </Section>

        <Section title="9. Menores de edad">
          <p>
            TukiJuris no está dirigido a menores de 18 años. No recopilamos intencionalmente datos
            de menores de edad. Si detectamos que un menor se ha registrado, procederemos a eliminar
            su cuenta y datos asociados.
          </p>
        </Section>

        <Section title="10. Transferencias internacionales">
          <p>
            Los datos pueden ser procesados en servidores ubicados fuera del Perú, principalmente
            en los siguientes flujos:
          </p>
          <ul className="list-disc list-inside space-y-1 ml-2">
            <li>
              <strong className="text-on-surface">Proveedores de IA (Estados Unidos y Unión Europea):</strong>{" "}
              OpenAI, Anthropic, Google y otros. Las consultas del usuario son procesadas en
              servidores internacionales para generar respuestas. Estos proveedores cuentan con
              acuerdos de procesamiento de datos y certificaciones SOC 2.
            </li>
            <li>
              <strong className="text-on-surface">Servicios de correo (Estados Unidos):</strong>{" "}
              El proveedor Resend procesa los correos transaccionales (registro, recuperación de
              contraseña, notificaciones).
            </li>
          </ul>
          <p className="mt-2">
            En todos los casos exigimos un nivel de protección adecuado conforme a la legislación
            peruana. El usuario consiente estas transferencias al utilizar la plataforma, y puede
            revocar su consentimiento eliminando su cuenta en cualquier momento.
          </p>
        </Section>

        <Section title="11. Cambios en esta política">
          <p>
            TukiTuki Solutions SAC se reserva el derecho de actualizar esta política en cualquier
            momento. Los cambios significativos serán notificados a través de la plataforma o por
            correo electrónico con al menos 30 días de anticipación. La fecha de última actualización
            siempre estará visible al inicio de este documento.
          </p>
        </Section>

        <Section title="12. Contacto del responsable de datos">
          <p>
            <strong className="text-on-surface">Responsable:</strong> TukiTuki Solutions SAC
          </p>
          <p>
            <strong className="text-on-surface">RUC:</strong> 20613614509
          </p>
          <p>
            <strong className="text-on-surface">Email:</strong>{" "}
            <a href="mailto:privacidad@tukijuris.com.pe" className="text-primary hover:underline">
              privacidad@tukijuris.com.pe
            </a>
          </p>
          <p>
            <strong className="text-on-surface">Web:</strong>{" "}
            <a href="https://tukijuris.com.pe" className="text-primary hover:underline">
              tukijuris.com.pe
            </a>
          </p>
        </Section>
      </main>

      <LegalFooter />
    </div>
  );
}
