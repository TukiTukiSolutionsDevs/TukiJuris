import Link from "next/link";
import Image from "next/image";

const FOOTER_LINKS = [
  { href: "/terms", label: "Términos" },
  { href: "/privacy", label: "Privacidad" },
  { href: "/docs", label: "Documentación" },
  { href: "/status", label: "Estado" },
];

export function PublicFooter() {
  return (
    <footer className="bg-background border-t border-ghost-border">
      <div className="max-w-7xl mx-auto px-4 lg:px-8 py-12">
        {/* Top row */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-8 mb-8">
          {/* Brand */}
          <div className="flex flex-col gap-3">
            <div className="flex items-center gap-2.5">
              <Image
                src="/brand/logo-icon.png"
                alt="TukiJuris"
                className="h-10 w-10 object-contain"
                width={40}
                height={40}
              />
              <span className="font-headline text-xl font-bold text-primary tracking-tight">
                TukiJuris
              </span>
            </div>
            <p className="text-sm text-on-surface/60 max-w-xs">
              Plataforma Jurídica Inteligente para el Derecho Peruano
            </p>
          </div>

          {/* Links */}
          <div className="flex flex-col sm:items-center gap-3">
            <nav className="flex flex-wrap gap-4 text-xs uppercase tracking-widest text-on-surface-variant">
              {FOOTER_LINKS.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  className="hover:text-primary transition-colors"
                >
                  {link.label}
                </Link>
              ))}
            </nav>
          </div>

          {/* Contact */}
          <div className="flex flex-col sm:items-end gap-2">
            <a
              href="mailto:soporte@tukijuris.net.pe"
              className="text-sm text-on-surface-variant hover:text-primary transition-colors"
            >
              soporte@tukijuris.net.pe
            </a>
          </div>
        </div>

        {/* Bottom */}
        <div className="pt-6 border-t border-ghost-border flex flex-col sm:flex-row items-center justify-between gap-2 text-xs text-on-surface/60 uppercase tracking-widest">
          <span>© {new Date().getFullYear()} TukiJuris Abogados. Todos los derechos reservados.</span>
          <span>Esta plataforma no constituye asesoría legal.</span>
        </div>
      </div>
    </footer>
  );
}
