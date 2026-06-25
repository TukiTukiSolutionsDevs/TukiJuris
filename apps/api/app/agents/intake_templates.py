"""
Intake templates — preguntas canónicas por área legal que el agente usa
durante la fase INTAKE / INVESTIGATION de una conversación de análisis de caso.

Las preguntas ahora son estructuradas (`PendingQuestion`) en vez de strings:
cada una tiene un `slot` canónico, texto de pregunta, helper opcional y una
lista de `options` de respuesta rápida. El frontend (`/analizar`) renderiza
chips para `options` + un input libre, evitando el "wall of questions" que
obligaba al cliente a tipear todo de golpe.

Backward compat: el orquestador y el frontend toleran `case_pending` con
strings (conversaciones legacy almacenadas antes de este cambio).
"""

from typing import TypedDict


class PendingQuestion(TypedDict, total=False):
    """Una pregunta estructurada que el frontend renderiza como card + chips."""

    slot: str               # clave canónica para matchear respuestas (ej "tributo")
    question: str           # texto que se muestra al cliente
    helper: str             # subtítulo opcional con contexto
    options: list[str]      # chips de respuesta rápida (lista vacía = solo input libre)
    multi: bool             # True → permite seleccionar varias opciones a la vez


class IntakeTemplate(TypedDict):
    framing: str
    questions: list[PendingQuestion]
    uploads_hint: str


# ──────────────────────────────────────────────────────────────────────────
# Templates by area
# ──────────────────────────────────────────────────────────────────────────

