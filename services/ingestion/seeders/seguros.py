"""
Seed: Derecho de Seguros (Perú).

Núcleo normativo:
    - Ley 29946 — Ley del Contrato de Seguro (LCS, vigente desde 2013)
    - Ley 26702 — LGSFS, Título VI (régimen de las empresas aseguradoras)
    - Resoluciones SBS sobre solvencia, transparencia, comercialización
    - DS 007-2017-EF — Reglamento sobre Microseguros
    - Ley 27181 + DS 024-2002-MTC — SOAT (Seguro Obligatorio de Accidentes de Tránsito)
"""

SEGUROS_ARTICLES = [
    {
        "article": "Ley-29946-Concepto",
        "section_path": "Ley 29946 > Contrato de seguro",
        "content": (
            "Artículos 1-3 Ley 29946 — Contrato de seguro.\n"
            "Es el contrato por el cual el ASEGURADOR, mediante el cobro de una PRIMA y "
            "para el caso de que se produzca un siniestro previsto, se obliga a satisfacer "
            "al ASEGURADO o al BENEFICIARIO la indemnización del daño sufrido o la "
            "prestación pactada.\n\n"
            "CARACTERES:\n"
            "1. CONSENSUAL: se perfecciona con el solo acuerdo de voluntades.\n"
            "2. BILATERAL: genera obligaciones para ambas partes.\n"
            "3. ONEROSO: ambas partes obtienen beneficios económicos.\n"
            "4. ALEATORIO: el siniestro depende del azar.\n"
            "5. DE BUENA FE REFORZADA (uberrimae fidei): exige máxima honestidad.\n"
            "6. DE ADHESIÓN: en la práctica, el asegurado se adhiere a condiciones generales "
            "predeterminadas por el asegurador.\n\n"
            "PRINCIPIOS RECTORES:\n"
            "- Principio INDEMNIZATORIO (Art. 76): el seguro debe restablecer al asegurado "
            "a su situación previa al siniestro, sin enriquecimiento.\n"
            "- Principio del INTERÉS ASEGURABLE (Art. 6): el asegurado debe tener un interés "
            "legítimo en que no se produzca el siniestro.\n"
            "- Principio de SUBROGACIÓN (Art. 138): el asegurador que paga la indemnización "
            "se subroga en los derechos del asegurado contra el tercero responsable del daño."
        ),
    },
    {
        "article": "Sujetos-del-Contrato",
        "section_path": "Ley 29946 > Sujetos del contrato",
        "content": (
            "Artículos 4-5 Ley 29946 — Sujetos intervinientes.\n"
            "1. ASEGURADOR: persona jurídica autorizada por la SBS para asumir el riesgo "
            "ajeno. En Perú existen seguros generales, seguros de vida y reaseguros.\n\n"
            "2. CONTRATANTE / TOMADOR: persona que celebra el contrato con el asegurador y "
            "se obliga al pago de la prima. Puede ser el propio asegurado o un tercero.\n\n"
            "3. ASEGURADO: titular del interés asegurable. Puede coincidir con el contratante "
            "o ser un tercero (ej. seguro de vida tomado por la empresa para un trabajador).\n\n"
            "4. BENEFICIARIO: persona designada para percibir la indemnización en caso de "
            "siniestro. En seguros de vida, suele ser distinto del asegurado (ej. familia).\n\n"
            "DESIGNACIÓN DEL BENEFICIARIO: puede ser revocable o irrevocable.\n"
            "- Revocable (default): el contratante puede modificar la designación en "
            "cualquier momento.\n"
            "- Irrevocable: requiere aceptación expresa del beneficiario; la posterior "
            "modificación necesita su consentimiento.\n\n"
            "INTERMEDIARIOS: corredores de seguros (Ley 26702 + SBS), agentes de seguros y "
            "promotores actúan bajo regulación SBS."
        ),
    },
    {
        "article": "Declaracion-Riesgo",
        "section_path": "Ley 29946 > Declaración del riesgo",
        "content": (
            "Artículos 7-12 Ley 29946 — Declaración del riesgo.\n"
            "El contratante / asegurado tiene el DEBER DE DECLARAR con exactitud todas las "
            "circunstancias por él conocidas que puedan influir en la valoración del riesgo "
            "por parte del asegurador, conforme al cuestionario presentado.\n\n"
            "RETICENCIA / DECLARACIÓN INEXACTA:\n"
            "- DOLOSA o por CULPA GRAVE: el asegurador puede RESOLVER el contrato dentro del "
            "mes desde el conocimiento del hecho. La prima se devenga hasta la resolución.\n"
            "- DE BUENA FE (sin dolo ni culpa grave): el asegurador puede MODIFICAR las "
            "condiciones (mayor prima) dentro del mes; si el contratante no acepta, el "
            "contrato se resuelve.\n\n"
            "REGLA PROPORCIONAL (Art. 11): si el siniestro ocurre antes de que el asegurador "
            "tenga conocimiento de la reticencia, la indemnización se reduce "
            "proporcionalmente entre la prima pagada y la que se habría debido pagar.\n\n"
            "MODIFICACIONES POSTERIORES (Art. 12): el contratante debe comunicar al "
            "asegurador toda circunstancia que durante la vigencia del contrato AGRAVE el "
            "riesgo asumido."
        ),
    },
    {
        "article": "Prima-Mora",
        "section_path": "Ley 29946 > Prima y mora",
        "content": (
            "Artículos 13-21 Ley 29946 — Prima del seguro.\n"
            "La PRIMA es la contraprestación que el contratante paga al asegurador a cambio "
            "de la asunción del riesgo. Se calcula sobre la base actuarial del riesgo asumido.\n\n"
            "PAGO: la prima es generalmente PAGADERA POR ADELANTADO. Puede pactarse en cuotas "
            "(fraccionamiento) o única.\n\n"
            "MORA EN EL PAGO:\n"
            "- Mora automática a partir del vencimiento del plazo.\n"
            "- SUSPENSIÓN DE LA COBERTURA: a los 30 días naturales desde el vencimiento del "
            "plazo de gracia (Art. 17). El asegurador no responde por siniestros ocurridos "
            "durante la suspensión.\n"
            "- REHABILITACIÓN: con el pago de la prima atrasada + intereses moratorios la "
            "cobertura se restablece a partir del día siguiente del pago (NO se aplica "
            "retroactivamente al período suspendido).\n"
            "- TERMINACIÓN: 90 días desde la suspensión sin haber regularizado, el contrato "
            "se da por terminado de pleno derecho.\n\n"
            "INTERÉS MORATORIO: tasa máxima convencional permitida por el BCRP (en defecto "
            "de pacto: la tasa pasiva en moneda nacional + 50%)."
        ),
    },
    {
        "article": "Siniestro-Aviso",
        "section_path": "Ley 29946 > Siniestro",
        "content": (
            "Artículos 65-75 Ley 29946 — Siniestro y obligaciones del asegurado.\n"
            "SINIESTRO: realización del riesgo previsto en el contrato.\n\n"
            "OBLIGACIONES DEL ASEGURADO AL OCURRIR EL SINIESTRO:\n"
            "1. AVISO oportuno al asegurador. Plazo legal: 3 DÍAS HÁBILES desde el "
            "conocimiento del siniestro (Art. 68), salvo que la póliza fije plazo mayor.\n"
            "2. ABSTENERSE de actos que agraven las consecuencias (deber de salvamento).\n"
            "3. PROPORCIONAR información veraz sobre las circunstancias y daños.\n"
            "4. PERMITIR la inspección del asegurador o del ajustador.\n\n"
            "OBLIGACIONES DEL ASEGURADOR:\n"
            "1. DESIGNAR AJUSTADOR si el monto reclamado supera el umbral reglamentario.\n"
            "2. PRONUNCIARSE sobre la cobertura dentro de los 20 días siguientes a la "
            "presentación de la documentación completa.\n"
            "3. PAGAR la indemnización dentro de los 30 DÍAS siguientes a la consignación del "
            "siniestro (con documentación completa).\n\n"
            "RECHAZO DE COBERTURA: debe ser fundamentado y comunicado por escrito. El asegurado "
            "puede impugnarlo ante la SBS, Defensoría del Asegurado (APESEG) o el PJ."
        ),
    },
    {
        "article": "Indemnizacion",
        "section_path": "Ley 29946 > Indemnización",
        "content": (
            "Artículos 76-94 Ley 29946 — Indemnización.\n"
            "INDEMNIZACIÓN: prestación que el asegurador debe satisfacer al ocurrir el "
            "siniestro. Se ajusta al principio indemnizatorio: el asegurado no debe "
            "enriquecerse con el seguro.\n\n"
            "SUMA ASEGURADA: valor máximo de la prestación del asegurador. Puede ser:\n"
            "- A VALOR REAL (valor de reposición / nuevo).\n"
            "- A VALOR DE USO (depreciado por uso y desgaste).\n"
            "- A VALOR CONVENIDO (pactado entre las partes — no aplica regla proporcional).\n\n"
            "INFRASEGURO (Art. 80): si la suma asegurada es INFERIOR al valor real, la "
            "indemnización se reduce proporcionalmente (regla proporcional).\n"
            "Ejemplo: bien valorizado en S/100k asegurado por S/60k → indemnización del 60% "
            "de la pérdida.\n\n"
            "SOBRESEGURO (Art. 81): si la suma asegurada SUPERA el valor real, la "
            "indemnización se limita al valor real efectivamente perdido. El contratante "
            "puede solicitar la reducción de la prima por el exceso.\n\n"
            "SEGUROS MÚLTIPLES (Art. 89): si el mismo riesgo está cubierto por varios "
            "seguros, cada asegurador responde proporcionalmente a la suma asegurada — "
            "PROHIBIDO el doble cobro por el mismo siniestro."
        ),
    },
    {
        "article": "Seguro-Vida",
        "section_path": "Ley 29946 > Seguros sobre la vida",
        "content": (
            "Artículos 156-180 Ley 29946 — Seguros sobre la vida.\n"
            "MODALIDADES:\n"
            "1. SEGURO DE VIDA TEMPORAL (TERM LIFE): cobertura por período determinado. "
            "Si el asegurado fallece dentro del plazo, los beneficiarios reciben el capital. "
            "Si sobrevive, no hay devolución.\n\n"
            "2. SEGURO DE VIDA ENTERA (WHOLE LIFE): cobertura por toda la vida del asegurado. "
            "Genera valor de rescate acumulable.\n\n"
            "3. DOTAL (ENDOWMENT): paga al beneficiario si el asegurado fallece dentro del "
            "plazo, o al propio asegurado si sobrevive al término. Mixto vida-ahorro.\n\n"
            "4. SEGURO DE RENTA VITALICIA: el asegurador paga una renta periódica al "
            "asegurado durante su vida (jubilación SPP).\n\n"
            "EXCLUSIONES TÍPICAS:\n"
            "- Suicidio dentro del primer año de vigencia (Art. 162) — devolución de la prima.\n"
            "- Pena de muerte legalmente impuesta.\n"
            "- Riesgos profesionales no declarados (deportes extremos, aviación civil).\n\n"
            "PRINCIPIO DE LIBRE DESIGNACIÓN DEL BENEFICIARIO: el asegurado puede designar "
            "libremente al beneficiario sin que importe el orden sucesorio. La indemnización "
            "se entrega DIRECTAMENTE al beneficiario, NO INTEGRA la masa hereditaria, ni "
            "responde por las deudas del causante (Art. 173)."
        ),
    },
    {
        "article": "SOAT",
        "section_path": "Ley 27181 + DS 024-2002-MTC > SOAT",
        "content": (
            "SOAT — Seguro Obligatorio de Accidentes de Tránsito.\n"
            "Establecido por Ley 27181 y reglamentado por el DS 024-2002-MTC. Aplica a TODO "
            "VEHÍCULO motorizado que circule por el territorio nacional.\n\n"
            "COBERTURA: indemniza a las víctimas (conductor, ocupantes, terceros) de "
            "accidentes de tránsito, independientemente de la responsabilidad del conductor "
            "(seguro de primera persona, no requiere imputación de culpa).\n\n"
            "PRESTACIONES (montos según escala vigente en UIT):\n"
            "1. Gastos médicos por accidentado.\n"
            "2. Incapacidad temporal y permanente.\n"
            "3. Muerte y sepelio.\n"
            "4. Asistencia médica de emergencia.\n\n"
            "PRESCRIPCIÓN: la acción para reclamar el SOAT prescribe a los DOS AÑOS desde "
            "el accidente.\n\n"
            "AFOCAT (Asociaciones de Fondos Regionales de Tránsito): los transportes urbanos "
            "(taxis, combis, motos) pueden afiliarse a un AFOCAT en lugar de SOAT — cobertura "
            "equivalente, prima reducida.\n\n"
            "SANCIONES: circular sin SOAT vigente configura infracción grave del Reglamento "
            "Nacional de Tránsito (DS 016-2009-MTC). Multa + retención del vehículo."
        ),
    },
    {
        "article": "Microseguros",
        "section_path": "DS 007-2017-EF > Microseguros",
        "content": (
            "DS 007-2017-EF — Reglamento de Microseguros.\n"
            "Productos de seguro diseñados para SEGMENTOS DE BAJOS INGRESOS, con primas "
            "asequibles (típicamente < S/30 mensuales), procedimientos simplificados y "
            "coberturas básicas.\n\n"
            "CARACTERÍSTICAS:\n"
            "1. Suma asegurada limitada (umbral máximo regulado por SBS).\n"
            "2. Póliza sencilla, redactada en lenguaje claro y comprensible.\n"
            "3. Sin exclusiones complejas — coberturas básicas: muerte accidental, "
            "hospitalización por accidente, robo simple.\n"
            "4. Procedimiento simplificado de reclamación: plazos reducidos, documentación "
            "mínima.\n"
            "5. Pago de indemnización rápido — máximo 10 días desde reclamación.\n\n"
            "CANALES DE DISTRIBUCIÓN: bancos masivos, cajas municipales, microfinancieras, "
            "tiendas por departamento, supermercados, telefonía móvil. La SBS exige que el "
            "personal de venta esté DEBIDAMENTE CAPACITADO en el producto.\n\n"
            "EXENCIÓN TRIBUTARIA: los microseguros gozan de EXONERACIÓN del IGV (Art. 5 "
            "Ley 30822) para promover su acceso a poblaciones vulnerables."
        ),
    },
    {
        "article": "Defensoria-Asegurado",
        "section_path": "APESEG > Defensoría del Asegurado",
        "content": (
            "Defensoría del Asegurado — APESEG (Asociación Peruana de Empresas de Seguros).\n"
            "Es una instancia GRATUITA de resolución de controversias entre asegurados y "
            "aseguradoras antes de acudir a la SBS o al Poder Judicial.\n\n"
            "REQUISITOS PARA ACUDIR:\n"
            "1. El asegurado debe haber reclamado previamente al asegurador y NO HABER "
            "RECIBIDO RESPUESTA SATISFACTORIA dentro de 30 días.\n"
            "2. La cuantía del reclamo debe ser INFERIOR a 50 UIT (cuantía ajustable).\n"
            "3. El siniestro/controversia debe haber ocurrido dentro del territorio peruano.\n\n"
            "TRÁMITE:\n"
            "1. Presentación del reclamo a la Defensoría con la documentación pertinente.\n"
            "2. La Defensoría notifica al asegurador, que tiene 15 días para responder.\n"
            "3. Audiencia conciliatoria — si hay acuerdo, se firma acta.\n"
            "4. Si no hay acuerdo, el Defensor emite un PRONUNCIAMIENTO MOTIVADO no vinculante "
            "para el asegurador pero VINCULANTE para la APESEG miembro.\n\n"
            "PLAZO MÁXIMO: 90 días desde la admisión del reclamo. Si el asegurado no queda "
            "satisfecho con el pronunciamiento, puede acudir a la SBS o al PJ."
        ),
    },
    {
        "article": "Prescripcion-Seguros",
        "section_path": "Ley 29946 > Prescripción",
        "content": (
            "Artículos 95-99 Ley 29946 — Prescripción de acciones del contrato de seguro.\n"
            "PLAZO GENERAL: 2 AÑOS desde el conocimiento del hecho que la motiva.\n\n"
            "Para acciones derivadas de:\n"
            "- Reclamación de indemnización por siniestro: 2 años desde el siniestro o desde "
            "el conocimiento del derecho.\n"
            "- Acción del asegurador contra el contratante (cobro de prima, repetición de "
            "pago indebido): 2 años.\n"
            "- Acción de subrogación contra el tercero responsable: 2 años desde el pago de "
            "la indemnización.\n\n"
            "EXCEPCIONES (Art. 96):\n"
            "- Beneficiario menor de edad: el plazo no corre durante la minoría.\n"
            "- Estado de inconsciencia o impedimento: el plazo se suspende.\n\n"
            "INTERRUPCIÓN DE LA PRESCRIPCIÓN:\n"
            "- Reclamación formal al asegurador.\n"
            "- Acción ante la SBS, Defensoría del Asegurado o INDECOPI.\n"
            "- Demanda judicial.\n"
            "- Reconocimiento expreso de la deuda por el asegurador."
        ),
    },
    {
        "article": "Cobertura-Exclusiones",
        "section_path": "Ley 29946 > Cláusulas de cobertura y exclusión",
        "content": (
            "Cláusulas de cobertura, exclusiones y limitaciones (Ley 29946 + Resolución SBS "
            "3199-2013 sobre transparencia).\n\n"
            "PÓLIZA: documento escrito que contiene las condiciones generales (impresas) y "
            "particulares (negociadas) del contrato.\n\n"
            "OBLIGACIONES DE TRANSPARENCIA DEL ASEGURADOR:\n"
            "1. Entregar la póliza al contratante en un plazo de 15 DÍAS desde la celebración.\n"
            "2. Destacar en CARACTERES NEGRITAS las exclusiones, limitaciones y cargas que "
            "imponga al asegurado.\n"
            "3. Indicar los procedimientos para presentar reclamos y los plazos del seguro.\n\n"
            "EXCLUSIONES TÍPICAS (variables por ramo):\n"
            "- Riesgos no asegurables: dolo del asegurado, actos de guerra, terrorismo "
            "(salvo cobertura específica), riesgo nuclear, contaminación radiactiva.\n"
            "- Riesgos pre-existentes no declarados.\n"
            "- Daños indirectos o consecuenciales (salvo pacto expreso).\n\n"
            "CLÁUSULAS ABUSIVAS: las cláusulas que desnaturalicen el contrato o limiten "
            "indebidamente los derechos del asegurado son NULAS DE PLENO DERECHO (Art. 3 "
            "Ley 29946 + Art. 50 Ley 29571). La SBS y el INDECOPI tienen competencia para "
            "declarar su inaplicabilidad."
        ),
    },
]
