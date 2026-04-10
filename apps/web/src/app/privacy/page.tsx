import Link from "next/link";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Politica de Privacidad | TukiJuris",
  description: "Politica de privacidad y proteccion de datos de TukiJuris.",
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
            Politica de Privacidad
          </h1>
          <p className="text-sm text-on-surface/50">
            Ultima actualizacion: 9 de abril de 2026
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
            Esta politica cumple con la Ley N° 29733 — Ley de Proteccion de Datos Personales del
            Peru y su Reglamento (D.S. N° 003-2013-JUS).
          </p>
        </div>

        {/* Content */}
        <Section title="1. Datos que Recopilamos">
          <p>Recopilamos las siguientes categorias de datos:</p>

          <h3 className="text-on-surface font-semibold text-sm mt-4 mb-2">1.1 Datos de registro</h3>
          <ul className="list-disc list-inside space-y-1 ml-2">
            <li>Nombre completo</li>
            <li>Correo electronico</li>
            <li>Contrasena (almacenada con hash bcrypt, nunca en texto plano)</li>
          </ul>

          <h3 className="text-on-surface font-semibold text-sm mt-4 mb-2">1.2 Datos de uso</h3>
          <ul className="list-disc list-inside space-y-1 ml-2">
            <li>Consultas realizadas a la plataforma</li>
            <li>Areas del derecho consultadas</li>
            <li>Frecuencia y patrones de uso</li>
            <li>Direccion IP y datos del navegador (User-Agent)</li>
          </ul>

          <h3 className="text-on-surface font-semibold text-sm mt-4 mb-2">1.3 Claves API de terceros (BYOK)</h3>
          <ul className="list-disc list-inside space-y-1 ml-2">
            <li>Las claves API proporcionadas por el usuario son cifradas en reposo (AES-256).</li>
            <li>Solo se descifran en memoria durante el procesamiento de cada solicitud.</li>
            <li>Jamas se almacenan en logs, se comparten con terceros ni se exponen en la interfaz.</li>
          </ul>

          <h3 className="text-on-surface font-semibold text-sm mt-4 mb-2">1.4 Datos de pago</h3>
          <ul className="list-disc list-inside space-y-1 ml-2">
            <li>
              Los datos de tarjeta de credito/debito son procesados directamente por las pasarelas
              de pago (Stripe/Culqi). TukiJuris NO almacena numeros de tarjeta.
            </li>
          </ul>
        </Section>

        <Section title="2. Finalidad del Tratamiento">
          <p>Los datos personales son tratados para:</p>
          <ul className="list-disc list-inside space-y-1 ml-2">
            <li>Proveer y mantener el servicio de TukiJuris</li>
            <li>Autenticar y gestionar las cuentas de usuario</li>
            <li>Procesar pagos y gestionar suscripciones</li>
            <li>Mejorar la calidad del servicio y los modelos de busqueda</li>
            <li>Enviar comunicaciones relacionadas con el servicio (actualizaciones, mantenimiento)</li>
            <li>Cumplir con obligaciones legales</li>
          </ul>
          <p className="mt-2">
            <strong className="text-on-surface">No vendemos ni compartimos datos personales con
            terceros para fines publicitarios.</strong>
          </p>
        </Section>

        <Section title="3. Base Legal del Tratamiento">
          <ul className="list-disc list-inside space-y-1 ml-2">
            <li>
              <strong className="text-on-surface">Ejecucion contractual:</strong> El tratamiento es
              necesario para prestar el servicio contratado.
            </li>
            <li>
              <strong className="text-on-surface">Consentimiento:</strong> Otorgado al registrarse
              y aceptar estos terminos.
            </li>
            <li>
              <strong className="text-on-surface">Obligacion legal:</strong> Cumplimiento de la Ley
              29733 y normativa tributaria peruana.
            </li>
          </ul>
        </Section>

        <Section title="4. Comparticion de Datos con Terceros">
          <p>Los datos del usuario pueden ser compartidos con:</p>
          <ul className="list-disc list-inside space-y-1 ml-2">
            <li>
              <strong className="text-on-surface">Proveedores de IA</strong> (OpenAI, Google,
              Anthropic): Reciben unicamente el texto de la consulta del usuario para generar
              respuestas. NO reciben datos personales identificables.
            </li>
            <li>
              <strong className="text-on-surface">Pasarelas de pago</strong> (Stripe/Culqi):
              Procesan datos de pago directamente, bajo sus propias politicas de privacidad.
            </li>
            <li>
              <strong className="text-on-surface">Proveedores de infraestructura</strong>:
              Servicios de hosting y base de datos operan bajo acuerdos de confidencialidad.
            </li>
            <li>
              <strong className="text-on-surface">Autoridades competentes</strong>: Cuando sea
              requerido por ley o por orden judicial.
            </li>
          </ul>
        </Section>

        <Section title="5. Seguridad de los Datos">
          <p>Implementamos las siguientes medidas de seguridad:</p>
          <ul className="list-disc list-inside space-y-1 ml-2">
            <li>Cifrado en transito (TLS/HTTPS) para todas las comunicaciones</li>
            <li>Cifrado en reposo para claves API (AES-256) y contrasenas (bcrypt)</li>
            <li>Autenticacion basada en JWT con expiracion configurable</li>
            <li>Rate limiting por IP y por usuario para prevenir abuso</li>
            <li>Logs de acceso y monitoreo de actividad sospechosa</li>
            <li>Backups cifrados de la base de datos</li>
          </ul>
          <div
            className="mt-4 p-4 rounded-lg bg-primary/5"
            style={{ border: "1px solid rgba(255,209,101,0.15)" }}
          >
            <p className="text-primary font-medium text-sm">
              TukiJuris es un software de asistencia juridica, NO un estudio de abogados.
            </p>
            <p className="text-on-surface-variant text-xs mt-1">
              Las consultas realizadas a traves de la plataforma NO estan protegidas por el
              secreto profesional abogado-cliente. No ingrese informacion sensible o confidencial
              que requiera dicha proteccion.
            </p>
          </div>
        </Section>

        <Section title="6. Conservacion de Datos">
          <ul className="list-disc list-inside space-y-1 ml-2">
            <li>
              <strong className="text-on-surface">Datos de cuenta:</strong> Se conservan mientras
              la cuenta este activa. Tras la eliminacion de cuenta, se eliminan en un plazo de 30 dias.
            </li>
            <li>
              <strong className="text-on-surface">Historial de consultas:</strong> Se conserva
              mientras la cuenta este activa. El usuario puede eliminarlo manualmente.
            </li>
            <li>
              <strong className="text-on-surface">Datos de facturacion:</strong> Se conservan por
              el periodo requerido por la legislacion tributaria peruana (hasta 5 anos).
            </li>
            <li>
              <strong className="text-on-surface">Logs de acceso:</strong> Se conservan por un
              maximo de 12 meses.
            </li>
          </ul>
        </Section>

        <Section title="7. Derechos del Usuario (ARCO)">
          <p>
            De acuerdo con la Ley 29733, el usuario tiene derecho a:
          </p>
          <ul className="list-disc list-inside space-y-1 ml-2">
            <li>
              <strong className="text-on-surface">Acceso:</strong> Solicitar informacion sobre los
              datos personales que tenemos.
            </li>
            <li>
              <strong className="text-on-surface">Rectificacion:</strong> Corregir datos inexactos
              o incompletos.
            </li>
            <li>
              <strong className="text-on-surface">Cancelacion:</strong> Solicitar la eliminacion de
              sus datos personales.
            </li>
            <li>
              <strong className="text-on-surface">Oposicion:</strong> Oponerse al tratamiento de
              sus datos para fines especificos.
            </li>
          </ul>
          <p className="mt-3">
            Para ejercer estos derechos, contactar a:{" "}
            <a href="mailto:privacidad@tukijuris.net.pe" className="text-primary hover:underline">
              privacidad@tukijuris.net.pe
            </a>
          </p>
          <p>
            Se respondera en un plazo maximo de 10 dias habiles, conforme a la ley.
          </p>
        </Section>

        <Section title="8. Cookies y Tecnologias de Rastreo">
          <p>TukiJuris utiliza:</p>
          <ul className="list-disc list-inside space-y-1 ml-2">
            <li>
              <strong className="text-on-surface">Cookies esenciales:</strong> Para mantener la
              sesion del usuario (JWT token). Son necesarias para el funcionamiento de la plataforma.
            </li>
            <li>
              <strong className="text-on-surface">Almacenamiento local (localStorage):</strong>{" "}
              Para preferencias de interfaz y configuracion del usuario.
            </li>
          </ul>
          <p className="mt-2">
            No utilizamos cookies de terceros para publicidad ni rastreo.
          </p>
        </Section>

        <Section title="9. Menores de Edad">
          <p>
            TukiJuris no esta dirigido a menores de 18 anos. No recopilamos intencionalmente datos
            de menores de edad. Si detectamos que un menor se ha registrado, procederemos a eliminar
            su cuenta y datos asociados.
          </p>
        </Section>

        <Section title="10. Transferencias Internacionales">
          <p>
            Los datos pueden ser procesados en servidores ubicados fuera del Peru (proveedores de
            cloud como AWS, Google Cloud, etc.). En todos los casos, se garantiza un nivel de
            proteccion adecuado conforme a la legislacion peruana.
          </p>
          <p>
            Las consultas enviadas a proveedores de IA (OpenAI, Google, Anthropic) se procesan en
            sus servidores internacionales. Estas transferencias son necesarias para la prestacion
            del servicio y el usuario las consiente al utilizar la plataforma.
          </p>
        </Section>

        <Section title="11. Cambios en esta Politica">
          <p>
            TukiTuki Solutions SAC se reserva el derecho de actualizar esta politica en cualquier
            momento. Los cambios significativos seran notificados a traves de la plataforma o por
            correo electronico. La fecha de ultima actualizacion siempre estara visible al inicio
            de este documento.
          </p>
        </Section>

        <Section title="12. Contacto del Responsable de Datos">
          <p>
            <strong className="text-on-surface">Responsable:</strong> TukiTuki Solutions SAC
          </p>
          <p>
            <strong className="text-on-surface">RUC:</strong> 20613614509
          </p>
          <p>
            <strong className="text-on-surface">Email:</strong>{" "}
            <a href="mailto:privacidad@tukijuris.net.pe" className="text-primary hover:underline">
              privacidad@tukijuris.net.pe
            </a>
          </p>
          <p>
            <strong className="text-on-surface">Web:</strong>{" "}
            <a href="https://tukijuris.net.pe" className="text-primary hover:underline">
              tukijuris.net.pe
            </a>
          </p>
        </Section>
      </main>

      <LegalFooter />
    </div>
  );
}