INTAKE_TEMPLATES: dict[str, IntakeTemplate] = {
    "laboral": {
        "framing": (
            "Tu caso entra en materia laboral. En Perú la normativa central es el "
            "TUO del DL 728 (DS 003-97-TR, Ley de Productividad y Competitividad "
            "Laboral) y la Ley 29783 (Seguridad y Salud en el Trabajo). Necesito "
            "datos puntuales para identificar tu régimen y la vía adecuada (interna, "
            "SUNAFIL o judicial laboral)."
        ),
        "questions": [
            {
                "slot": "regimen_laboral",
                "question": "¿En qué régimen estás contratado?",
                "helper": "Determina los derechos y la vía aplicable.",
                "options": [
                    "Régimen privado (DL 728)",
                    "CAS",
                    "MYPE",
                    "SERVIR",
                    "Agrario",
                    "No estoy seguro",
                ],
            },
            {
                "slot": "antiguedad",
                "question": "¿Cuánto tiempo llevas en la empresa?",
                "helper": "Indica años o meses aproximados.",
                "options": [
                    "Menos de 3 meses (período de prueba)",
                    "3-12 meses",
                    "1-5 años",
                    "Más de 5 años",
                ],
            },
            {
                "slot": "contrato",
                "question": "¿Tienes contrato firmado?",
                "options": [
                    "Sí, indefinido",
                    "Sí, plazo fijo",
                    "Sí, parcial",
                    "No tengo contrato escrito",
                ],
            },
            {
                "slot": "boletas",
                "question": "¿Recibes boletas de pago mensuales?",
                "options": [
                    "Sí, todas",
                    "Sí, pero con errores",
                    "Solo algunas",
                    "No, nunca",
                ],
            },
            {
                "slot": "evidencia",
                "question": "¿Qué evidencia escrita tienes del problema?",
                "helper": "Puedes marcar varias o describir libremente.",
                "options": [
                    "Mensajes / WhatsApp",
                    "Correos electrónicos",
                    "Audios o videos",
                    "Capturas de pantalla",
                    "Testigos directos",
                    "No tengo evidencia escrita",
                ],
                "multi": True,
            },
            {
                "slot": "reclamo_previo",
                "question": "¿Hiciste algún reclamo previo?",
                "options": [
                    "No, ninguno",
                    "Reclamo interno a RRHH",
                    "Denuncia ante SUNAFIL",
                    "Demanda judicial laboral",
                ],
            },
        ],
        "uploads_hint": "contrato de trabajo, boletas de pago, correos con RRHH, capturas de WhatsApp",
    },
    "familia": {
        "framing": (
            "Tu caso entra en derecho de familia. La base es el Código Civil "
            "(Libro III), el Código de los Niños y Adolescentes (Ley 27337) y, "
            "si hay violencia, la Ley 30364. Necesito datos personales del núcleo "
            "para definir la vía (notarial, conciliación o juzgado de familia)."
        ),
        "questions": [
            {
                "slot": "estado_civil",
                "question": "¿Cuál es tu estado civil?",
                "options": [
                    "Casado(a)",
                    "Conviviente (unión de hecho)",
                    "Separado(a) de hecho",
                    "Divorciado(a)",
                    "Soltero(a)",
                ],
            },
            {
                "slot": "hijos",
                "question": "¿Hay hijos menores de edad involucrados?",
                "options": [
                    "No, no hay menores",
                    "Sí, uno",
                    "Sí, dos o más",
                ],
            },
            {
                "slot": "regimen_patrimonial",
                "question": "¿Qué régimen patrimonial rige tu matrimonio?",
                "options": [
                    "Sociedad de gananciales",
                    "Separación de patrimonios",
                    "No aplica (no estoy casado)",
                    "No estoy seguro",
                ],
            },
            {
                "slot": "bienes",
                "question": "¿Qué tipo de bienes en común tienen?",
                "helper": "Puedes describir libremente si es algo distinto.",
                "options": [
                    "Inmuebles (casa, terreno)",
                    "Vehículos",
                    "Cuentas bancarias / inversiones",
                    "Negocio o empresa",
                    "No hay bienes en común",
                ],
                "multi": True,
            },
            {
                "slot": "via_preferida",
                "question": "¿Cómo te gustaría resolver?",
                "options": [
                    "Acuerdo conjunto (notarial)",
                    "Conciliación extrajudicial",
                    "Vía judicial",
                    "No estoy seguro todavía",
                ],
            },
            {
                "slot": "violencia",
                "question": "¿Hay antecedentes de violencia familiar?",
                "options": [
                    "No",
                    "Sí, con denuncia previa",
                    "Sí, sin denuncia",
                    "Hay medidas de protección vigentes",
                ],
            },
        ],
        "uploads_hint": "partida de matrimonio o reconocimiento de unión de hecho, partidas de hijos, escrituras de bienes",
    },
    "penal": {
        "framing": (
            "Tu caso entra en derecho penal. La normativa central es el Código "
            "Penal (DL 635) y el Nuevo Código Procesal Penal (DL 957). Necesito "
            "saber tu rol (denunciante, agraviado, imputado) y el estado actual "
            "del proceso para guiarte sobre la vía y los plazos críticos."
        ),
        "questions": [
            {
                "slot": "rol",
                "question": "¿Cuál es tu rol en el caso?",
                "options": [
                    "Agraviado(a) / víctima",
                    "Denunciante (no soy víctima directa)",
                    "Investigado(a) / imputado(a)",
                    "Testigo",
                ],
            },
            {
                "slot": "estado_proceso",
                "question": "¿Ya hay una denuncia o investigación abierta?",
                "options": [
                    "Sí, en fiscalía",
                    "Sí, en comisaría",
                    "Sí, en juzgado penal",
                    "No, todavía no he denunciado",
                ],
            },
            {
                "slot": "delito",
                "question": "¿Qué delito o tipo penal está involucrado?",
                "helper": "Si no estás seguro, describe el hecho libremente.",
                "options": [
                    "Robo / hurto",
                    "Estafa / fraude",
                    "Lesiones",
                    "Violencia familiar",
                    "Difamación / calumnia",
                    "No estoy seguro",
                ],
                "multi": True,
            },
            {
                "slot": "medidas_cautelares",
                "question": "¿Hay medidas cautelares vigentes?",
                "options": [
                    "Detención",
                    "Comparecencia con restricciones",
                    "Impedimento de salida del país",
                    "Prisión preventiva",
                    "No hay medidas",
                ],
                "multi": True,
            },
            {
                "slot": "pruebas",
                "question": "¿Qué pruebas o evidencia tienes?",
                "options": [
                    "Documentos / contratos",
                    "Fotos / videos",
                    "Testigos directos",
                    "Parte médico",
                    "Capturas de mensajes",
                    "No tengo evidencia aún",
                ],
                "multi": True,
            },
            {
                "slot": "defensa",
                "question": "¿Tienes asesoría legal actualmente?",
                "options": [
                    "Sí, abogado privado",
                    "Defensa pública",
                    "Todavía no",
                ],
            },
        ],
        "uploads_hint": "denuncia policial, citación fiscal, parte médico, declaraciones, fotos del lugar",
    },
    "civil": {
        "framing": (
            "Tu caso entra en derecho civil. La base es el Código Civil de 1984 "
            "(DL 295). Según el contenido específico (contratos, obligaciones, "
            "responsabilidad civil, derechos reales, sucesiones), la vía procesal "
            "y plazos cambian."
        ),
        "questions": [
            {
                "slot": "institucion",
                "question": "¿Cuál es la institución civil involucrada?",
                "options": [
                    "Contrato (incumplimiento, nulidad)",
                    "Propiedad / derechos reales",
                    "Herencia / sucesión",
                    "Responsabilidad civil / daños",
                    "Arrendamiento",
                    "Otro",
                ],
            },
            {
                "slot": "fecha_hecho",
                "question": "¿Cuándo ocurrió el hecho que origina el reclamo?",
                "helper": "Crítico para evaluar prescripción.",
                "options": [
                    "Hace menos de 6 meses",
                    "Hace 6-12 meses",
                    "Hace 1-2 años",
                    "Hace más de 2 años",
                ],
            },
            {
                "slot": "cuantia",
                "question": "¿Cuál es la cuantía aproximada en juego?",
                "helper": "Define competencia y vía procesal.",
                "options": [
                    "Menos de 5 UIT",
                    "5-20 UIT",
                    "20-50 UIT",
                    "Más de 50 UIT",
                    "No es cuantificable",
                ],
            },
            {
                "slot": "documentacion",
                "question": "¿Qué documentación firmada tienes?",
                "options": [
                    "Contrato firmado",
                    "Escritura pública",
                    "Recibos / vouchers",
                    "Correos o mensajes",
                    "No tengo nada formal",
                ],
                "multi": True,
            },
            {
                "slot": "contraparte",
                "question": "¿La contraparte está identificada y localizable?",
                "options": [
                    "Sí, persona natural",
                    "Sí, empresa",
                    "Sí, entidad pública",
                    "Sí pero no la encuentro",
                    "No la conozco",
                ],
            },
            {
                "slot": "proceso",
                "question": "¿Ya hay un proceso judicial iniciado?",
                "options": [
                    "No, todavía extrajudicial",
                    "Sí, en juzgado",
                    "Sí, en arbitraje",
                    "Está en conciliación",
                ],
            },
        ],
        "uploads_hint": "contratos, escrituras públicas, correos de tratativas, recibos, partidas registrales",
    },
    "tributario": {
        "framing": (
            "Tu caso entra en materia tributaria. La normativa marco es el TUO del "
            "Código Tributario (DS 133-2013-EF). Necesito identificar el tributo, "
            "el ejercicio fiscal y la situación actual frente a SUNAT para evaluar "
            "fraccionamiento, reclamación o defensa contenciosa."
        ),
        "questions": [
            {
                "slot": "tributo",
                "question": "¿Cuál es el tributo en cuestión?",
                "options": [
                    "Renta de 3ra (empresa)",
                    "Renta de 1ra / 2da / 4ta / 5ta",
                    "IGV",
                    "NRUS",
                    "Predial",
                    "Alcabala",
                    "Vehicular",
                    "Otro",
                ],
            },
            {
                "slot": "regimen_tributario",
                "question": "¿En qué régimen tributario estás?",
                "options": [
                    "NRUS",
                    "RER",
                    "MYPE Tributario",
                    "Régimen General",
                    "Persona natural sin negocio",
                    "No estoy seguro",
                ],
            },
            {
                "slot": "notificacion",
                "question": "¿Has recibido alguna notificación de SUNAT?",
                "options": [
                    "Sí, multa",
                    "Sí, resolución de determinación",
                    "Sí, esquela inductiva",
                    "Sí, orden de pago",
                    "No, todavía no",
                ],
            },
            {
                "slot": "ejercicio_fiscal",
                "question": "¿En qué ejercicio fiscal ocurrió el hecho?",
                "options": [
                    "2026 (ejercicio en curso)",
                    "2025",
                    "2024",
                    "2023",
                    "Anterior a 2023",
                    "No estoy seguro",
                ],
            },
            {
                "slot": "declaracion",
                "question": "¿Presentaste declaración jurada?",
                "options": [
                    "Sí, en plazo",
                    "Sí, fuera de plazo",
                    "No, omití presentar",
                    "No me corresponde declarar",
                ],
            },
            {
                "slot": "plazo_reclamo",
                "question": "¿Estás dentro del plazo de 20 días hábiles para reclamar?",
                "helper": "Crítico — si vence, pierdes la vía contenciosa.",
                "options": [
                    "Sí, todavía tengo plazo",
                    "Está por vencer (5 días o menos)",
                    "Ya venció",
                    "No sé desde cuándo cuento el plazo",
                ],
            },
        ],
        "uploads_hint": "resolución SUNAT, valores notificados, declaraciones presentadas, comprobantes",
    },
    "consumidor": {
        "framing": (
            "Tu caso entra en protección al consumidor. La normativa central es "
            "el Código de Protección y Defensa del Consumidor (Ley 29571) y INDECOPI "
            "es la autoridad. Necesito datos sobre la transacción y la prueba del "
            "incumplimiento para definir reclamo, denuncia o procedimiento sumarísimo."
        ),
        "questions": [
            {
                "slot": "tipo_producto",
                "question": "¿Qué tipo de producto o servicio adquiriste?",
                "options": [
                    "Producto físico",
                    "Servicio (incl. educativo, médico)",
                    "Producto financiero (banco, AFP)",
                    "Producto digital / app",
                    "Otro",
                ],
            },
            {
                "slot": "canal",
                "question": "¿Por qué canal lo adquiriste?",
                "options": [
                    "Tienda física",
                    "Online (e-commerce)",
                    "App móvil",
                    "Llamada telefónica",
                    "Vendedor a domicilio",
                ],
            },
            {
                "slot": "problema",
                "question": "¿Cuál es el problema concreto?",
                "options": [
                    "Producto/servicio no idóneo",
                    "Información engañosa o falta de info",
                    "Garantía rechazada",
                    "Cobro indebido o doble",
                    "Métodos comerciales abusivos",
                    "Otro",
                ],
                "multi": True,
            },
            {
                "slot": "comprobante",
                "question": "¿Conservas comprobante de pago?",
                "options": [
                    "Sí, boleta",
                    "Sí, factura",
                    "Sí, voucher",
                    "Sí, captura o email",
                    "No tengo comprobante",
                ],
                "multi": True,
            },
            {
                "slot": "libro_reclamaciones",
                "question": "¿Anotaste el reclamo en el Libro de Reclamaciones?",
                "options": [
                    "Sí, ya está anotado",
                    "Intenté pero no me dejaron",
                    "No, todavía no",
                ],
            },
            {
                "slot": "monto_perjuicio",
                "question": "¿Cuál es el monto del perjuicio aproximado?",
                "options": [
                    "Menos de S/ 500",
                    "S/ 500 - S/ 5,000",
                    "S/ 5,000 - S/ 50,000",
                    "Más de S/ 50,000",
                ],
            },
        ],
        "uploads_hint": "comprobante de pago, captura de la publicidad, conversaciones con el proveedor, hoja del Libro de Reclamaciones",
    },
    "datos_personales": {
        "framing": (
            "Tu caso entra en protección de datos personales. La Ley 29733 + DS "
            "016-2024-JUS regulan el tratamiento de tus datos y la ANPD es la "
            "autoridad. Identifiquemos quién es el responsable del tratamiento, "
            "el dato afectado y qué derecho ARCO-PD necesitas ejercer."
        ),
        "questions": [
            {
                "slot": "responsable",
                "question": "¿Quién está tratando tus datos?",
                "options": [
                    "Banco / financiera",
                    "Empleador",
                    "Red social",
                    "Comercio / e-commerce",
                    "Entidad pública",
                    "Otro",
                ],
            },
            {
                "slot": "tipo_dato",
                "question": "¿Qué tipo de datos están involucrados?",
                "options": [
                    "Datos básicos (nombre, DNI, dirección)",
                    "Datos de salud",
                    "Biométricos (huella, rostro, voz)",
                    "Ideología / religión / sindicales",
                    "Datos financieros",
                    "Otros datos sensibles",
                ],
                "multi": True,
            },
            {
                "slot": "consentimiento",
                "question": "¿Diste consentimiento informado?",
                "options": [
                    "Sí, por escrito",
                    "Sí, verbal o por click",
                    "No, nunca",
                    "No estoy seguro",
                ],
            },
            {
                "slot": "dano",
                "question": "¿Cuál es el daño o riesgo principal?",
                "options": [
                    "Suplantación de identidad",
                    "Exposición pública",
                    "Perfilamiento / scoring",
                    "Cobros o llamadas indebidas",
                    "Discriminación",
                    "Otro",
                ],
                "multi": True,
            },
            {
                "slot": "derechos_arco",
                "question": "¿Ya ejerciste derechos ARCO-PD?",
                "helper": "Acceso, Rectificación, Cancelación, Oposición.",
                "options": [
                    "Sí, sin respuesta",
                    "Sí, con respuesta insatisfactoria",
                    "No, todavía no",
                ],
            },
            {
                "slot": "brecha",
                "question": "¿Hubo una brecha de seguridad o filtración?",
                "options": [
                    "Sí, pública y comprobada",
                    "Sí, lo sospecho",
                    "No",
                ],
            },
        ],
        "uploads_hint": "captura del aviso de privacidad, correos de la empresa, evidencia de la filtración",
    },
    "contrataciones_estado": {
        "framing": (
            "Tu caso entra en contrataciones del Estado. Si el procedimiento se "
            "convocó después del 22-abr-2025 aplica la nueva Ley 32069 (LGCP); "
            "antes de esa fecha, la Ley 30225. Necesito identificar el tipo de "
            "procedimiento y la fase actual para definir si toca observación de "
            "bases, recurso de apelación o vía arbitral."
        ),
        "questions": [
            {
                "slot": "fecha_convocatoria",
                "question": "¿Cuándo se convocó el procedimiento?",
                "helper": "Decide qué ley aplica.",
                "options": [
                    "Después del 22-abr-2025 (Ley 32069)",
                    "Antes del 22-abr-2025 (Ley 30225)",
                    "No estoy seguro",
                ],
            },
            {
                "slot": "tipo_procedimiento",
                "question": "¿Qué tipo de procedimiento es?",
                "options": [
                    "Licitación pública",
                    "Concurso público",
                    "Adjudicación simplificada",
                    "Contratación directa",
                    "Subasta inversa",
                    "Comparación de precios",
                ],
            },
            {
                "slot": "fase",
                "question": "¿En qué fase está el proceso?",
                "options": [
                    "Bases / convocatoria",
                    "Presentación de ofertas",
                    "Otorgamiento de buena pro",
                    "Ejecución contractual",
                    "Liquidación",
                ],
            },
            {
                "slot": "monto",
                "question": "¿Cuál es el monto del contrato?",
                "options": [
                    "Menos de 8 UIT",
                    "8 - 50 UIT",
                    "50 - 200 UIT",
                    "Más de 200 UIT",
                ],
            },
            {
                "slot": "arbitraje",
                "question": "¿Hay convenio arbitral en el contrato?",
                "options": [
                    "Sí, centro de arbitraje (PUCP, AmCham)",
                    "Sí, OSCE",
                    "No, vía Tribunal de Contrataciones",
                    "No estoy seguro",
                ],
            },
            {
                "slot": "plazo_actuacion",
                "question": "¿Cuál es tu plazo límite para actuar?",
                "options": [
                    "Menos de 5 días hábiles",
                    "5 - 10 días hábiles",
                    "Más de 10 días",
                    "No tengo plazo inmediato",
                ],
            },
        ],
        "uploads_hint": "bases del procedimiento, oferta presentada, contrato, notificaciones, OECE",
    },
    "ambiental": {
        "framing": (
            "Tu caso entra en derecho ambiental. La Ley General del Ambiente "
            "(Ley 28611) es la base. Según el componente afectado (agua, aire, "
            "suelo, biodiversidad), la autoridad competente cambia entre MINAM, "
            "OEFA, ANA, SERFOR o gobiernos regionales."
        ),
        "questions": [
            {
                "slot": "componente",
                "question": "¿Qué componente ambiental está siendo afectado?",
                "options": [
                    "Agua",
                    "Aire",
                    "Suelo",
                    "Biodiversidad (flora/fauna)",
                    "Ruido",
                    "Residuos sólidos",
                ],
                "multi": True,
            },
            {
                "slot": "causante",
                "question": "¿Quién es el presunto causante?",
                "options": [
                    "Empresa formal",
                    "Minería informal / ilegal",
                    "Vecino / particular",
                    "Entidad pública",
                    "No identificado",
                ],
            },
            {
                "slot": "instrumento_ambiental",
                "question": "¿La actividad cuenta con instrumento ambiental?",
                "options": [
                    "Sí, EIA detallado",
                    "Sí, EIA semidetallado",
                    "Sí, DIA",
                    "No tiene instrumento",
                    "No lo sé",
                ],
            },
            {
                "slot": "comunidad_anp",
                "question": "¿Hay comunidad indígena o área natural protegida afectada?",
                "options": [
                    "Sí, comunidad indígena",
                    "Sí, ANP",
                    "Ambos",
                    "No",
                ],
                "multi": True,
            },
            {
                "slot": "denuncia_previa",
                "question": "¿Hay denuncia previa ante alguna autoridad?",
                "options": [
                    "OEFA",
                    "ANA",
                    "Municipalidad",
                    "Gobierno regional",
                    "No hay denuncia previa",
                ],
                "multi": True,
            },
            {
                "slot": "evidencia",
                "question": "¿Qué evidencia tienes?",
                "options": [
                    "Fotos / videos",
                    "Análisis de laboratorio (agua, aire)",
                    "Testimonios",
                    "Denuncias previas archivadas",
                    "No tengo evidencia aún",
                ],
                "multi": True,
            },
        ],
        "uploads_hint": "fotos del impacto, análisis de calidad de agua/aire, denuncia previa, EIA público",
    },
    "constitucional": {
        "framing": (
            "Tu caso entra en derecho constitucional. La base es la Constitución "
            "de 1993 y el Código Procesal Constitucional (Ley 31307). Necesito "
            "identificar el derecho fundamental afectado, el acto lesivo y si "
            "hay vía previa para evaluar amparo, habeas corpus o habeas data."
        ),
        "questions": [
            {
                "slot": "derecho_afectado",
                "question": "¿Qué derecho fundamental consideras afectado?",
                "options": [
                    "Libertad personal",
                    "Debido proceso",
                    "Igualdad / no discriminación",
                    "Información / acceso a datos públicos",
                    "Salud / educación / pensión",
                    "Otro",
                ],
                "multi": True,
            },
            {
                "slot": "acto_lesivo",
                "question": "¿Quién emitió el acto lesivo?",
                "options": [
                    "Entidad pública",
                    "Empresa privada",
                    "Particular",
                    "Resolución judicial",
                ],
            },
            {
                "slot": "via_previa",
                "question": "¿Agotaste la vía previa?",
                "helper": "Requisito para amparo salvo excepciones.",
                "options": [
                    "Sí, agotada",
                    "No, pero es excepción",
                    "Todavía no",
                    "No estoy seguro",
                ],
            },
            {
                "slot": "urgencia",
                "question": "¿Existe daño irreparable o urgencia?",
                "options": [
                    "Sí, urgente (medida cautelar)",
                    "Sí, pero no irreparable",
                    "No es urgente",
                ],
            },
            {
                "slot": "evidencia",
                "question": "¿Qué evidencia documental tienes?",
                "options": [
                    "Resolución / acto administrativo",
                    "Cartas o notificaciones",
                    "Sentencia judicial",
                    "Testimonios",
                    "No tengo aún",
                ],
                "multi": True,
            },
        ],
        "uploads_hint": "resolución o acto cuestionado, cartas, sentencias, pruebas del daño",
    },
    "administrativo": {
        "framing": (
            "Tu caso entra en derecho administrativo. La base es el TUO de la "
            "Ley del Procedimiento Administrativo General (DS 004-2019-JUS) y, "
            "según el sector, la normativa especial. Necesito saber la entidad, "
            "el acto y el estado del procedimiento."
        ),
        "questions": [
            {
                "slot": "entidad",
                "question": "¿Qué entidad pública está involucrada?",
                "options": [
                    "Municipalidad",
                    "Gobierno regional",
                    "Ministerio",
                    "Organismo regulador (OSINERGMIN, OSIPTEL, SUNASS)",
                    "SUNAT / INDECOPI / SBS",
                    "Otra",
                ],
            },
            {
                "slot": "tipo_acto",
                "question": "¿Qué tipo de acto te afecta?",
                "options": [
                    "Sanción / multa",
                    "Denegatoria de trámite",
                    "Silencio administrativo",
                    "Acto que afecta derechos",
                    "Otro",
                ],
            },
            {
                "slot": "fase",
                "question": "¿En qué fase está el procedimiento?",
                "options": [
                    "Inicio / notificación",
                    "Descargos pendientes",
                    "Resolución de primera instancia",
                    "Recurso de apelación / reconsideración",
                    "Contencioso administrativo",
                ],
            },
            {
                "slot": "plazo",
                "question": "¿Tienes plazo límite para actuar?",
                "options": [
                    "Sí, menos de 5 días hábiles",
                    "Sí, 5-15 días hábiles",
                    "Sí, más de 15 días",
                    "Ya venció",
                    "No estoy seguro",
                ],
            },
            {
                "slot": "evidencia",
                "question": "¿Qué documentación tienes?",
                "options": [
                    "Notificación del acto",
                    "Expediente administrativo",
                    "Descargos previos",
                    "Resoluciones",
                    "No tengo aún",
                ],
                "multi": True,
            },
        ],
        "uploads_hint": "notificación, resoluciones, expediente administrativo, TUPA aplicable",
    },
    "corporativo": {
        "framing": (
            "Tu caso entra en derecho corporativo / societario. La base es la "
            "Ley General de Sociedades (Ley 26887) y, según la situación, la "
            "ley de la EIRL o normativa especial. Necesito identificar el tipo "
            "societario y la operación o conflicto."
        ),
        "questions": [
            {
                "slot": "tipo_sociedad",
                "question": "¿Qué tipo de sociedad o vehículo es?",
                "options": [
                    "SAC (S.A.C.)",
                    "SA / SAA",
                    "SRL",
                    "EIRL",
                    "Sociedad civil",
                    "Aún no constituida",
                ],
            },
            {
                "slot": "situacion",
                "question": "¿Cuál es la situación concreta?",
                "options": [
                    "Constituir empresa",
                    "Conflicto entre accionistas",
                    "Aumento o reducción de capital",
                    "Fusión / escisión / disolución",
                    "Responsabilidad de directores",
                    "Otro",
                ],
            },
            {
                "slot": "participacion",
                "question": "¿Cuál es tu rol en la sociedad?",
                "options": [
                    "Accionista mayoritario",
                    "Accionista minoritario",
                    "Director / gerente",
                    "Tercero afectado",
                    "Fundador / inversionista",
                ],
            },
            {
                "slot": "documentacion",
                "question": "¿Qué documentación societaria tienes?",
                "options": [
                    "Escritura de constitución",
                    "Estatutos vigentes",
                    "Actas de junta",
                    "Convenios de accionistas",
                    "No tengo acceso a todo",
                ],
                "multi": True,
            },
            {
                "slot": "urgencia",
                "question": "¿Hay convocatoria o decisión próxima?",
                "options": [
                    "Sí, esta semana",
                    "Sí, este mes",
                    "No, todavía no",
                ],
            },
        ],
        "uploads_hint": "escritura de constitución, estatutos, actas, partida registral de SUNARP",
    },
    "registral": {
        "framing": (
            "Tu caso entra en materia registral. La base es la Ley 26366 (creación "
            "de SUNARP), el Reglamento General de los Registros Públicos "
            "(Res. 126-2012-SUNARP) y, para predios, la Ley 27755. Necesito saber "
            "el registro, el acto y el estado de la calificación."
        ),
        "questions": [
            {
                "slot": "registro",
                "question": "¿En qué registro estás operando?",
                "options": [
                    "Predios",
                    "Personas jurídicas",
                    "Mandatos y poderes",
                    "Vehicular",
                    "Mineros",
                    "Otro",
                ],
            },
            {
                "slot": "tipo_acto",
                "question": "¿Qué tipo de acto querés inscribir?",
                "options": [
                    "Compraventa",
                    "Hipoteca / garantía",
                    "Sucesión intestada",
                    "Constitución de empresa",
                    "Poder",
                    "Otro",
                ],
            },
            {
                "slot": "estado_calificacion",
                "question": "¿En qué estado está el trámite?",
                "options": [
                    "Por presentar",
                    "En calificación",
                    "Esquela de observación",
                    "Tachado",
                    "Inscrito",
                ],
            },
            {
                "slot": "documentacion",
                "question": "¿Qué documentación tienes a la mano?",
                "options": [
                    "Escritura pública",
                    "Minuta",
                    "Partida registral",
                    "Esquela de observación",
                    "Título archivado",
                    "No tengo todo",
                ],
                "multi": True,
            },
            {
                "slot": "plazo",
                "question": "¿Tienes plazo de vigencia del título?",
                "helper": "El asiento de presentación vence a los 35 días.",
                "options": [
                    "Sí, está por vencer",
                    "Sí, todavía hay tiempo",
                    "Ya venció",
                    "No tengo asiento aún",
                ],
            },
        ],
        "uploads_hint": "esquela de observación, escritura, minuta, partida registral SUNARP",
    },
    "competencia": {
        "framing": (
            "Tu caso entra en libre competencia y/o competencia desleal. La base "
            "son el DL 1034 (TUO DS 030-2019-PCM, libre competencia), el DL 1044 "
            "(competencia desleal) y la Ley 31112 (control de fusiones). INDECOPI "
            "es la autoridad."
        ),
        "questions": [
            {
                "slot": "tipo_conducta",
                "question": "¿Qué conducta consideras anticompetitiva o desleal?",
                "options": [
                    "Cártel / acuerdo entre competidores",
                    "Abuso de posición de dominio",
                    "Publicidad engañosa o denigratoria",
                    "Confusión / imitación",
                    "Fusión sin autorización",
                    "Otra",
                ],
            },
            {
                "slot": "rol",
                "question": "¿Cuál es tu rol?",
                "options": [
                    "Denunciante / víctima",
                    "Investigado(a)",
                    "Tercero con interés",
                ],
            },
            {
                "slot": "mercado",
                "question": "¿En qué mercado o sector?",
                "options": [
                    "Retail / consumo masivo",
                    "Servicios profesionales",
                    "Tecnología / digital",
                    "Industrial / B2B",
                    "Salud / farma",
                    "Otro",
                ],
            },
            {
                "slot": "evidencia",
                "question": "¿Qué evidencia tienes?",
                "options": [
                    "Documentos / contratos",
                    "Correos o mensajes",
                    "Publicidad cuestionada",
                    "Análisis económico",
                    "No tengo aún",
                ],
                "multi": True,
            },
            {
                "slot": "estado_proceso",
                "question": "¿Hay procedimiento abierto?",
                "options": [
                    "Sí, en INDECOPI",
                    "Sí, con resolución de primera instancia",
                    "No, todavía no",
                ],
            },
        ],
        "uploads_hint": "publicidad o pieza cuestionada, contratos, correos, resoluciones INDECOPI",
    },
    "compliance": {
        "framing": (
            "Tu caso entra en compliance y cumplimiento normativo. Las normas "
            "clave son la Ley 30424 (responsabilidad penal de personas jurídicas), "
            "DL 1106 (lavado de activos), Ley 27693 (UIF), DL 1372 (beneficiario "
            "final) y, según sector, normativa especial (SBS, MTC, etc.)."
        ),
        "questions": [
            {
                "slot": "objetivo",
                "question": "¿Cuál es tu objetivo principal?",
                "options": [
                    "Implementar programa de cumplimiento",
                    "Responder a investigación / denuncia",
                    "Diligencia debida (M&A, contraparte)",
                    "Capacitación interna",
                    "Defensa penal corporativa",
                    "Otro",
                ],
            },
            {
                "slot": "riesgo",
                "question": "¿Qué riesgo principal te preocupa?",
                "options": [
                    "Soborno / corrupción",
                    "Lavado de activos",
                    "Financiamiento del terrorismo",
                    "Conflicto de interés",
                    "Datos personales",
                    "Otro",
                ],
            },
            {
                "slot": "tamano_empresa",
                "question": "¿De qué tamaño es la organización?",
                "options": [
                    "Microempresa",
                    "Pequeña empresa",
                    "Mediana empresa",
                    "Gran empresa",
                    "Multinacional",
                    "ONG / sin fines de lucro",
                ],
            },
            {
                "slot": "sector",
                "question": "¿En qué sector opera?",
                "options": [
                    "Financiero",
                    "Construcción / infraestructura",
                    "Minería / energía",
                    "Retail / consumo",
                    "Tecnología",
                    "Otro",
                ],
            },
            {
                "slot": "estado",
                "question": "¿Hay procedimiento o investigación en curso?",
                "options": [
                    "Sí, fiscalía",
                    "Sí, autoridad sectorial",
                    "Sí, auditoría interna",
                    "No, todavía no",
                ],
            },
        ],
        "uploads_hint": "código de ética, manuales, contratos sospechosos, notificaciones de autoridad",
    },
    "comercio_exterior": {
        "framing": (
            "Tu caso entra en comercio exterior y aduanas. La base es la Ley "
            "General de Aduanas (DL 1053) y su reglamento, además de los TLC "
            "vigentes. Necesito saber el régimen aduanero y la etapa del trámite."
        ),
        "questions": [
            {
                "slot": "regimen",
                "question": "¿Qué régimen aduanero aplica?",
                "options": [
                    "Importación definitiva",
                    "Exportación",
                    "Admisión temporal",
                    "Drawback",
                    "Zona franca",
                    "Otro",
                ],
            },
            {
                "slot": "estado_trámite",
                "question": "¿En qué fase está el trámite?",
                "options": [
                    "DAM por presentar",
                    "En despacho",
                    "Levante autorizado",
                    "Fiscalización posterior",
                    "Resolución sancionatoria",
                ],
            },
            {
                "slot": "tlc",
                "question": "¿Aplicas algún TLC o acuerdo comercial?",
                "options": [
                    "Sí, TLC EEUU",
                    "Sí, TLC China",
                    "Sí, TLC UE",
                    "Sí, otro",
                    "No",
                ],
                "multi": True,
            },
            {
                "slot": "monto",
                "question": "¿Monto aproximado de la operación?",
                "options": [
                    "Menos de USD 10,000",
                    "USD 10,000 - 100,000",
                    "USD 100,000 - 1M",
                    "Más de USD 1M",
                ],
            },
            {
                "slot": "documentacion",
                "question": "¿Qué documentación aduanera tienes?",
                "options": [
                    "DAM / declaración",
                    "Factura comercial",
                    "Conocimiento de embarque (BL)",
                    "Certificado de origen",
                    "No tengo todo",
                ],
                "multi": True,
            },
        ],
        "uploads_hint": "DAM, factura, BL, certificado de origen, notificaciones SUNAT-Aduanas",
    },
    "procesal": {
        "framing": (
            "Tu caso entra en derecho procesal. Según la materia, aplica el "
            "Código Procesal Civil (DL 768), el Nuevo Código Procesal Penal "
            "(DL 957) o la Nueva Ley Procesal del Trabajo (Ley 29497). Necesito "
            "saber la vía, fase y el acto procesal que necesitas."
        ),
        "questions": [
            {
                "slot": "via",
                "question": "¿En qué vía está el proceso?",
                "options": [
                    "Civil",
                    "Penal",
                    "Laboral",
                    "Contencioso administrativo",
                    "Constitucional",
                    "Familia",
                ],
            },
            {
                "slot": "fase",
                "question": "¿En qué fase procesal estás?",
                "options": [
                    "Por demandar",
                    "Demanda admitida / contestación",
                    "Audiencia / juzgamiento",
                    "Sentencia primera instancia",
                    "Apelación / casación",
                    "Ejecución",
                ],
            },
            {
                "slot": "acto_requerido",
                "question": "¿Qué acto procesal necesitas resolver?",
                "options": [
                    "Demanda / contestación",
                    "Recurso (apelación, casación)",
                    "Medida cautelar",
                    "Excepciones procesales",
                    "Ejecución de sentencia",
                    "Otro",
                ],
            },
            {
                "slot": "plazo",
                "question": "¿Cuál es el plazo crítico?",
                "options": [
                    "Menos de 5 días hábiles",
                    "5-10 días hábiles",
                    "Más de 10 días",
                    "No tengo plazo inmediato",
                ],
            },
            {
                "slot": "expediente",
                "question": "¿Tienes el expediente o número de causa?",
                "options": [
                    "Sí, completo",
                    "Sí, parcial",
                    "Solo número de expediente",
                    "No tengo aún",
                ],
            },
        ],
        "uploads_hint": "demanda / contestación, resoluciones, cédulas, sentencia, recursos",
    },
    "comercial": {
        "framing": (
            "Tu caso entra en derecho comercial / mercantil. La base son la Ley "
            "de Títulos Valores (Ley 27287), la Ley de Arbitraje (DL 1071) y la "
            "Ley del Sistema Concursal (Ley 27809). Necesito saber el instrumento "
            "o contrato y la situación de incumplimiento."
        ),
        "questions": [
            {
                "slot": "instrumento",
                "question": "¿Qué instrumento o contrato está involucrado?",
                "options": [
                    "Letra de cambio",
                    "Pagaré",
                    "Cheque",
                    "Factura negociable",
                    "Contrato comercial",
                    "Otro",
                ],
            },
            {
                "slot": "rol",
                "question": "¿Cuál es tu rol?",
                "options": [
                    "Acreedor",
                    "Deudor",
                    "Avalista / garante",
                    "Endosatario",
                ],
            },
            {
                "slot": "monto",
                "question": "¿Cuál es el monto en juego?",
                "options": [
                    "Menos de 5 UIT",
                    "5 - 20 UIT",
                    "20 - 100 UIT",
                    "Más de 100 UIT",
                ],
            },
            {
                "slot": "incumplimiento",
                "question": "¿Cuándo se produjo el incumplimiento?",
                "options": [
                    "Hace menos de 30 días",
                    "1-6 meses",
                    "6-12 meses",
                    "Más de 1 año",
                ],
            },
            {
                "slot": "accion_buscada",
                "question": "¿Qué acción buscas?",
                "options": [
                    "Proceso de ejecución",
                    "Demanda ordinaria",
                    "Arbitraje",
                    "Concurso preventivo / liquidación",
                    "Acuerdo extrajudicial",
                ],
            },
        ],
        "uploads_hint": "título valor original, contratos, cartas de requerimiento, comprobantes",
    },
    "notarial": {
        "framing": (
            "Tu caso entra en materia notarial. La base es el DL 1049 (Ley del "
            "Notariado) y la Ley 26662 (asuntos no contenciosos). Necesito saber "
            "el acto que necesitas y si hay alguna observación o conflicto."
        ),
        "questions": [
            {
                "slot": "acto",
                "question": "¿Qué acto notarial necesitas?",
                "options": [
                    "Escritura pública",
                    "Minuta",
                    "Acta notarial",
                    "Carta notarial",
                    "Protocolización",
                    "Asunto no contencioso (sucesión, rectificación)",
                ],
            },
            {
                "slot": "partes",
                "question": "¿Quiénes son las partes?",
                "options": [
                    "Solo yo",
                    "Familiares",
                    "Socios comerciales",
                    "Contraparte desconocida o ausente",
                ],
            },
            {
                "slot": "documentacion",
                "question": "¿Qué documentación tienes?",
                "options": [
                    "DNI vigente de todas las partes",
                    "Minuta firmada",
                    "Títulos de propiedad",
                    "Partidas registrales",
                    "Falta documentación",
                ],
                "multi": True,
            },
            {
                "slot": "urgencia",
                "question": "¿Hay plazo o urgencia?",
                "options": [
                    "Sí, esta semana",
                    "Sí, este mes",
                    "No es urgente",
                ],
            },
            {
                "slot": "observacion",
                "question": "¿Hubo observación notarial o registral?",
                "options": [
                    "Sí, notarial",
                    "Sí, registral",
                    "No, recién empiezo",
                ],
            },
        ],
        "uploads_hint": "minuta, DNIs, partidas registrales, observaciones recibidas",
    },
    "seguridad_social": {
        "framing": (
            "Tu caso entra en seguridad social. La base es la Ley 26790 (EsSalud), "
            "el DL 19990 (Sistema Nacional de Pensiones — ONP) y el DL 25897 "
            "(SPP — AFP). Necesito saber el sistema, el aporte y la prestación "
            "que reclamas."
        ),
        "questions": [
            {
                "slot": "sistema",
                "question": "¿En qué sistema estás afiliado(a)?",
                "options": [
                    "ONP (SNP)",
                    "AFP (SPP)",
                    "Ambos en distintos periodos",
                    "Régimen militar / policial / docente",
                    "Ninguno",
                ],
            },
            {
                "slot": "prestacion",
                "question": "¿Qué prestación necesitas?",
                "options": [
                    "Pensión de jubilación",
                    "Pensión de invalidez",
                    "Pensión de sobrevivencia",
                    "Reconocimiento de aportes",
                    "Atención EsSalud",
                    "Otro",
                ],
            },
            {
                "slot": "edad",
                "question": "¿En qué rango de edad estás?",
                "options": [
                    "Menos de 50",
                    "50-60",
                    "60-65",
                    "65 o más",
                ],
            },
            {
                "slot": "anos_aporte",
                "question": "¿Aproximadamente cuántos años de aporte tienes?",
                "options": [
                    "Menos de 10",
                    "10-20",
                    "20-30",
                    "Más de 30",
                    "No tengo claro",
                ],
            },
            {
                "slot": "estado_solicitud",
                "question": "¿Hay solicitud o resolución previa?",
                "options": [
                    "Sí, denegatoria",
                    "Sí, en evaluación",
                    "Sí, aprobada pero con problemas",
                    "No, todavía no he presentado",
                ],
            },
        ],
        "uploads_hint": "boletas de aporte, certificados de trabajo, resoluciones ONP/AFP, partida de nacimiento",
    },
    "propiedad_intelectual": {
        "framing": (
            "Tu caso entra en propiedad intelectual. La base es la Decisión 486 "
            "(propiedad industrial), la Decisión 351 (derecho de autor), el DL 1075 "
            "y el DL 822. INDECOPI es la autoridad."
        ),
        "questions": [
            {
                "slot": "tipo_derecho",
                "question": "¿Qué tipo de derecho está involucrado?",
                "options": [
                    "Marca",
                    "Patente",
                    "Diseño industrial",
                    "Derecho de autor",
                    "Modelo de utilidad",
                    "Secreto empresarial",
                ],
            },
            {
                "slot": "objetivo",
                "question": "¿Qué necesitas hacer?",
                "options": [
                    "Registrar",
                    "Renovar",
                    "Denunciar infracción",
                    "Defender oposición",
                    "Licenciar / ceder",
                    "Otro",
                ],
            },
            {
                "slot": "registro_actual",
                "question": "¿Cuál es el estado de tu registro?",
                "options": [
                    "Sin registrar",
                    "Solicitud en trámite",
                    "Registrado y vigente",
                    "Caducado",
                    "Otorgado a un tercero",
                ],
            },
            {
                "slot": "alcance",
                "question": "¿En qué territorio te interesa proteger?",
                "options": [
                    "Solo Perú",
                    "Comunidad Andina",
                    "Internacional (PCT / Madrid)",
                    "No estoy seguro",
                ],
            },
            {
                "slot": "evidencia_uso",
                "question": "¿Qué evidencia de uso o creación tienes?",
                "options": [
                    "Documento de creación / desarrollo",
                    "Facturas / ventas",
                    "Publicidad y redes",
                    "Acuerdo de confidencialidad",
                    "No tengo aún",
                ],
                "multi": True,
            },
        ],
        "uploads_hint": "constancia INDECOPI, manual de marca, evidencia de uso, contratos de licencia",
    },
    "financiero": {
        "framing": (
            "Tu caso entra en derecho financiero. La base es la Ley 26702 (Ley "
            "General del Sistema Financiero) y normativa SBS. Necesito identificar "
            "la entidad, el producto y la conducta cuestionada."
        ),
        "questions": [
            {
                "slot": "tipo_entidad",
                "question": "¿Con qué tipo de entidad tienes el conflicto?",
                "options": [
                    "Banco",
                    "Financiera",
                    "Caja municipal",
                    "Cooperativa",
                    "Fintech",
                    "Otra",
                ],
            },
            {
                "slot": "producto",
                "question": "¿Qué producto está involucrado?",
                "options": [
                    "Tarjeta de crédito",
                    "Crédito hipotecario",
                    "Crédito vehicular",
                    "Crédito personal",
                    "Cuenta de ahorros / corriente",
                    "Otro",
                ],
            },
            {
                "slot": "problema",
                "question": "¿Cuál es el problema concreto?",
                "options": [
                    "Cobros indebidos",
                    "Tasa de interés abusiva",
                    "Reporte negativo en centrales de riesgo",
                    "Negativa de servicio",
                    "Cláusula abusiva",
                    "Otro",
                ],
                "multi": True,
            },
            {
                "slot": "monto",
                "question": "¿Monto aproximado en disputa?",
                "options": [
                    "Menos de S/ 5,000",
                    "S/ 5,000 - S/ 50,000",
                    "S/ 50,000 - S/ 200,000",
                    "Más de S/ 200,000",
                ],
            },
            {
                "slot": "estado_reclamo",
                "question": "¿Ya hiciste algún reclamo?",
                "options": [
                    "Sí, ante la entidad",
                    "Sí, ante INDECOPI",
                    "Sí, ante SBS",
                    "No, todavía no",
                ],
            },
        ],
        "uploads_hint": "contrato del producto, estados de cuenta, cartas, capturas del reporte de riesgo",
    },
    "mercado_valores": {
        "framing": (
            "Tu caso entra en mercado de valores. La base es el TUO de la Ley "
            "del Mercado de Valores (DS 093-2002-EF) y normativa de la SMV. "
            "Necesito saber el rol y el instrumento involucrado."
        ),
        "questions": [
            {
                "slot": "rol",
                "question": "¿Cuál es tu rol?",
                "options": [
                    "Emisor",
                    "Inversionista",
                    "Intermediario / SAB",
                    "Directivo / insider",
                    "Tercero afectado",
                ],
            },
            {
                "slot": "instrumento",
                "question": "¿Qué instrumento está involucrado?",
                "options": [
                    "Acciones",
                    "Bonos",
                    "Fondos mutuos",
                    "Fideicomisos",
                    "Derivados",
                    "Otro",
                ],
            },
            {
                "slot": "situacion",
                "question": "¿Cuál es la situación?",
                "options": [
                    "Oferta pública / emisión",
                    "Información privilegiada / insider trading",
                    "Manipulación del mercado",
                    "Falta de transparencia",
                    "Conflicto con intermediario",
                    "Otro",
                ],
            },
            {
                "slot": "estado_proceso",
                "question": "¿Hay procedimiento abierto en la SMV?",
                "options": [
                    "Sí, inicial",
                    "Sí, con resolución",
                    "No, recién empiezo",
                ],
            },
            {
                "slot": "documentacion",
                "question": "¿Qué documentación tienes?",
                "options": [
                    "Prospecto / hecho de importancia",
                    "Contratos de intermediación",
                    "Estados financieros",
                    "Comunicaciones SMV",
                    "No tengo aún",
                ],
                "multi": True,
            },
        ],
        "uploads_hint": "prospecto, hechos de importancia, estados financieros, comunicaciones SMV",
    },
    "seguros": {
        "framing": (
            "Tu caso entra en derecho de seguros. La base es la Ley 29946 "
            "(Contrato de Seguro). Necesito saber el tipo de póliza, el "
            "siniestro y la posición de la aseguradora."
        ),
        "questions": [
            {
                "slot": "tipo_poliza",
                "question": "¿Qué tipo de póliza tienes?",
                "options": [
                    "Vehicular / SOAT",
                    "Salud / EPS",
                    "Vida",
                    "Hogar / patrimonial",
                    "Empresarial / responsabilidad civil",
                    "Otro",
                ],
            },
            {
                "slot": "rol",
                "question": "¿Cuál es tu rol?",
                "options": [
                    "Asegurado / contratante",
                    "Beneficiario",
                    "Tercero afectado",
                    "Aseguradora",
                ],
            },
            {
                "slot": "siniestro",
                "question": "¿Hubo siniestro?",
                "options": [
                    "Sí, ya denunciado",
                    "Sí, sin denunciar todavía",
                    "Estoy evaluando la cobertura",
                    "Conflicto con prima / vigencia",
                ],
            },
            {
                "slot": "respuesta_aseguradora",
                "question": "¿Qué respuesta dio la aseguradora?",
                "options": [
                    "Rechazó cobertura",
                    "Cubrió parcialmente",
                    "Demora injustificada",
                    "Aún no responde",
                ],
            },
            {
                "slot": "monto",
                "question": "¿Monto aproximado en juego?",
                "options": [
                    "Menos de S/ 5,000",
                    "S/ 5,000 - S/ 50,000",
                    "S/ 50,000 - S/ 500,000",
                    "Más de S/ 500,000",
                ],
            },
        ],
        "uploads_hint": "póliza, denuncia del siniestro, peritajes, respuestas de la aseguradora",
    },
    "minero": {
        "framing": (
            "Tu caso entra en derecho minero. La base es el TUO de la Ley General "
            "de Minería (DS 014-92-EM), la Ley 28090 (cierre de minas), Ley 28271 "
            "(pasivos ambientales) y DL 1100 (minería ilegal)."
        ),
        "questions": [
            {
                "slot": "rol",
                "question": "¿Cuál es tu rol en el caso?",
                "options": [
                    "Titular de concesión",
                    "Comunidad afectada",
                    "Trabajador / contratista",
                    "Inversionista",
                    "Autoridad / regulado por OSINERGMIN",
                ],
            },
            {
                "slot": "tipo_actividad",
                "question": "¿Qué tipo de actividad minera?",
                "options": [
                    "Gran y mediana minería",
                    "Pequeña minería",
                    "Minería artesanal (MAPE)",
                    "Beneficio / procesamiento",
                    "Exploración",
                ],
            },
            {
                "slot": "situacion",
                "question": "¿Cuál es la situación?",
                "options": [
                    "Petitorio / concesión",
                    "Servidumbre minera",
                    "Conflicto con comunidad",
                    "Fiscalización OEFA / OSINERGMIN",
                    "Cierre de mina / pasivos",
                    "Formalización MAPE",
                ],
            },
            {
                "slot": "instrumento_ambiental",
                "question": "¿Tienes instrumento ambiental aprobado?",
                "options": [
                    "Sí, EIA-d",
                    "Sí, EIA-sd",
                    "Sí, DIA / IGAFOM",
                    "No, no tiene",
                    "En trámite",
                ],
            },
            {
                "slot": "estado_proceso",
                "question": "¿Hay procedimiento en curso?",
                "options": [
                    "Sanción de OEFA",
                    "Procedimiento ante INGEMMET",
                    "Conflicto judicial",
                    "Diálogo / mesa de trabajo",
                    "Recién comenzando",
                ],
            },
        ],
        "uploads_hint": "título de concesión, EIA, resoluciones OEFA/INGEMMET, actas comunales",
    },
    "hidrocarburos": {
        "framing": (
            "Tu caso entra en derecho de hidrocarburos / energía. La base es la "
            "Ley Orgánica de Hidrocarburos (Ley 26221 / TUO DS 042-2005-EM), DL "
            "25844 (concesiones eléctricas) y normativa OSINERGMIN."
        ),
        "questions": [
            {
                "slot": "sector",
                "question": "¿En qué sub-sector estás?",
                "options": [
                    "Upstream (exploración / producción)",
                    "Midstream (transporte / almacenamiento)",
                    "Downstream (distribución / comercialización)",
                    "Electricidad",
                    "Gas natural domiciliario",
                ],
            },
            {
                "slot": "rol",
                "question": "¿Cuál es tu rol?",
                "options": [
                    "Concesionario / contratista",
                    "Usuario final",
                    "Comunidad afectada",
                    "Regulador / autoridad",
                    "Inversionista",
                ],
            },
            {
                "slot": "situacion",
                "question": "¿Cuál es la situación concreta?",
                "options": [
                    "Otorgamiento / renovación de concesión",
                    "Servidumbre",
                    "Conflicto con comunidad",
                    "Fiscalización OSINERGMIN",
                    "Tarifa / regulación",
                    "Otro",
                ],
            },
            {
                "slot": "monto",
                "question": "¿Monto aproximado en juego?",
                "options": [
                    "Menos de USD 100K",
                    "USD 100K - 1M",
                    "USD 1M - 10M",
                    "Más de USD 10M",
                    "No es cuantificable",
                ],
            },
            {
                "slot": "documentacion",
                "question": "¿Qué documentación tienes?",
                "options": [
                    "Contrato de concesión / licencia",
                    "Estudios ambientales",
                    "Resoluciones OSINERGMIN / PERUPETRO",
                    "Actas comunales",
                    "No tengo todo",
                ],
                "multi": True,
            },
        ],
        "uploads_hint": "contrato de concesión, EIA, resoluciones OSINERGMIN / PERUPETRO",
    },
    "telecom": {
        "framing": (
            "Tu caso entra en telecomunicaciones. La base es el TUO de la Ley "
            "de Telecomunicaciones (DS 013-93-TCC), Ley 28295 (compartición de "
            "infraestructura), Ley 29904 (banda ancha) y normativa OSIPTEL."
        ),
        "questions": [
            {
                "slot": "tipo_caso",
                "question": "¿Qué tipo de caso es?",
                "options": [
                    "Reclamo de usuario (facturación, calidad)",
                    "Conflicto entre operadores",
                    "Concesión / licencia",
                    "Espectro radioeléctrico",
                    "Compartición de infraestructura",
                    "Otro",
                ],
            },
            {
                "slot": "rol",
                "question": "¿Cuál es tu rol?",
                "options": [
                    "Usuario final (persona / empresa)",
                    "Operador",
                    "Proveedor de infraestructura",
                    "Autoridad",
                ],
            },
            {
                "slot": "operador",
                "question": "¿Con qué operador está el conflicto?",
                "options": [
                    "Movistar (Telefónica)",
                    "Claro",
                    "Entel",
                    "Bitel",
                    "Otro operador",
                    "No aplica",
                ],
            },
            {
                "slot": "estado_reclamo",
                "question": "¿Estado del reclamo?",
                "options": [
                    "Reclamo ante el operador",
                    "Recurso ante OSIPTEL",
                    "Tribunal Administrativo de Solución de Reclamos",
                    "Vía judicial",
                    "Recién empezando",
                ],
            },
            {
                "slot": "evidencia",
                "question": "¿Qué evidencia tienes?",
                "options": [
                    "Contrato / términos del servicio",
                    "Recibos / facturas",
                    "Capturas de conversación",
                    "Comunicaciones del operador",
                    "No tengo aún",
                ],
                "multi": True,
            },
        ],
        "uploads_hint": "contrato del servicio, recibos, comunicaciones del operador, resoluciones OSIPTEL",
    },
    "transporte": {
        "framing": (
            "Tu caso entra en derecho de transporte y tránsito. La base es la "
            "Ley 27181 (Ley General de Transporte), el Código de Tránsito (DS "
            "016-2009-MTC) y normativa MTC / SUTRAN / ATU."
        ),
        "questions": [
            {
                "slot": "tipo_caso",
                "question": "¿Qué tipo de caso es?",
                "options": [
                    "Papeleta / infracción de tránsito",
                    "Licencia (denegatoria, retención)",
                    "Permiso de operación (transporte público)",
                    "Accidente de tránsito",
                    "Fiscalización SUTRAN",
                    "Otro",
                ],
            },
            {
                "slot": "tipo_vehiculo",
                "question": "¿Qué tipo de vehículo?",
                "options": [
                    "Particular",
                    "Taxi / app",
                    "Transporte público de pasajeros",
                    "Carga pesada",
                    "Motorizado menor",
                ],
            },
            {
                "slot": "autoridad",
                "question": "¿Qué autoridad está involucrada?",
                "options": [
                    "Municipalidad",
                    "MTC",
                    "ATU (Lima/Callao)",
                    "SUTRAN",
                    "Policía Nacional",
                ],
            },
            {
                "slot": "estado",
                "question": "¿En qué fase está?",
                "options": [
                    "Notificación / acta",
                    "Descargos pendientes",
                    "Resolución sancionatoria",
                    "Recurso de apelación",
                    "Ejecución coactiva",
                ],
            },
            {
                "slot": "plazo",
                "question": "¿Plazo para actuar?",
                "options": [
                    "Menos de 5 días hábiles",
                    "5-15 días hábiles",
                    "Más de 15 días",
                    "Ya venció",
                ],
            },
        ],
        "uploads_hint": "papeleta / acta, licencia, permisos, resoluciones, fotos del accidente",
    },
    "salud": {
        "framing": (
            "Tu caso entra en derecho de salud. La base es la Ley General de "
            "Salud (Ley 26842), Ley 29459 (productos farmacéuticos), Ley 30024 "
            "(historia clínica electrónica) y Ley 29414 (derechos del paciente)."
        ),
        "questions": [
            {
                "slot": "tipo_caso",
                "question": "¿Qué tipo de caso es?",
                "options": [
                    "Mala praxis médica",
                    "Negativa de atención",
                    "Falta de información / consentimiento",
                    "Cobertura EsSalud / EPS / SIS",
                    "Producto farmacéutico defectuoso",
                    "Otro",
                ],
            },
            {
                "slot": "establecimiento",
                "question": "¿En qué tipo de establecimiento?",
                "options": [
                    "Hospital público (MINSA)",
                    "Hospital EsSalud",
                    "Clínica privada",
                    "EPS / aseguradora",
                    "Farmacia / botica",
                    "Otro",
                ],
            },
            {
                "slot": "dano",
                "question": "¿Qué tipo de daño hubo?",
                "options": [
                    "Daño físico permanente",
                    "Daño físico temporal",
                    "Daño emocional / moral",
                    "Daño económico (gastos)",
                    "Fallecimiento",
                    "Aún en evaluación",
                ],
                "multi": True,
            },
            {
                "slot": "documentacion",
                "question": "¿Qué documentación tienes?",
                "options": [
                    "Historia clínica",
                    "Recetas / órdenes médicas",
                    "Comprobantes de pago",
                    "Peritajes",
                    "No tengo aún (la pidieron y no la dan)",
                ],
                "multi": True,
            },
            {
                "slot": "estado_reclamo",
                "question": "¿Ya hiciste algún reclamo?",
                "options": [
                    "Sí, ante el establecimiento",
                    "Sí, ante SUSALUD",
                    "Sí, ante INDECOPI",
                    "Sí, vía penal",
                    "No, todavía no",
                ],
            },
        ],
        "uploads_hint": "historia clínica, comprobantes, peritajes, comunicaciones del establecimiento",
    },
}


