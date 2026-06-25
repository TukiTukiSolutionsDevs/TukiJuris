"""
Seed: Derecho del Consumidor (Perú).

Núcleo normativo:
    - Ley 29571 — Código de Protección y Defensa del Consumidor (2010)
    - DS 011-2011-PCM — Reglamento del Libro de Reclamaciones

Cada chunk resume una institución/regla del Código de Consumo con cita exacta
del artículo. Estilo defensivo: cuando el artículo es muy técnico se resume
con prefijo "Resumen:" antes del texto, indicando interpretación autoritativa
y NO transcripción literal del Código.
"""

CONSUMIDOR_ARTICLES = [
    # ── Disposiciones generales ──────────────────────────────────────────
    {
        "article": "1",
        "section_path": "Código de Consumo > Título Preliminar > Art. 1",
        "content": (
            "Artículo 1.- Derechos de los consumidores (Ley 29571).\n"
            "El Código reconoce los siguientes derechos:\n"
            "a) Derecho a una protección eficaz respecto de productos o servicios que en "
            "condiciones normales o previsibles representen riesgo o peligro para la vida, "
            "salud e integridad física.\n"
            "b) Derecho a acceder a información oportuna, suficiente, veraz y fácilmente "
            "accesible, relevante para tomar una decisión o realizar una elección de consumo.\n"
            "c) Derecho a la protección de sus intereses económicos y de la salud, mediante "
            "el trato equitativo y justo en toda transacción comercial y la protección contra "
            "métodos comerciales coercitivos, abusivos, desleales o que generen información engañosa.\n"
            "d) Derecho a un trato justo y equitativo en toda transacción comercial y a no ser "
            "discriminados por origen, raza, sexo, idioma, religión, opinión, condición económica.\n"
            "e) Derecho a la reparación o reposición del producto, a una nueva ejecución del servicio, "
            "a la devolución del monto pagado o a la indemnización por los daños y perjuicios.\n"
            "f) Derecho a elegir libremente entre productos y servicios.\n"
            "g) Derecho a la protección de sus derechos mediante procedimientos eficaces, "
            "céleres o ágiles, con formalidades mínimas, gratuitos o no costosos.\n"
            "h) Derecho a ser escuchados de manera individual o colectiva."
        ),
    },
    {
        "article": "2",
        "section_path": "Código de Consumo > Título Preliminar > Art. 2",
        "content": (
            "Artículo 2.- Definición de consumidor (Ley 29571).\n"
            "Consumidor es la persona natural o jurídica que adquiere, utiliza o disfruta como "
            "destinatario final productos o servicios materiales e inmateriales, en beneficio "
            "propio o de su grupo familiar o social, actuando así en un ámbito ajeno a una "
            "actividad empresarial o profesional.\n"
            "Quedan incluidos: los microempresarios que evidencien una situación de asimetría "
            "informativa con el proveedor respecto de productos o servicios no relacionados con "
            "el giro propio de su negocio. NO se considera consumidor a quien adquiere bienes o "
            "servicios para incorporarlos al proceso productivo."
        ),
    },
    {
        "article": "18",
        "section_path": "Código de Consumo > Libro I > Idoneidad",
        "content": (
            "Artículo 18.- Idoneidad (Ley 29571).\n"
            "Se entiende por idoneidad la correspondencia entre lo que un consumidor espera y "
            "lo que efectivamente recibe, en función a lo que se le hubiera ofrecido, la "
            "publicidad e información transmitida, las condiciones y circunstancias de la "
            "transacción, las características y naturaleza del producto o servicio, el precio, "
            "entre otros factores, atendiendo a las circunstancias del caso.\n\n"
            "La idoneidad es evaluada en función a la propia naturaleza del producto o servicio "
            "y a su aptitud para satisfacer la finalidad para la cual ha sido puesto en el mercado."
        ),
    },
    {
        "article": "19",
        "section_path": "Código de Consumo > Libro I > Idoneidad",
        "content": (
            "Artículo 19.- Obligación de responder por la idoneidad (Ley 29571).\n"
            "El proveedor responde por la idoneidad y calidad de los productos y servicios "
            "ofrecidos; por la autenticidad de las marcas y leyendas que exhiben sus productos "
            "o del signo que respalda al prestador del servicio; por la falta de conformidad "
            "entre la publicidad comercial de los productos y servicios y éstos; así como por "
            "el contenido y la vida útil del producto indicado en el envase, en lo que corresponda."
        ),
    },
    # ── Información ──────────────────────────────────────────────────────
    {
        "article": "2-Info",
        "section_path": "Código de Consumo > Libro I > Información",
        "content": (
            "Artículos 2-9.- Información relevante (Ley 29571).\n"
            "El proveedor tiene la obligación de ofrecer al consumidor información veraz, "
            "suficiente, de fácil comprensión, apropiada, oportuna y fácilmente accesible, "
            "debiendo ser brindada en idioma castellano.\n\n"
            "La información debe ser proporcionada antes y durante todo el proceso de "
            "consumo. La información requerida varía según el producto/servicio pero incluye: "
            "precio total, características esenciales, riesgos previsibles, restricciones, "
            "garantías, plazo de validez, entidad emisora y cualquier otra información que "
            "el consumidor necesite para una decisión adecuada.\n\n"
            "La carga de la prueba sobre cumplimiento del deber de información corresponde "
            "al proveedor."
        ),
    },
    # ── Publicidad ───────────────────────────────────────────────────────
    {
        "article": "13-Pub",
        "section_path": "Código de Consumo > Libro II > Publicidad comercial",
        "content": (
            "Artículos 13-17.- Publicidad comercial (Ley 29571).\n"
            "Principios aplicables a la publicidad comercial:\n"
            "1. Principio de veracidad: la publicidad no debe contener información falsa o "
            "que induzca a error al consumidor (artículo 8 del DL 1044 también aplicable).\n"
            "2. Principio de autenticidad: la publicidad debe ser identificable como tal.\n"
            "3. Principio de legalidad: la publicidad no debe contravenir el ordenamiento jurídico.\n\n"
            "Publicidad engañosa: aquella que de cualquier manera, incluida su presentación o "
            "diseño, induce a error al consumidor respecto de la naturaleza, características, "
            "calidad, cantidad, precio, condiciones, ventajas o cualquier otro aspecto del producto.\n\n"
            "Autoridad: INDECOPI a través de la Comisión de Fiscalización de la Competencia "
            "Desleal (CFCD) — DL 1044 Ley de Represión de la Competencia Desleal."
        ),
    },
    # ── Métodos comerciales agresivos ────────────────────────────────────
    {
        "article": "58",
        "section_path": "Código de Consumo > Libro II > Métodos comerciales agresivos o engañosos",
        "content": (
            "Artículos 58-59.- Métodos comerciales agresivos o engañosos (Ley 29571).\n"
            "Está prohibido al proveedor:\n"
            "1. Crear la impresión de que el consumidor ya ha ganado, va a ganar o conseguirá "
            "si realiza un acto determinado, un premio o cualquier ventaja, cuando en realidad "
            "no exista tal premio o ventaja, o cuando la obtención esté sujeta a un pago.\n"
            "2. El cobro indebido o no autorizado de productos o servicios que no han sido "
            "expresamente solicitados por el consumidor.\n"
            "3. La modificación, sin el consentimiento expreso del consumidor, de las "
            "condiciones y términos en los que adquirió un producto o contrató un servicio.\n"
            "4. Realizar visitas no solicitadas en el domicilio del consumidor a horas inusuales.\n"
            "5. Realizar comunicaciones telefónicas no deseadas o intempestivas, mensajes "
            "electrónicos, correos electrónicos o cualquier otra forma de comunicación a distancia.\n\n"
            "DERECHO DE RESTITUCIÓN: 7 días calendario para retractarse en ventas a domicilio o "
            "fuera del establecimiento (artículo 59)."
        ),
    },
    # ── Cláusulas abusivas ───────────────────────────────────────────────
    {
        "article": "49",
        "section_path": "Código de Consumo > Libro II > Cláusulas abusivas",
        "content": (
            "Artículos 49-52.- Cláusulas abusivas en contratos de consumo (Ley 29571).\n"
            "Las cláusulas abusivas son INEFICACES de pleno derecho, aún cuando hayan sido "
            "aceptadas formalmente por el consumidor.\n\n"
            "Son cláusulas ABSOLUTAMENTE ABUSIVAS (artículo 50):\n"
            "a) Las que excluyen o limitan la responsabilidad del proveedor por dolo o culpa.\n"
            "b) Las que facultan al proveedor a suspender o resolver unilateralmente el contrato "
            "sin razón objetiva.\n"
            "c) Las que faculten al proveedor a la prórroga o renovación tácita.\n"
            "d) Las que excluyan o limiten el derecho del consumidor a usar las acciones legales.\n"
            "e) Las que liberen al proveedor de responsabilidad por defectos del producto o servicio.\n\n"
            "Son cláusulas RELATIVAMENTE ABUSIVAS (artículo 51): aquellas que, en perjuicio del "
            "consumidor y considerando las circunstancias del caso, importen un desequilibrio "
            "importante en los derechos y obligaciones (cobros excesivos por mora, plazos "
            "desproporcionados, etc.)."
        ),
    },
    # ── Servicios públicos ───────────────────────────────────────────────
    {
        "article": "65",
        "section_path": "Código de Consumo > Libro II > Servicios públicos regulados",
        "content": (
            "Artículos 65 y siguientes.- Servicios públicos regulados (Ley 29571).\n"
            "Los proveedores de servicios públicos (energía eléctrica, agua, gas natural, "
            "telecomunicaciones, transporte) deben cumplir con estándares mínimos de calidad, "
            "continuidad y oportunidad en el suministro.\n\n"
            "Reclamaciones: el consumidor puede reclamar ante el proveedor en primera instancia. "
            "Si no es atendido, puede acudir al organismo regulador sectorial (OSIPTEL, "
            "OSINERGMIN, SUNASS, ANA según sea el caso) antes de INDECOPI.\n\n"
            "Doble vía: el consumidor puede optar por la vía administrativa sectorial o por "
            "INDECOPI cuando los hechos involucran protección al consumidor."
        ),
    },
    # ── Libro de reclamaciones ───────────────────────────────────────────
    {
        "article": "150",
        "section_path": "Código de Consumo > Libro IV > Libro de reclamaciones",
        "content": (
            "Artículos 150-152.- Libro de Reclamaciones (Ley 29571 + DS 011-2011-PCM).\n"
            "Los establecimientos comerciales deben contar con un Libro de Reclamaciones "
            "(físico o virtual) en un lugar visible y de fácil acceso para el consumidor.\n\n"
            "Obligaciones del proveedor:\n"
            "1. Exhibir un aviso indicando la existencia del Libro.\n"
            "2. Atender el reclamo en un plazo máximo de 30 días calendario.\n"
            "3. Conservar los reclamos por un mínimo de 2 años.\n"
            "4. Remitir información al INDECOPI cuando éste lo requiera.\n\n"
            "El Libro Virtual de Reclamaciones es obligatorio para establecimientos cuyas ventas "
            "sean por canales electrónicos."
        ),
    },
    # ── Procedimiento sumarísimo ─────────────────────────────────────────
    {
        "article": "125",
        "section_path": "Código de Consumo > Libro IV > Procedimiento sumarísimo",
        "content": (
            "Artículos 125-127.- Procedimiento sumarísimo en INDECOPI (Ley 29571).\n"
            "Para denuncias por afectación de derechos del consumidor, INDECOPI conoce los casos "
            "en un procedimiento simplificado:\n"
            "1. Comisión de Protección al Consumidor (CPC) en primera instancia.\n"
            "2. Sala Especializada en Protección al Consumidor del Tribunal del INDECOPI en "
            "segunda instancia.\n\n"
            "Plazos: 30 días hábiles para la primera instancia. Las resoluciones admiten "
            "recurso de apelación dentro de los 15 días hábiles.\n\n"
            "Sanciones (artículo 110):\n"
            "- Amonestación.\n"
            "- Multa hasta 450 UIT, según la gravedad y reiterancia.\n"
            "- Medidas correctivas: reparación, reposición, devolución del monto pagado."
        ),
    },
    # ── Medidas correctivas ──────────────────────────────────────────────
    {
        "article": "115",
        "section_path": "Código de Consumo > Libro IV > Medidas correctivas",
        "content": (
            "Artículos 115-116.- Medidas correctivas reparadoras (Ley 29571).\n"
            "Adicionalmente a la multa, INDECOPI puede ordenar al proveedor:\n"
            "1. Reparación del producto.\n"
            "2. Reposición del producto.\n"
            "3. Devolución de la contraprestación pagada.\n"
            "4. Devolución de los montos cobrados indebidamente, incluyendo intereses legales.\n"
            "5. Entrega del producto faltante.\n"
            "6. Cumplimiento del contrato.\n"
            "7. Información correcta cuando se ha brindado información falsa o que induzca a error.\n\n"
            "Las medidas correctivas son acumulativas con la multa y deben ejecutarse en un "
            "plazo razonable bajo apercibimiento de multa coercitiva."
        ),
    },
    # ── Contratos de consumo a distancia ─────────────────────────────────
    {
        "article": "47",
        "section_path": "Código de Consumo > Libro II > Comercio electrónico",
        "content": (
            "Artículos 47-48.- Contratos celebrados a distancia / fuera del establecimiento (Ley 29571).\n"
            "Aplican a contratos celebrados por internet, teléfono, catálogo, venta directa.\n\n"
            "Derecho de revocación (cancelación): el consumidor tiene 7 días calendario para "
            "revocar el contrato sin necesidad de expresar causa y sin penalidad, contados "
            "desde la recepción del bien o desde la celebración del contrato si se trata de "
            "servicios. El proveedor debe devolver íntegramente el monto pagado.\n\n"
            "Información previa exigible: identidad del proveedor, características principales "
            "del producto o servicio, precio total con tributos, modalidades de pago, plazo de "
            "validez de la oferta, derecho de revocación y procedimiento."
        ),
    },
    # ── Discriminación al consumidor ─────────────────────────────────────
    {
        "article": "38",
        "section_path": "Código de Consumo > Libro II > No discriminación",
        "content": (
            "Artículos 38-39.- Prohibición de discriminación (Ley 29571).\n"
            "Está prohibido seleccionar a la clientela, excluir personas o realizar otras "
            "prácticas similares, sin que medien causas de seguridad del establecimiento o "
            "tranquilidad de sus clientes u otras razones objetivas y justificadas.\n\n"
            "La carga de la prueba sobre la existencia de un trato diferenciado idóneo "
            "corresponde al proveedor. La discriminación injustificada por motivos de origen, "
            "raza, sexo, idioma, religión, opinión, condición económica o de cualquier otra "
            "índole es sancionable como infracción muy grave."
        ),
    },
    # ── Productos y servicios financieros ────────────────────────────────
    {
        "article": "82",
        "section_path": "Código de Consumo > Libro III > Servicios financieros",
        "content": (
            "Artículos 82-92.- Productos y servicios financieros (Ley 29571).\n"
            "Para servicios financieros (créditos, depósitos, tarjetas de crédito) las entidades "
            "deben informar la TCEA (tasa de costo efectivo anual) y la TREA (tasa de "
            "rendimiento efectivo anual) en lugar visible.\n\n"
            "Está prohibido el cobro de comisiones por consultas de saldo, mantenimiento de "
            "cuenta inactiva por debajo de cierto umbral, y otras prácticas detalladas por SBS.\n\n"
            "Doble vía de reclamación: SBS para conducta de mercado de la entidad financiera y "
            "INDECOPI cuando se trata de protección al consumidor. La SBS tiene competencia "
            "primaria por el régimen sectorial de tutela del usuario financiero."
        ),
    },
    # ── Asociaciones de consumidores ─────────────────────────────────────
    {
        "article": "153",
        "section_path": "Código de Consumo > Libro IV > Asociaciones de consumidores",
        "content": (
            "Artículos 153-159.- Asociaciones de consumidores (Ley 29571).\n"
            "Son entidades civiles sin fines de lucro reconocidas por INDECOPI, cuyo objeto es "
            "proteger los derechos e intereses de los consumidores. Pueden iniciar denuncias "
            "individuales o colectivas y representar a grupos de consumidores en procesos de "
            "intereses difusos.\n\n"
            "Tienen derecho a percibir una parte de las multas impuestas en los procedimientos "
            "que hayan promovido (hasta el 50% según el caso, conforme el reglamento) como "
            "incentivo a la defensa colectiva."
        ),
    },
    # ── Garantías ────────────────────────────────────────────────────────
    {
        "article": "20",
        "section_path": "Código de Consumo > Libro I > Garantías",
        "content": (
            "Artículos 20-22.- Garantía del producto o servicio (Ley 29571).\n"
            "Tipos de garantía:\n"
            "1. Garantía legal: aquella inherente al producto/servicio, exigible aún cuando no "
            "se haya pactado expresamente.\n"
            "2. Garantía explícita: la que el proveedor ofrece de manera expresa, escrita u oral.\n"
            "3. Garantía implícita: la que se deduce de la naturaleza del producto/servicio "
            "y de la información provista por el proveedor.\n\n"
            "El consumidor puede exigir el cumplimiento de la garantía en el plazo razonable, "
            "que no puede ser menor a 30 días contados desde la entrega del producto.\n\n"
            "En caso de no cumplimiento, el consumidor puede optar entre reparación, "
            "reposición o devolución del monto pagado, sin perjuicio de la indemnización."
        ),
    },
]
