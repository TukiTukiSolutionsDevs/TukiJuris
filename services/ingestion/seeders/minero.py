"""
Seed: Derecho Minero (Perú).

Núcleo normativo:
    - TUO de la Ley General de Minería (DS 014-92-EM)
    - DS 018-92-EM — Reglamento de Procedimientos Mineros
    - Ley 28090 — Plan de Cierre de Minas
    - Ley 28271 — Pasivos Ambientales Mineros (PAM)
    - Ley 29789 — Impuesto Especial a la Minería (IEM)
    - Ley 29790 — Gravamen Especial a la Minería (GEM)
    - Ley 28258 — Regalía minera
    - DL 1336 — Formalización Minera Integral (MAPE)
    - DL 1100 — Lucha contra la minería ilegal en zonas amazónicas
"""

MINERO_ARTICLES = [
    {
        "article": "TUO-LGM-Concesion",
        "section_path": "TUO LGM > Concesión minera",
        "content": (
            "Artículos 9-24 TUO LGM (DS 014-92-EM) — Concesión minera.\n"
            "La CONCESIÓN MINERA otorga a su titular el DERECHO EXCLUSIVO a la exploración y "
            "explotación de los recursos minerales concedidos, dentro de un área específica y "
            "por tiempo indefinido, sujeta al pago oportuno del derecho de vigencia y "
            "penalidades.\n\n"
            "CARACTERÍSTICAS:\n"
            "1. Es un DERECHO REAL distinto e independiente del derecho de propiedad del "
            "predio donde se ubica.\n"
            "2. Es INDIVISIBLE como unidad de producción.\n"
            "3. Es TRANSFERIBLE por acto entre vivos o mortis causa, mediante escritura "
            "pública e inscripción en el catastro minero.\n"
            "4. Se confiere por UNIDADES DE 100 HECTÁREAS contiguas (mínimo).\n\n"
            "EXTENSIÓN MÁXIMA: 1,000 hectáreas para concesiones metálicas y 100 hectáreas para "
            "concesiones no metálicas.\n\n"
            "TIPOS DE CONCESIÓN:\n"
            "- Concesión minera (exploración y explotación).\n"
            "- Concesión de beneficio (planta de tratamiento).\n"
            "- Concesión de labor general (servicios auxiliares).\n"
            "- Concesión de transporte minero (transporte de minerales por medios no "
            "convencionales)."
        ),
    },
    {
        "article": "Petitorio-Minero",
        "section_path": "DS 018-92-EM > Procedimiento de petitorio",
        "content": (
            "Procedimiento ordinario minero — Petitorio (DS 018-92-EM).\n"
            "FASE 1 — Solicitud (Petitorio):\n"
            "- Presentación ante el Instituto Geológico, Minero y Metalúrgico (INGEMMET) o la "
            "Dirección Regional de Energía y Minas (DREM) según la jurisdicción.\n"
            "- Indicación de coordenadas UTM, área (en hectáreas), nombre de la concesión y "
            "datos del solicitante.\n"
            "- Pago del derecho de trámite.\n\n"
            "FASE 2 — Publicación y oposición:\n"
            "- Publicación de avisos en El Peruano y diario regional.\n"
            "- Plazo de OPOSICIÓN: 30 días desde la última publicación.\n\n"
            "FASE 3 — Resolución y título:\n"
            "- Si no hay oposición o se resuelve, INGEMMET expide el TÍTULO DE CONCESIÓN MINERA.\n"
            "- Inscripción del título en el Registro de Derechos Mineros de SUNARP.\n\n"
            "DERECHO DE VIGENCIA: pago anual obligatorio (US$ 3 por hectárea/año para "
            "régimen general; US$ 1 para pequeña minería; US$ 0.50 para minería artesanal). "
            "Vencimiento: 30 de junio de cada año. Su impago por 2 años consecutivos genera "
            "extinción de la concesión."
        ),
    },
    {
        "article": "Actividades-Mineras",
        "section_path": "TUO LGM > Actividades mineras",
        "content": (
            "Artículos 5-8 TUO LGM — Clasificación de actividades mineras.\n\n"
            "1. CATEO Y PROSPECCIÓN: actividades exploratorias preliminares no requieren "
            "concesión, salvo en áreas protegidas o concesionadas a terceros.\n\n"
            "2. EXPLORACIÓN: identificación y delimitación de yacimientos. Requiere CONCESIÓN "
            "y autorización ambiental (DIA / EIA-sd / EIA-d según la magnitud).\n\n"
            "3. EXPLOTACIÓN: extracción de los minerales. Bajo el mismo título de concesión "
            "minera. Requiere autorización de operación y plan de minado.\n\n"
            "4. BENEFICIO: tratamiento metalúrgico para concentrar los minerales. Requiere "
            "CONCESIÓN DE BENEFICIO independiente y EIA específico de planta.\n\n"
            "5. LABOR GENERAL: actividades auxiliares (drenaje, ventilación, transporte "
            "interno). Concesión de labor general en zonas de varias concesiones colindantes.\n\n"
            "6. TRANSPORTE MINERO: por relaves o conductos a distancia. Concesión específica.\n\n"
            "7. COMERCIALIZACIÓN: libre (no requiere concesión) pero sujeta a obligaciones de "
            "declaración SUNAT y MINEM (Sistema de Información Minera Regional)."
        ),
    },
    {
        "article": "Estratos-Mineros",
        "section_path": "TUO LGM > Estratos de la minería",
        "content": (
            "Estratificación de la actividad minera por escala (Art. 91 TUO LGM modificado).\n\n"
            "GRAN MINERÍA: más de 5,000 TM/día de capacidad instalada. Régimen tributario "
            "general + estabilidad jurídica + EIA-d obligatorio. Predominio en Cu, Au, Zn, Pb, Mo.\n\n"
            "MEDIANA MINERÍA: entre 350 y 5,000 TM/día. Régimen general. EIA-d.\n\n"
            "PEQUEÑA MINERÍA (PM): hasta 350 TM/día y hasta 2,000 ha de concesión. EIA-sd. "
            "Régimen tributario especial (escalas reducidas).\n\n"
            "MINERÍA ARTESANAL (MA): hasta 25 TM/día y hasta 1,000 ha. Régimen formalizado "
            "(DL 1336). DIA simplificada.\n\n"
            "MAPE — Pequeña Minería y Minería Artesanal: marco normativo especial bajo el "
            "DL 1336 (2017) con incentivos de formalización: simplificación de procedimientos, "
            "facilidades tributarias, asistencia técnica del MINEM.\n\n"
            "REINEM (Registro Integral de Formalización Minera): instrumento de control donde "
            "se inscriben los mineros formales en proceso. La inscripción REINEM acredita la "
            "condición legal del minero ante SUNAT, SUNAFIL, BANCO, etc."
        ),
    },
    {
        "article": "Servidumbre-Minera",
        "section_path": "TUO LGM > Servidumbres",
        "content": (
            "Artículos 37-43 TUO LGM — Servidumbres mineras.\n"
            "El titular de la concesión minera tiene DERECHO A LA SERVIDUMBRE sobre los "
            "predios superficiales necesarios para la actividad minera, previo pago de la "
            "compensación al propietario.\n\n"
            "TIPOS DE SERVIDUMBRE MINERA:\n"
            "1. De paso (acceso a la concesión).\n"
            "2. De acueducto (canalización de agua).\n"
            "3. De ocupación temporal (campamentos, plantas).\n"
            "4. De ocupación permanente (operación industrial).\n\n"
            "ESTABLECIMIENTO DE LA SERVIDUMBRE:\n"
            "- POR ACUERDO entre el concesionario y el propietario del predio superficial "
            "(escritura pública e inscripción registral).\n"
            "- POR RESOLUCIÓN del Consejo Nacional de Minería ante la falta de acuerdo, "
            "previo informe técnico de INGEMMET y pago de la compensación.\n\n"
            "INDEMNIZACIÓN: valor del predio o el daño causado, fijado por peritos. Comprende "
            "el lucro cesante y el valor de mercado.\n\n"
            "POSESIÓN AGRARIA / COMUNIDADES CAMPESINAS: las servidumbres sobre territorios "
            "comunales requieren previa CONSULTA PREVIA conforme Convenio 169 OIT y Ley 29785, "
            "y acuerdos comunales (Ley 26505 sobre tierras de comunidades campesinas)."
        ),
    },
    {
        "article": "Estabilidad-Jurídica",
        "section_path": "TUO LGM > Estabilidad tributaria",
        "content": (
            "Régimen de estabilidad jurídica y tributaria minera (TUO LGM + DL 757).\n\n"
            "ESTABILIDAD GENERAL (Art. 78 TUO LGM): contratos por 10 años garantizan al "
            "titular: estabilidad del régimen tributario, libre disponibilidad de divisas, "
            "libre comercialización de productos, régimen cambiario y tributario aplicable a "
            "exportadores.\n\n"
            "ESTABILIDAD AMPLIADA (Art. 82): contratos por 15 años para proyectos con "
            "inversión SUPERIOR a US$ 500 millones. Incluye estabilidad ADICIONAL sobre el "
            "régimen administrativo de evaluación ambiental y normas de exportación.\n\n"
            "REQUISITOS PARA SUSCRIBIR CONTRATO DE ESTABILIDAD:\n"
            "1. Inversión mínima conforme la escala de la mina.\n"
            "2. Aprobación del estudio de factibilidad y del EIA-d.\n"
            "3. Aprobación del proyecto de operación.\n"
            "4. Garantía de cumplimiento (mecanismo financiero).\n\n"
            "RENUNCIA: el titular puede renunciar a la estabilidad para acogerse al régimen "
            "general posterior si éste le es más favorable.\n\n"
            "Crítica: el régimen ha sido cuestionado por organizaciones civiles por congelar "
            "tasas tributarias en períodos de boom de precios."
        ),
    },
    {
        "article": "Ley-28258-Regalia",
        "section_path": "Ley 28258 > Regalía minera",
        "content": (
            "Ley 28258 (2004) — Regalía minera.\n"
            "Contraprestación económica que los titulares de concesiones mineras pagan al "
            "Estado por la explotación de los recursos minerales metálicos y no metálicos.\n\n"
            "BASE DE CÁLCULO: VALOR de la PRODUCCIÓN VENDIDA. Se aplica una escala "
            "progresiva sobre la Utilidad Operativa Trimestral:\n"
            "- 1% si la utilidad operativa es hasta US$ 60 millones / año.\n"
            "- 2% entre US$ 60 - US$ 120 millones / año.\n"
            "- 3% sobre la utilidad operativa que exceda US$ 120 millones / año.\n\n"
            "REGALÍA MÍNIMA: 1% del valor de la producción concentrada — pago mínimo "
            "garantizado aún en períodos de baja rentabilidad.\n\n"
            "EXCLUSIONES:\n"
            "- Pequeña minería y minería artesanal (formalizados).\n"
            "- Productores de minerales no metálicos para construcción local.\n\n"
            "DESTINO DE LOS RECURSOS: el 100% se distribuye entre los gobiernos regionales y "
            "locales del área de influencia del proyecto minero, conforme al Sistema Nacional "
            "de Inversión Pública (proyectos de salud, educación, infraestructura)."
        ),
    },
    {
        "article": "IEM-GEM",
        "section_path": "Ley 29789 + Ley 29790 > IEM y GEM",
        "content": (
            "Tributos mineros adicionales — IEM y GEM (Leyes 29789 y 29790, 2011).\n\n"
            "IMPUESTO ESPECIAL A LA MINERÍA (IEM) — Ley 29789:\n"
            "- Tributo aplicable a empresas mineras SIN convenio de estabilidad jurídica.\n"
            "- Base de cálculo: utilidad operativa trimestral del titular.\n"
            "- Escala progresiva del 2% al 8.4% sobre la utilidad operativa.\n"
            "- Recaudado por SUNAT — destinado al Fisco Nacional.\n\n"
            "GRAVAMEN ESPECIAL A LA MINERÍA (GEM) — Ley 29790:\n"
            "- Aplicable a empresas mineras que SÍ TIENEN convenio de estabilidad jurídica.\n"
            "- Se establece mediante CONVENIO VOLUNTARIO entre el Estado y la empresa, dado "
            "que la estabilidad impide aplicar el IEM como tributo nuevo.\n"
            "- Tasas equivalentes a las del IEM, aplicadas vía convenio.\n\n"
            "PROPÓSITO POLÍTICO: capturar parte de las rentas extraordinarias del boom de "
            "minerales 2003-2014, sin violar la estabilidad jurídica de los contratos previos.\n\n"
            "PRESCRIPCIÓN tributaria: 4 años (Código Tributario, DS 133-2013-EF Art. 43)."
        ),
    },
    {
        "article": "Cierre-Minas",
        "section_path": "Ley 28090 > Plan de cierre",
        "content": (
            "Ley 28090 (2003) — Plan de Cierre de Minas.\n"
            "Obligación de TODO TITULAR de actividad minera de elaborar y ejecutar un PLAN "
            "DE CIERRE de la unidad minera al concluir las operaciones, a fin de prevenir o "
            "remediar los impactos ambientales y sociales remanentes.\n\n"
            "CONTENIDO DEL PLAN:\n"
            "1. Descripción de la unidad minera y sus componentes.\n"
            "2. Identificación de los impactos a remediar.\n"
            "3. Acciones técnicas de cierre (estabilización física y geoquímica).\n"
            "4. Plan de monitoreo post-cierre (5 años mínimo).\n"
            "5. Plan de revegetación y rehabilitación de suelos.\n"
            "6. Programa de cierre social (reinserción laboral, transferencia de "
            "infraestructura social a la comunidad).\n\n"
            "GARANTÍA DEL CIERRE: el titular debe constituir una GARANTÍA FINANCIERA (carta "
            "fianza, seguro de caución o fideicomiso) equivalente al costo del cierre "
            "estimado, actualizada periódicamente.\n\n"
            "PRESENTACIÓN: el Plan se presenta junto con el EIA y se actualiza cada 5 años "
            "o cuando ocurra una modificación significativa. Aprobación de MINEM con opinión "
            "técnica de OEFA.\n\n"
            "CIERRE PROGRESIVO: las actividades de cierre pueden ejecutarse de forma "
            "progresiva durante la vida útil del proyecto, no solo al final."
        ),
    },
    {
        "article": "PAM-Ley-28271",
        "section_path": "Ley 28271 > Pasivos Ambientales Mineros",
        "content": (
            "Ley 28271 (2004) — Pasivos Ambientales Mineros (PAM).\n"
            "PAM: instalaciones, efluentes, emisiones, restos o depósitos de residuos PRODUCIDOS "
            "POR OPERACIONES MINERAS ABANDONADAS o INACTIVAS que constituyen un riesgo "
            "permanente y potencial para la salud humana, los ecosistemas y la propiedad.\n\n"
            "INVENTARIO NACIONAL DE PAM: registro oficial mantenido por MINEM, con "
            "clasificación por nivel de riesgo (alto, medio, bajo). Al 2024 existen >7,000 PAM "
            "identificados en el país.\n\n"
            "RESPONSABILIDAD POR LA REMEDIACIÓN:\n"
            "1. PRIMARIA: el TITULAR HISTÓRICO causante del PAM, si es identificable.\n"
            "2. SUBSIDIARIA: el Estado, a través del Fondo Nacional del Ambiente — FONAM y la "
            "Empresa Estatal Activos Mineros SAC, cuando el causante es desconocido o "
            "insolvente.\n\n"
            "REMEDIACIÓN VOLUNTARIA INCENTIVADA: terceros (incluidos titulares mineros "
            "actuales) pueden asumir voluntariamente la remediación a cambio de beneficios "
            "tributarios (deducción de costos como gasto, certificados ambientales transferibles).\n\n"
            "Activos Mineros SAC: empresa pública dedicada a la rehabilitación de PAM "
            "huérfanos prioritarios (Quiulacocha, Ticapampa, Toromocho, El Dorado, etc.).\n\n"
            "FISCALIZACIÓN: OEFA verifica el cumplimiento y aplica sanciones por incumplimiento."
        ),
    },
    {
        "article": "DL-1336-MAPE",
        "section_path": "DL 1336 > Formalización minera",
        "content": (
            "DL 1336 (2017) — Procedimiento de Formalización Minera Integral.\n"
            "Régimen excepcional dirigido a la PEQUEÑA MINERÍA Y MINERÍA ARTESANAL (PMMA / "
            "MAPE) para regularizar su situación legal y reducir la informalidad.\n\n"
            "PASOS DE LA FORMALIZACIÓN:\n"
            "1. INSCRIPCIÓN EN EL REINEM (Registro Integral de Formalización Minera).\n"
            "2. ACREDITACIÓN DE PROPIEDAD O AUTORIZACIÓN del propietario del terreno superficial.\n"
            "3. ACREDITACIÓN DE EXPLOTACIÓN sobre concesión minera vigente (propia, en cesión "
            "o por contrato de explotación).\n"
            "4. APROBACIÓN DEL IGAFOM (Instrumento de Gestión Ambiental y Fiscalización para "
            "la Formalización Minera) — versión simplificada de EIA para MAPE.\n"
            "5. AUTORIZACIÓN DE INICIO DE OPERACIONES.\n"
            "6. INSCRIPCIÓN como contribuyente activo en SUNAT.\n\n"
            "BENEFICIOS DE LA FORMALIZACIÓN:\n"
            "- Acceso a crédito formal y mercados.\n"
            "- Exoneración de IGV en compras (régimen especial).\n"
            "- Asistencia técnica del MINEM y de los gobiernos regionales.\n"
            "- Participación en el FONDO DE RECONVERSIÓN PRODUCTIVA.\n\n"
            "PLAZO: el procedimiento ha sido AMPLIADO POR SUCESIVOS DL — última extensión "
            "hasta diciembre de 2027 (verificar normativa vigente)."
        ),
    },
    {
        "article": "Mineria-Ilegal",
        "section_path": "DL 1100 + Art. 307-A CP > Minería ilegal",
        "content": (
            "Lucha contra la minería ILEGAL (DL 1100 + Art. 307-A CP).\n\n"
            "MINERÍA ILEGAL vs INFORMAL:\n"
            "- INFORMAL: actividad minera sin cumplir todos los requisitos legales pero que "
            "ESTÁ EN PROCESO DE FORMALIZACIÓN (REINEM) — sancionada administrativamente.\n"
            "- ILEGAL: actividad minera realizada EN ZONAS PROHIBIDAS (áreas naturales "
            "protegidas, zonas amazónicas restringidas) o SIN INTENCIÓN DE FORMALIZARSE — "
            "constituye DELITO PENAL.\n\n"
            "DL 1100 (2012): suspende la actividad minera en zonas amazónicas (Madre de "
            "Dios principalmente). Autoriza al Estado a EJECUTAR INTERDICCIONES — destrucción "
            "de maquinaria (dragas, retroexcavadoras, motobombas, cargadores frontales) usada "
            "en minería ilegal por las FF.AA., PNP y Fiscalía.\n\n"
            "DELITO DE MINERÍA ILEGAL (Art. 307-A CP):\n"
            "- El que realiza actividad minera sin autorización, en áreas no permitidas, o "
            "incumpliendo la normativa, causando perjuicio al medio ambiente: pena privativa "
            "de libertad de 4 a 8 años.\n"
            "- AGRAVANTES (Art. 307-B): uso de mercurio o cianuro, área natural protegida, "
            "tierras de comunidades indígenas, participación de funcionario público o "
            "miembro de organización criminal — pena de 8 a 10 años.\n\n"
            "DECOMISO PERMANENTE de maquinaria y bienes utilizados en el delito (Art. 307-D)."
        ),
    },
]