GENERIC_TEMPLATE: IntakeTemplate = {
    "framing": (
        "Tu consulta entra en derecho peruano. Antes de analizarla en profundidad "
        "necesito información puntual para identificar la mejor vía y citar las "
        "normas exactas que aplican a tu situación."
    ),
    "questions": [
        {
            "slot": "cuando_donde",
            "question": "¿Cuándo y dónde ocurrió el hecho que motiva tu consulta?",
            "helper": "Indica fecha aproximada y lugar.",
            "options": [],
        },
        {
            "slot": "partes",
            "question": "¿Quiénes son las partes involucradas?",
            "helper": "Personas, empresas o entidades públicas.",
            "options": [],
        },
        {
            "slot": "documentacion",
            "question": "¿Qué documentación tienes hasta ahora?",
            "options": [
                "Contratos firmados",
                "Mensajes / WhatsApp",
                "Correos electrónicos",
                "Resoluciones o cartas",
                "Fotos / videos",
                "No tengo documentación aún",
            ],
            "multi": True,
        },
        {
            "slot": "accion_previa",
            "question": "¿Tomaste alguna acción previa?",
            "options": [
                "No, ninguna",
                "Reclamo verbal",
                "Reclamo escrito",
                "Denuncia formal",
            ],
        },
        {
            "slot": "resultado_buscado",
            "question": "¿Qué resultado concreto buscas?",
            "options": [
                "Cese de un acto",
                "Indemnización",
                "Regularización",
                "Información / orientación",
                "Otro",
            ],
        },
        {
            "slot": "plazo_limite",
            "question": "¿Hay algún plazo límite que te preocupe?",
            "options": [
                "Sí, urgente (menos de 7 días)",
                "Sí, próximas semanas",
                "No, no hay plazo inmediato",
                "No estoy seguro",
            ],
        },
    ],
    "uploads_hint": "cualquier documento, correo, captura o resolución vinculada al caso",
}


