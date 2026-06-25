"""
Seed: Propiedad Intelectual (Perú + Comunidad Andina).

Núcleo normativo:
    - DL 1075 — Régimen Común sobre Propiedad Industrial (complementa Decisión 486 CAN)
    - DL 822 — Ley sobre el Derecho de Autor (complementa Decisión 351 CAN)
    - Decisión 486 — Régimen Común de Propiedad Industrial (Comunidad Andina)
    - Decisión 351 — Régimen Común sobre Derecho de Autor y Derechos Conexos
    - Convenio de París (CUP), Convenio de Berna, ADPIC (TRIPS), PCT
"""

PROPIEDAD_INTELECTUAL_ARTICLES = [
    {
        "article": "Marcas-Concepto",
        "section_path": "Decisión 486 + DL 1075 > Marcas",
        "content": (
            "Artículos 134-174 Decisión 486 + DL 1075 — Marcas.\n"
            "MARCA: cualquier signo que sea apto para distinguir productos o servicios en el "
            "mercado. Pueden ser palabras, dibujos, imágenes, formas, colores, sonidos, "
            "olores u olor de los productos.\n\n"
            "REQUISITOS DE REGISTRO (Art. 134):\n"
            "1. PERCEPTIBILIDAD: detectable por los sentidos.\n"
            "2. DISTINTIVIDAD: aptitud para identificar el origen empresarial.\n"
            "3. REPRESENTABILIDAD GRÁFICA: descripción precisa.\n\n"
            "VIGENCIA: 10 años desde la concesión del registro, RENOVABLES indefinidamente "
            "por períodos sucesivos de 10 años (Art. 152).\n\n"
            "CLASIFICACIÓN INTERNACIONAL DE NIZA: 45 clases (34 productos + 11 servicios). "
            "El registro se otorga POR CLASE — multi-clase posible con un solo expediente.\n\n"
            "DERECHOS DEL TITULAR (Art. 154):\n"
            "- Uso exclusivo en el mercado.\n"
            "- Acción contra terceros que usen signos idénticos o confundibles.\n"
            "- Licencias y transferencias (con anotación registral)."
        ),
    },
    {
        "article": "Marca-Procedimiento-Registro",
        "section_path": "DL 1075 > Procedimiento de registro de marca",
        "content": (
            "Procedimiento de registro de marca ante INDECOPI (DL 1075 + Decisión 486).\n"
            "AUTORIDAD: Dirección de Signos Distintivos de INDECOPI.\n\n"
            "ETAPAS:\n"
            "1. BÚSQUEDA FONÉTICA Y FIGURATIVA: recomendada antes de solicitar registro para "
            "evitar conflictos con marcas pre-existentes.\n"
            "2. SOLICITUD: formato + denominación + reproducción gráfica + clases + pago de "
            "tasa.\n"
            "3. EXAMEN DE FORMA: 15 días hábiles.\n"
            "4. PUBLICACIÓN en Gaceta Electrónica de Propiedad Industrial.\n"
            "5. PLAZO DE OPOSICIÓN: 30 DÍAS HÁBILES desde la publicación. Cualquier tercero "
            "con interés legítimo puede oponerse.\n"
            "6. EXAMEN DE FONDO: distintividad, no incurrir en prohibiciones absolutas o "
            "relativas, no confundibilidad con marcas anteriores.\n"
            "7. RESOLUCIÓN: concesión o denegatoria, recurrible en apelación ante la Sala "
            "Especializada en PI del Tribunal de INDECOPI.\n\n"
            "PROHIBICIONES ABSOLUTAS (Art. 135): signos genéricos, descriptivos, contrarios al "
            "orden público o las buenas costumbres, banderas estatales, etc.\n"
            "PROHIBICIONES RELATIVAS (Art. 136): identidad o semejanza con marcas registradas, "
            "afectación a derechos de autor o derechos previos."
        ),
    },
    {
        "article": "Cancelacion-por-falta-de-uso",
        "section_path": "Decisión 486 > Cancelación por falta de uso",
        "content": (
            "Artículo 165 Decisión 486 — Cancelación por falta de uso de la marca.\n"
            "Procede cancelar el registro de una marca cuando NO HA SIDO USADA por su titular "
            "en al menos uno de los países andinos durante los 3 AÑOS CONSECUTIVOS anteriores a "
            "la fecha de la solicitud de cancelación.\n\n"
            "LEGITIMADO ACTIVO: cualquier persona con interés legítimo (típicamente, otro "
            "comerciante interesado en registrar una marca similar).\n\n"
            "CARGA DE LA PRUEBA DEL USO: corresponde al TITULAR de la marca probarla. Medios:\n"
            "- Facturas, comprobantes de pago.\n"
            "- Catálogos y material publicitario.\n"
            "- Empaques y etiquetas.\n"
            "- Declaraciones juradas y testimoniales.\n\n"
            "CAUSAS JUSTIFICADAS DE NO USO: fuerza mayor, restricciones legales sobre el "
            "producto, exigencias de autorización sanitaria, etc.\n\n"
            "EFECTOS DE LA CANCELACIÓN: la marca queda libre para registro por terceros — el "
            "solicitante de la cancelación tiene PRIORIDAD para registrarla durante 3 meses."
        ),
    },
    {
        "article": "Marca-Notoria",
        "section_path": "Decisión 486 > Marca notoriamente conocida",
        "content": (
            "Artículos 224-236 Decisión 486 — Marca notoriamente conocida.\n"
            "DEFINICIÓN: marca conocida por el sector pertinente del público en cualquier país "
            "miembro de la CAN, sea o no su registrada.\n\n"
            "FACTORES PARA LA NOTORIEDAD (Art. 228):\n"
            "1. Grado de conocimiento de la marca en el sector pertinente.\n"
            "2. Intensidad y ámbito de difusión y publicidad.\n"
            "3. Antigüedad y uso constante.\n"
            "4. Análisis económico de la marca (valor patrimonial).\n"
            "5. Comercialización transfronteriza.\n\n"
            "PROTECCIÓN REFORZADA:\n"
            "- Se protege contra REGISTRO o USO de signos idénticos o similares por terceros "
            "sin necesidad de registro previo en el país.\n"
            "- Protección AMPLIA frente al riesgo de DILUCIÓN, parasitismo o aprovechamiento "
            "desleal de su reputación.\n"
            "- Procede aún para productos o servicios DISTINTOS si existe riesgo de asociación "
            "indebida.\n\n"
            "INSCRIPCIÓN VOLUNTARIA DE NOTORIEDAD ante INDECOPI: facilita la prueba en futuros "
            "procedimientos de oposición o infracción."
        ),
    },
    {
        "article": "Patentes-Concepto",
        "section_path": "Decisión 486 + DL 1075 > Patentes de invención",
        "content": (
            "Artículos 14-49 Decisión 486 — Patente de invención.\n"
            "PATENTE: derecho exclusivo concedido por el Estado al inventor para la "
            "explotación de su invención por un plazo de 20 AÑOS contado desde la fecha de "
            "presentación de la solicitud (Art. 50).\n\n"
            "REQUISITOS DE PATENTABILIDAD (Art. 14):\n"
            "1. NOVEDAD: la invención no debe estar comprendida en el estado de la técnica "
            "anterior a la fecha de prioridad.\n"
            "2. NIVEL INVENTIVO: la invención no debe ser obvia para una persona del oficio "
            "con conocimiento medio en la materia.\n"
            "3. APLICACIÓN INDUSTRIAL: la invención debe poder ser producida o utilizada en "
            "cualquier tipo de industria.\n\n"
            "INVENCIONES NO PATENTABLES (Art. 15):\n"
            "- Descubrimientos científicos y teorías matemáticas.\n"
            "- Métodos terapéuticos, diagnósticos y quirúrgicos.\n"
            "- Plantas, animales y procedimientos esencialmente biológicos.\n"
            "- Software per se (puede ser objeto de derecho de autor).\n"
            "- Métodos de negocios y reglas de juego.\n\n"
            "DERECHO DE PRIORIDAD: 12 meses desde la primera solicitud en un país signatario "
            "del Convenio de París para reclamar prioridad en otros países (PCT incluido)."
        ),
    },
    {
        "article": "Modelo-Utilidad-Diseno-Industrial",
        "section_path": "Decisión 486 > Modelo de utilidad y diseño industrial",
        "content": (
            "Modelos de utilidad y diseños industriales (Decisión 486).\n\n"
            "MODELO DE UTILIDAD (Arts. 81-87):\n"
            "- Toda nueva FORMA, configuración o disposición de elementos que confiera una "
            "ventaja técnica o funcional.\n"
            "- Requiere NOVEDAD y APLICACIÓN INDUSTRIAL (no nivel inventivo).\n"
            "- Plazo de protección: 10 AÑOS contados desde la solicitud, NO renovables.\n"
            "- Útil para mejoras menores que no llegan al umbral de patente.\n\n"
            "DISEÑO INDUSTRIAL (Arts. 113-133):\n"
            "- Apariencia particular de un producto que resulta de cualquier reunión de "
            "líneas o combinación de colores o forma externa.\n"
            "- Requisitos: NOVEDAD MUNDIAL en la fecha de prioridad.\n"
            "- Plazo de protección: 10 AÑOS contados desde la solicitud, RENOVABLES por "
            "períodos de 5 años hasta un total de 15 años.\n"
            "- Protege la estética visual del producto (forma, ornamentación).\n\n"
            "Ambos se tramitan ante la Dirección de Invenciones y Nuevas Tecnologías de "
            "INDECOPI."
        ),
    },
    {
        "article": "Derecho-Autor-Concepto",
        "section_path": "Decisión 351 + DL 822 > Derecho de autor",
        "content": (
            "DL 822 + Decisión 351 — Ley sobre el Derecho de Autor.\n"
            "PROTECCIÓN AUTOMÁTICA: el derecho de autor se otorga POR EL SOLO HECHO DE LA "
            "CREACIÓN de la obra, SIN necesidad de registro (Art. 3 DL 822). El registro en "
            "INDECOPI tiene efectos meramente probatorios.\n\n"
            "OBRAS PROTEGIDAS (Art. 5 DL 822):\n"
            "- Obras literarias, artículos, ensayos, conferencias, sermones.\n"
            "- Composiciones musicales con o sin letra.\n"
            "- Obras dramáticas, dramático-musicales, coreográficas, pantomímicas.\n"
            "- Obras audiovisuales (películas, videos).\n"
            "- Obras de las artes plásticas, pintura, dibujo, escultura, grabado, fotografía.\n"
            "- Obras de arquitectura, planos, mapas, ilustraciones.\n"
            "- Programas de ordenador (software).\n"
            "- Bases de datos originales (compilaciones, antologías).\n\n"
            "DURACIÓN:\n"
            "- VIDA DEL AUTOR + 70 AÑOS POST MORTEM.\n"
            "- Obras anónimas o pseudónimas: 70 años desde la primera publicación.\n"
            "- Obras colectivas: 70 años desde la divulgación.\n\n"
            "Tras la expiración, la obra entra al DOMINIO PÚBLICO — uso libre por cualquiera, "
            "respetando los derechos morales (paternidad, integridad)."
        ),
    },
    {
        "article": "Derechos-Patrimoniales-Morales",
        "section_path": "DL 822 > Derechos del autor",
        "content": (
            "Artículos 18-33 DL 822 — Derechos morales y patrimoniales del autor.\n\n"
            "DERECHOS MORALES (Arts. 21-25): PERPETUOS, INALIENABLES e IRRENUNCIABLES.\n"
            "1. PATERNIDAD: derecho a ser reconocido como autor de la obra.\n"
            "2. INTEGRIDAD: derecho a oponerse a deformaciones, mutilaciones o modificaciones "
            "que perjudiquen el honor o reputación del autor.\n"
            "3. DIVULGACIÓN: derecho a decidir si y cómo se divulga la obra.\n"
            "4. INÉDITO: mantener la obra inédita o retirarla del comercio.\n"
            "5. ACCESO al ejemplar original o único de la obra.\n\n"
            "DERECHOS PATRIMONIALES (Arts. 30-33): EXCLUSIVOS, TRANSMISIBLES y de duración "
            "limitada (vida + 70 años).\n"
            "1. REPRODUCCIÓN: fijación material por cualquier medio.\n"
            "2. COMUNICACIÓN PÚBLICA: representación, exhibición, radiodifusión, puesta a "
            "disposición online.\n"
            "3. DISTRIBUCIÓN: venta, alquiler, préstamo público.\n"
            "4. TRADUCCIÓN, ADAPTACIÓN, arreglo o transformación.\n"
            "5. IMPORTACIÓN: introducción de ejemplares al territorio nacional.\n\n"
            "LICENCIA: el autor puede ceder los derechos patrimoniales por escrito, con "
            "indicación expresa de las facultades cedidas, ámbito territorial, plazo y "
            "remuneración."
        ),
    },
    {
        "article": "Software-Derecho-Autor",
        "section_path": "DL 822 > Programas de ordenador",
        "content": (
            "Artículos 69-77 DL 822 — Programas de ordenador (software).\n"
            "El software se protege como OBRA LITERARIA, abarcando tanto el código fuente "
            "como el código objeto, las descripciones del programa y los materiales auxiliares "
            "(documentación técnica).\n\n"
            "TITULARIDAD POR DEFECTO:\n"
            "- Software desarrollado en el marco de una relación LABORAL: derechos "
            "patrimoniales del EMPLEADOR (Art. 71). El trabajador conserva los morales.\n"
            "- Software desarrollado bajo CONTRATO DE OBRA: derechos del COMITENTE si así se "
            "pactó expresamente; en defecto, del autor.\n"
            "- Software OPEN SOURCE: el autor mantiene la titularidad pero licencia el uso "
            "bajo términos específicos (GPL, MIT, Apache, etc.).\n\n"
            "USO PERMITIDO POR EL USUARIO LEGÍTIMO (Art. 73):\n"
            "- Una copia de respaldo (backup).\n"
            "- Adaptación necesaria para el uso conforme a su destino.\n"
            "- Corrección de errores.\n\n"
            "PIRATERÍA DE SOFTWARE: constituye delito contra los derechos intelectuales "
            "(Art. 217 CP) y genera responsabilidad civil. Fiscalización a cargo de INDECOPI "
            "y la Fiscalía Penal Especializada en Propiedad Intelectual."
        ),
    },
    {
        "article": "Accion-Infraccion",
        "section_path": "DL 1075 + DL 822 > Acción por infracción",
        "content": (
            "Acción administrativa por infracción de derechos de PI ante INDECOPI.\n"
            "COMPETENCIA: Dirección de Signos Distintivos (marcas), Dirección de Invenciones "
            "y Nuevas Tecnologías (patentes), Dirección de Derecho de Autor (autoría).\n\n"
            "MEDIDAS CAUTELARES (Art. 245 Decisión 486 + DL 1075):\n"
            "- Cese inmediato de los actos infractores.\n"
            "- Decomiso/comiso de los productos infractores y materiales usados para su "
            "elaboración.\n"
            "- Cierre temporal del establecimiento infractor.\n"
            "- Notificación a terceros (proveedores, clientes).\n\n"
            "SANCIÓN:\n"
            "- Cese definitivo de los actos infractores.\n"
            "- Multa hasta 150 UIT (revisable según gravedad y reiterancia).\n"
            "- Decomiso definitivo y destrucción de productos infractores.\n"
            "- Publicación de la sanción a costa del infractor.\n"
            "- Compensación al titular por daños y perjuicios (vía civil o como medida "
            "complementaria).\n\n"
            "VÍA PENAL PARALELA: delitos contra la propiedad industrial (Art. 222 CP) y "
            "contra los derechos de autor (Art. 217 CP)."
        ),
    },
    {
        "article": "Tratados-Internacionales",
        "section_path": "PI > Tratados internacionales",
        "content": (
            "Tratados internacionales en propiedad intelectual ratificados por el Perú.\n\n"
            "CONVENIO DE PARÍS (CUP, 1883): primer instrumento internacional sobre propiedad "
            "industrial. Establece el principio de TRATO NACIONAL (los extranjeros gozan de "
            "los mismos derechos que los nacionales) y el DERECHO DE PRIORIDAD (12 meses "
            "para patentes, 6 meses para marcas y diseños).\n\n"
            "CONVENIO DE BERNA (1886): protección de obras literarias y artísticas. Establece "
            "el principio de protección automática sin necesidad de formalidades de registro.\n\n"
            "ACUERDO ADPIC / TRIPS (1994, OMC): establece estándares mínimos de protección "
            "para todas las categorías de propiedad intelectual entre los miembros de la OMC.\n\n"
            "TRATADO DE COOPERACIÓN EN MATERIA DE PATENTES (PCT, 1970): permite presentar una "
            "única solicitud internacional de patente que produce efecto en los países "
            "designados. Tramitada a través de la OMPI.\n\n"
            "TRATADOS OMPI:\n"
            "- Tratado sobre Derechos de Autor (TODA / WCT 1996): derechos digitales.\n"
            "- Tratado sobre Interpretación o Ejecución y Fonogramas (TOIEF / WPPT 1996).\n"
            "- Tratado de Marrakech (2013): excepciones para personas con discapacidad visual.\n\n"
            "DECISIONES CAN (Comunidad Andina): Decisión 486 (PI industrial), Decisión 351 "
            "(derecho de autor), Decisión 391 (recursos genéticos), Decisión 345 (variedades "
            "vegetales) — vinculantes para Perú, Bolivia, Colombia y Ecuador."
        ),
    },
    {
        "article": "Conocimientos-Tradicionales",
        "section_path": "Ley 27811 > Conocimientos colectivos",
        "content": (
            "Ley 27811 (2002) — Protección de conocimientos colectivos de los pueblos "
            "indígenas vinculados a recursos biológicos.\n"
            "RECONOCE el derecho de los pueblos indígenas sobre sus conocimientos colectivos "
            "tradicionales relacionados con recursos biológicos.\n\n"
            "REGISTRO TRIPARTITO en INDECOPI:\n"
            "1. Registro Público — información de dominio público.\n"
            "2. Registro Confidencial — información que el pueblo no desea divulgar.\n"
            "3. Registro Nacional — gestionado por INDECOPI.\n\n"
            "CONTRATOS DE LICENCIA: cualquier uso comercial de conocimientos colectivos "
            "registrados o no, requiere LICENCIA y consentimiento previo del pueblo titular, "
            "con DISTRIBUCIÓN EQUITATIVA de beneficios.\n\n"
            "Articulada con la Decisión 391 CAN (acceso a recursos genéticos) y el Protocolo "
            "de Nagoya (Convenio sobre Diversidad Biológica).\n\n"
            "FONDO PARA EL DESARROLLO DE LOS PUEBLOS INDÍGENAS: percibe el 10% de los royalties "
            "derivados de los contratos de licencia y financia proyectos comunales."
        ),
    },
]
