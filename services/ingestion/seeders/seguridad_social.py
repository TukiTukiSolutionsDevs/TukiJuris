"""
Seed: Seguridad Social y Pensiones (Perú).

Núcleo normativo:
    - DL 19990 — Sistema Nacional de Pensiones (SNP / ONP)
    - DL 25897 — Sistema Privado de Pensiones (SPP / AFP)
    - Ley 26790 — Modernización de la Seguridad Social en Salud (EsSalud)
    - Ley 28991 — Libre desafiliación informada del SPP
    - Ley 30425 — Disposición del 95.5% del fondo AFP al jubilarse
    - Ley 29903 — Reforma del SPP
"""

SEGURIDAD_SOCIAL_ARTICLES = [
    {
        "article": "DL-19990-A1",
        "section_path": "DL 19990 > SNP > Fundamentos",
        "content": (
            "DL 19990 (1973) — Sistema Nacional de Pensiones de la Seguridad Social (SNP).\n"
            "Es el sistema público de pensiones administrado por la ONP (Oficina de "
            "Normalización Previsional). Régimen contributivo, solidario y de reparto.\n"
            "AFILIACIÓN: obligatoria para trabajadores dependientes del sector privado y "
            "público (DL 728 y Ley 30057 cuando no se hayan afiliado al SPP).\n"
            "APORTE: 13% mensual de la remuneración asegurable, asumido íntegramente por el "
            "trabajador (descuento por planilla).\n"
            "PRESTACIONES: pensión de jubilación, invalidez, sobrevivencia (viudez, orfandad, "
            "ascendientes), capital de defunción."
        ),
    },
    {
        "article": "DL-19990-A38",
        "section_path": "DL 19990 > SNP > Jubilación",
        "content": (
            "Artículo 38 DL 19990.- Pensión de jubilación general SNP.\n"
            "REQUISITOS:\n"
            "1. 65 años de edad cumplidos.\n"
            "2. 20 años de aportes acreditados.\n\n"
            "MONTO: 30% de la remuneración de referencia + 2% por cada año adicional sobre "
            "los 20 años, hasta un tope de 100%. La remuneración de referencia se calcula con "
            "el promedio de los últimos 60 meses aportados.\n\n"
            "TOPES VIGENTES (revisar valor anual): pensión mínima S/ 600 y pensión máxima "
            "S/ 893 al 2026 (ajustados periódicamente). Ley 32123 amplió beneficios para "
            "ciertos grupos.\n\n"
            "JUBILACIÓN ADELANTADA: 55 años (mujeres) / 60 años (hombres), con 30 años de "
            "aportes — el monto se reduce 4% por cada año de adelanto."
        ),
    },
    {
        "article": "DL-25897-A1",
        "section_path": "DL 25897 > SPP > Fundamentos",
        "content": (
            "DL 25897 (1992) — Sistema Privado de Pensiones (SPP).\n"
            "Régimen de CAPITALIZACIÓN INDIVIDUAL administrado por las AFP (Administradoras "
            "de Fondos de Pensiones), supervisado por la SBS.\n"
            "APORTE OBLIGATORIO: 10% de la remuneración asegurable a la Cuenta Individual de "
            "Capitalización (CIC) + comisión de la AFP + prima de seguros previsionales.\n"
            "COMISIÓN AFP: existen 2 esquemas — comisión por flujo (% sobre remuneración) o "
            "comisión por saldo (% sobre el fondo acumulado).\n"
            "MULTIFONDOS: tres fondos según perfil de riesgo — Fondo 1 (conservador), Fondo 2 "
            "(mixto, por defecto), Fondo 3 (apreciación de capital, mayor riesgo). Los "
            "afiliados próximos a jubilarse migran obligatoriamente al Fondo 0/1."
        ),
    },
    {
        "article": "Ley-26790-A12",
        "section_path": "Ley 26790 > EsSalud",
        "content": (
            "Ley 26790 (1997) — Modernización de la Seguridad Social en Salud.\n"
            "ESSALUD ofrece prestaciones de salud a los afiliados regulares (trabajadores "
            "dependientes y sus derechohabientes), afiliados potestativos y agrarios.\n"
            "APORTE: 9% de la remuneración mensual, ASUMIDO POR EL EMPLEADOR (no se descuenta "
            "al trabajador).\n"
            "PRESTACIONES:\n"
            "1. Promoción de la salud y prevención.\n"
            "2. Recuperación de la salud (consultas, hospitalización, intervenciones).\n"
            "3. Maternidad (98 días — Ley 30367 prenatal y postnatal).\n"
            "4. Prestaciones económicas (subsidios).\n"
            "5. Prestaciones sociales y de bienestar.\n\n"
            "EPS (Entidades Prestadoras de Salud): el empleador puede contratar una EPS para "
            "que asuma parte de las prestaciones a cambio del 25% del aporte del 9% — el "
            "trabajador conserva su afiliación a EsSalud."
        ),
    },
    {
        "article": "Subsidios-EsSalud",
        "section_path": "Ley 26790 > Subsidios económicos",
        "content": (
            "Subsidios EsSalud (Ley 26790 + DS 020-2006-TR).\n"
            "1. SUBSIDIO POR INCAPACIDAD TEMPORAL: cubre los primeros 11 meses 10 días de "
            "incapacidad para el trabajo, después del día 21 de iniciada la incapacidad "
            "(los primeros 20 días los paga el empleador). Equivale al promedio de las "
            "últimas 12 remuneraciones.\n"
            "2. SUBSIDIO POR MATERNIDAD: 98 días remunerados (49 prenatal + 49 postnatal). "
            "El cálculo es el promedio de las últimas 12 remuneraciones.\n"
            "3. SUBSIDIO POR LACTANCIA: 1 UIT por hijo nacido, pagado por EsSalud al término "
            "del periodo de licencia.\n"
            "4. SUBSIDIO POR SEPELIO: monto fijado por EsSalud al cónyuge o concubino "
            "supérstite que se haga cargo del entierro.\n\n"
            "Trámite: solicitud a EsSalud con CITT (Certificado de Incapacidad Temporal) o "
            "partida de nacimiento/matrimonio/defunción según corresponda."
        ),
    },
    {
        "article": "Pension-Invalidez",
        "section_path": "DL 19990 + DL 25897 > Pensión de invalidez",
        "content": (
            "Pensión de invalidez (DL 19990 Arts. 25-37 + DL 25897 Arts. 113-120).\n"
            "SNP: Procede cuando el asegurado se encuentra incapacitado para el trabajo, en "
            "forma permanente, en un porcentaje igual o superior al 50% (invalidez parcial) o "
            "al 66% (invalidez total). Se requiere certificación por la Comisión Médica de "
            "Evaluación de Incapacidades del MINSA, ONP o EsSalud (COMEC).\n\n"
            "SPP: Cobertura del Seguro de Invalidez, Sobrevivencia y Gastos de Sepelio "
            "(SISGS) cuando el afiliado tiene la cobertura vigente. Requiere certificación "
            "por la COMEC y solicitar el dictamen del Comité Médico del SPP (COMAFP/COMEC SPP).\n\n"
            "MONTO: SNP — 50% de remuneración de referencia + bonificaciones. SPP — pensión "
            "según los fondos acumulados + aporte adicional del SISGS para alcanzar el monto "
            "equivalente al 70% de la remuneración promedio."
        ),
    },
    {
        "article": "Pension-Sobrevivencia",
        "section_path": "DL 19990 + DL 25897 > Sobrevivencia",
        "content": (
            "Pensión de sobrevivencia (Arts. 51-58 DL 19990 + Arts. 113-120 DL 25897).\n"
            "BENEFICIARIOS POR ORDEN:\n"
            "1. Viuda/viudo o concubino reconocido (Ley 29560 + jurisprudencia TC).\n"
            "2. Hijos menores de edad o mayores con incapacidad permanente.\n"
            "3. Hijos hasta los 25 años cursando estudios superiores.\n"
            "4. Padres dependientes económicamente del causante.\n\n"
            "MONTO TÍPICO:\n"
            "- Viudez: 50% de la pensión que recibía/correspondía al causante.\n"
            "- Orfandad: 20% por cada hijo, con tope global del 100%.\n"
            "- Ascendientes: en defecto de viuda e hijos.\n\n"
            "REQUISITO: el causante debió tener aportes vigentes o estar pensionado al momento "
            "del fallecimiento."
        ),
    },
    {
        "article": "Bono-Reconocimiento",
        "section_path": "DL 25897 + Ley 26790 > Bono de Reconocimiento",
        "content": (
            "Bono de Reconocimiento — BR (Art. 9 DL 25897).\n"
            "Es el reconocimiento monetario que efectúa el SNP al afiliado que se traslada "
            "al SPP, computando los aportes efectuados al SNP antes de su afiliación al SPP.\n"
            "REQUISITOS:\n"
            "1. Haber aportado mínimo 48 meses al SNP en los últimos 10 años anteriores al "
            "traslado al SPP.\n"
            "2. La remuneración promedio del último año de aporte al SNP determina el monto.\n\n"
            "TIPOS DE BR:\n"
            "- BR 1992: para quienes se afiliaron al SPP entre 1993 y 2001.\n"
            "- BR 1996: para quienes aportaron al SNP entre 1992 y 2001.\n"
            "- BR 2001: para quienes aportaron al SNP entre 1997 y 2001.\n\n"
            "El BR se redime al momento de la jubilación o invalidez del afiliado, "
            "incorporándose a su CIC."
        ),
    },
    {
        "article": "Ley-28991",
        "section_path": "Ley 28991 > Libre desafiliación SPP",
        "content": (
            "Ley 28991 (2007) — Libre desafiliación informada del SPP.\n"
            "Permite a los afiliados al SPP regresar al SNP en supuestos específicos:\n"
            "1. Afiliados con derecho a percibir una pensión en el SNP (60 años con 20 años de "
            "aportes), si así lo solicitan.\n"
            "2. Trabajadores que realizan labores de riesgo (Ley 25009 — trabajos mineros, "
            "metalúrgicos y siderúrgicos) y desean acogerse al SNP.\n"
            "3. Afiliados que fueron MAL INFORMADOS al momento de afiliarse al SPP — requiere "
            "acreditarlo ante la SBS.\n\n"
            "TRÁMITE: solicitud ante la AFP, que la deriva al MEF y a la ONP. Se compara la "
            "pensión que recibiría en cada sistema. Si el SNP es más beneficioso, procede la "
            "desafiliación. Los fondos de la CIC se transfieren a la ONP."
        ),
    },
    {
        "article": "Ley-30425",
        "section_path": "Ley 30425 > Disposición del 95.5% AFP",
        "content": (
            "Ley 30425 (2016) — Disposición del 95.5% del fondo AFP al jubilarse.\n"
            "Modifica el Art. 40 del DL 25897 — TUO del SPP.\n"
            "Al cumplir los 65 años de edad o tener derecho a jubilación anticipada, el "
            "afiliado al SPP puede DISPONER HASTA EL 95.5% del fondo acumulado en su CIC, "
            "en lugar de contratar una pensión vitalicia.\n\n"
            "REQUISITOS:\n"
            "1. Tener 65 años cumplidos.\n"
            "2. Solicitar a la AFP la disposición.\n"
            "3. La AFP debe brindar asesoría sobre las consecuencias previsionales.\n\n"
            "EL 4.5% RESTANTE se destina obligatoriamente a EsSalud para que el jubilado "
            "mantenga cobertura de salud durante toda su vida.\n\n"
            "RETIROS EXTRAORDINARIOS: leyes especiales han permitido retiros parciales por "
            "causas excepcionales (COVID, crisis económica, etc.) — ver legislación vigente "
            "en cada caso (Ley 31192, Ley 31478, etc.)."
        ),
    },
    {
        "article": "PEA-Independiente",
        "section_path": "DL 19990 + Ley 26790 > Trabajadores independientes",
        "content": (
            "Régimen previsional de trabajadores independientes (PEA no asalariada).\n"
            "AFILIACIÓN POTESTATIVA: los trabajadores independientes (cuarta categoría, "
            "comerciantes, profesionales) pueden afiliarse voluntariamente al SNP o al SPP.\n\n"
            "SNP — aporte mensual sobre una remuneración asegurable mínima (la que el "
            "afiliado declare, no menor a la RMV vigente). Aporta el 13%.\n\n"
            "SPP — el afiliado independiente aporta el 10% obligatorio + comisión AFP + "
            "prima del SISGS sobre su ingreso mensual declarado.\n\n"
            "ESSALUD POTESTATIVO: los independientes pueden afiliarse a EsSalud como "
            "potestativos pagando una prima mensual fija que cubre prestaciones de salud "
            "personales (Plan Independiente).\n\n"
            "Beneficios fiscales: las contribuciones previsionales son deducibles del impuesto "
            "a la renta de cuarta categoría hasta el límite legal."
        ),
    },
    {
        "article": "DL-22482",
        "section_path": "DL 22482 > Régimen de la Caja Militar y Policial",
        "content": (
            "DL 22482 (1979) — Régimen de Pensiones del Personal Militar y Policial.\n"
            "Régimen previsional especial cerrado para personal de las FF.AA. y PNP.\n"
            "Administrado por la Caja de Pensiones Militar Policial (CPMP) y por el Fondo "
            "de Aseguramiento en Salud de la PNP/FAP/Ejército/Marina.\n"
            "JUBILACIÓN POR TIEMPO DE SERVICIOS: 25 años de servicios efectivos (15 para "
            "personal femenino y por discapacidad) — monto equivalente al 100% del haber "
            "pensionable.\n\n"
            "INCOMPATIBILIDAD: percibir pensión militar/policial y simultáneamente otra "
            "pensión del Estado por servicios civiles (excepción: incremento por "
            "condecoraciones). Los pasivos pueden ejercer empleo en el sector privado sin "
            "afectar su pensión."
        ),
    },
]