def get_template(area: str) -> IntakeTemplate:
    """Return the intake template for a legal area, falling back to GENERIC."""
    return INTAKE_TEMPLATES.get(area, GENERIC_TEMPLATE)


def normalize_pending(raw: list) -> list[PendingQuestion]:
    """Coerce a `case_pending` list into structured PendingQuestion[].

    Tolerates legacy conversations where `case_pending` was `list[str]` —
    wraps each string into a synthetic structured question with no options.
    """
    out: list[PendingQuestion] = []
    for i, item in enumerate(raw or []):
        if isinstance(item, dict) and item.get("question"):
            out.append(
                {
                    "slot": str(item.get("slot") or f"q_{i}"),
                    "question": str(item["question"]),
                    "helper": str(item["helper"]) if item.get("helper") else "",
                    "options": [str(o) for o in (item.get("options") or [])],
                    "multi": bool(item.get("multi", False)),
                }
            )
        elif isinstance(item, str) and item.strip():
            out.append(
                {
                    "slot": f"q_{i}",
                    "question": item.strip(),
                    "helper": "",
                    "options": [],
                    "multi": False,
                }
            )
    return out


# ──────────────────────────────────────────────────────────────────────────
# Tuning constants
# ──────────────────────────────────────────────────────────────────────────

# Hard cap on investigation turns before forcing analysis. After this many
# back-and-forth exchanges the orchestrator commits to a final analysis to
# avoid feeling like an interrogation.
MAX_INVESTIGATION_TURNS = 3

# Tokens budget for intake / investigation LLM calls.
# Intake: only the framing — 600 is enough (questions come from template).
# Investigation: returns JSON with response + facts + remaining + ready flag.
# Empirically Groq llama-3.3-70b uses ~1100-1400 tokens for the JSON payload,
# so we give 1800 to leave headroom and avoid mid-JSON truncation that
# breaks parsing downstream.
INTAKE_MAX_TOKENS = 600
INVESTIGATE_MAX_TOKENS = 1800

# User signals that force immediate transition to analysis phase.
FORCE_ANALYSIS_SIGNALS = (
    "analiza ya",
    "pasa al análisis",
    "pasa al analisis",
    "dame el análisis",
    "dame el analisis",
    "ya tengo todo",
    "ya tienes todo",
    "analiza ahora",
    "responde ya",
    "salta",
    "skip",
)


def user_signaled_analysis(message: str) -> bool:
    """True if the user explicitly asks to jump to the analysis phase."""
    low = message.lower()
    return any(sig in low for sig in FORCE_ANALYSIS_SIGNALS)
