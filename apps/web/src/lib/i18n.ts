/**
 * Simple i18n preparation — string constants for future translation.
 * Currently Spanish only, but structured for easy addition of other languages.
 */

type Locale = "es" | "en";

const translations: Record<Locale, Record<string, string>> = {
  es: {
    "app.name": "TukiJuris",
    "app.tagline": "Plataforma Juridica Inteligente",
    "app.subtitle": "Derecho Peruano IA",
    "app.description":
      "Plataforma juridica inteligente especializada en derecho peruano. Consulta normativa, jurisprudencia y recibe orientacion legal con agentes de IA especializados.",
    "app.version": "v0.3.0",

    "chat.placeholder": "Escribe tu consulta legal sobre derecho peruano...",
    "chat.send": "Enviar",
    "chat.new": "Nueva consulta",
    "chat.analyzing": "Analizando tu consulta legal...",
    "chat.general": "Consulta general — el orquestador determinara el area",
    "chat.directed": "Consulta dirigida",
    "chat.feedback.good": "Respuesta util",
    "chat.feedback.bad": "Respuesta incorrecta",
    "chat.download.pdf": "Descargar como PDF",
    "chat.history": "Historial",
    "chat.error":
      "Lo siento, hubo un error al procesar tu consulta. Verifica que el servidor API este corriendo en http://localhost:8000",

    "nav.search": "Buscar normativa",
    "nav.analyze": "Analizar caso",
    "nav.org": "Organizacion",
    "nav.billing": "Planes y uso",
    "nav.settings": "Configuracion",
    "nav.guide": "Guia de uso",
    "nav.analytics": "Analytics",
    "nav.bookmarks": "Marcadores",
    "nav.history": "Historial",
    "nav.developer": "API para Desarrolladores",
    "nav.open": "Abrir menu de navegacion",

    "areas.title": "Areas del Derecho",
    "areas.toggle": "Mostrar/ocultar areas del derecho",
    "areas.civil": "Civil",
    "areas.penal": "Penal",
    "areas.laboral": "Laboral",
    "areas.tributario": "Tributario",
    "areas.constitucional": "Constitucional",
    "areas.administrativo": "Administrativo",
    "areas.corporativo": "Corporativo",
    "areas.registral": "Registral",
    "areas.comercio_exterior": "Comercio Ext.",
    "areas.compliance": "Compliance",
    "areas.competencia": "Competencia/PI",

    "auth.login": "Iniciar sesion",
    "auth.register": "Crear cuenta",
    "auth.logout": "Cerrar sesion",
    "auth.email": "Email",
    "auth.password": "Contrasena",
    "auth.name": "Nombre completo",
    "auth.signing_in": "Ingresando...",
    "auth.registering": "Registrando...",
    "auth.no_account": "No tienes cuenta?",
    "auth.has_account": "Ya tienes cuenta?",
    "auth.sign_up": "Registrate",
    "auth.sign_in": "Inicia sesion",
    "auth.or_continue": "O continuar con",
    "auth.free_access": "Accede a TukiJuris gratis",

    "disclaimer":
      "Esta plataforma brinda orientacion juridica, no constituye asesoria legal. Consulte con un abogado colegiado para casos especificos.",

    "shortcuts.title": "Atajos de Teclado",
    "shortcuts.close": "Cerrar",
    "shortcuts.focus_search": "Enfocar busqueda",
    "shortcuts.new_chat": "Nueva consulta",
    "shortcuts.show_shortcuts": "Mostrar atajos",
    "shortcuts.close_modal": "Cerrar modal/menu",
    "shortcuts.toggle_sidebar": "Mostrar/ocultar sidebar",
    "shortcuts.send_message": "Enviar mensaje",
    "shortcuts.bookmarks": "Ir a marcadores",
    "shortcuts.history": "Ir a historial",

    "help.title": "Ayuda",
    "help.keyboard_shortcuts": "Atajos de teclado",
    "help.guide": "Guia de uso",
    "help.status": "Estado del servicio",
    "help.version": "Version",

    "skip.content": "Ir al contenido principal",

    "model.select": "Seleccionar modelo de IA",
    "notifications.label": "Notificaciones",
    "settings.label": "Configuracion",
  },
  en: {
    "app.name": "TukiJuris",
    "app.tagline": "Intelligent Legal Platform",
    "app.subtitle": "Peruvian Law AI",
    "app.description":
      "Intelligent legal platform specialized in Peruvian law. Query regulations, case law and receive legal guidance from specialized AI agents.",
    "app.version": "v0.3.0",

    "chat.placeholder": "Type your legal query about Peruvian law...",
    "chat.send": "Send",
    "chat.new": "New query",
    "chat.analyzing": "Analyzing your legal query...",
    "chat.general": "General query — the orchestrator will determine the area",
    "chat.directed": "Directed query",
    "chat.feedback.good": "Helpful response",
    "chat.feedback.bad": "Incorrect response",
    "chat.download.pdf": "Download as PDF",
    "chat.history": "History",
    "chat.error":
      "Sorry, there was an error processing your query. Check that the API server is running at http://localhost:8000",

    "nav.search": "Search regulations",
    "nav.analyze": "Analyze case",
    "nav.org": "Organization",
    "nav.billing": "Plans & usage",
    "nav.settings": "Settings",
    "nav.guide": "User guide",
    "nav.analytics": "Analytics",
    "nav.bookmarks": "Bookmarks",
    "nav.history": "History",
    "nav.developer": "Developer API",
    "nav.open": "Open navigation menu",

    "areas.title": "Legal Areas",
    "areas.toggle": "Show/hide legal areas",

    "auth.login": "Log in",
    "auth.register": "Create account",
    "auth.logout": "Log out",
    "auth.email": "Email",
    "auth.password": "Password",
    "auth.name": "Full name",
    "auth.signing_in": "Signing in...",
    "auth.registering": "Registering...",
    "auth.no_account": "Don't have an account?",
    "auth.has_account": "Already have an account?",
    "auth.sign_up": "Sign up",
    "auth.sign_in": "Sign in",
    "auth.or_continue": "Or continue with",
    "auth.free_access": "Access TukiJuris for free",

    "disclaimer":
      "This platform provides legal guidance, it does not constitute legal advice. Consult a licensed attorney for specific cases.",

    "shortcuts.title": "Keyboard Shortcuts",
    "shortcuts.close": "Close",
    "shortcuts.focus_search": "Focus search",
    "shortcuts.new_chat": "New query",
    "shortcuts.show_shortcuts": "Show shortcuts",
    "shortcuts.close_modal": "Close modal/menu",
    "shortcuts.toggle_sidebar": "Toggle sidebar",
    "shortcuts.send_message": "Send message",
    "shortcuts.bookmarks": "Go to bookmarks",
    "shortcuts.history": "Go to history",

    "help.title": "Help",
    "help.keyboard_shortcuts": "Keyboard shortcuts",
    "help.guide": "User guide",
    "help.status": "Service status",
    "help.version": "Version",

    "skip.content": "Skip to main content",

    "model.select": "Select AI model",
    "notifications.label": "Notifications",
    "settings.label": "Settings",
  },
};

let currentLocale: Locale = "es";

export function t(key: string): string {
  return translations[currentLocale]?.[key] ?? translations["es"][key] ?? key;
}

export function setLocale(locale: Locale) {
  currentLocale = locale;
}

export function getLocale(): Locale {
  return currentLocale;
}
