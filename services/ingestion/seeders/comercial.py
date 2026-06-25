"""
Seed: Derecho Comercial / Mercantil (Perú).

Núcleo normativo:
    - Ley 27287 — Ley de Títulos Valores
    - Ley 27809 — Ley General del Sistema Concursal
    - DL 1071 — Ley de Arbitraje
    - Ley 29623 / DS 047-2011-EF — Factura Negociable
    - Código de Comercio (vigente como supletorio)
"""

COMERCIAL_ARTICLES = [
    {
        "article": "Ley-27287-A1",
        "section_path": "Ley 27287 > Disposiciones generales",
        "content": (
            "Artículos 1-8 Ley 27287 — Ley de Títulos Valores (2000).\n"
            "TÍTULO VALOR: documento que representa o incorpora derechos patrimoniales, "
            "destinado a la circulación. Posee los caracteres de FORMALIDAD, LITERALIDAD, "
            "INCORPORACIÓN, AUTONOMÍA y ABSTRACCIÓN (cuando corresponda).\n\n"
            "REQUISITOS ESENCIALES:\n"
            "1. Conformidad con la ley.\n"
            "2. Indicación del derecho que confiere.\n"
            "3. Identificación del emisor (firma manuscrita o electrónica).\n"
            "4. Demás requisitos específicos por tipo de título.\n\n"
            "CLASIFICACIÓN:\n"
            "- Al portador (transferible por la sola entrega).\n"
            "- A la orden (transferible por endoso).\n"
            "- Nominativos (transferencia con anotación en registro)."
        ),
    },
    {
        "article": "Letra-de-Cambio",
        "section_path": "Ley 27287 > Letra de cambio",
        "content": (
            "Artículos 119-198 Ley 27287 — Letra de cambio.\n"
            "Es el título valor a la orden, mediante el cual el GIRADOR ordena al GIRADO "
            "pagar una suma determinada de dinero al BENEFICIARIO en una fecha y lugar "
            "indicados.\n\n"
            "REQUISITOS FORMALES (Art. 119):\n"
            "1. Denominación 'Letra de cambio' inserta en el texto.\n"
            "2. Indicación del lugar y fecha de giro.\n"
            "3. Orden incondicional de pagar una cantidad determinada de dinero.\n"
            "4. Nombre y documento de identidad del girado.\n"
            "5. Nombre del beneficiario.\n"
            "6. Indicación del vencimiento (a la vista, a cierto plazo desde la vista, "
            "a cierto plazo desde su giro, a fecha fija).\n"
            "7. Indicación del lugar de pago.\n"
            "8. Nombre, documento de identidad y firma del girador.\n\n"
            "ACEPTACIÓN: el girado se obliga al pago mediante su firma en la letra (Art. 127).\n\n"
            "PROTESTO POR FALTA DE PAGO: dentro de los 15 días posteriores al vencimiento "
            "ante notario o juez de paz (Art. 71).\n\n"
            "ACCIÓN CAMBIARIA: prescribe a los 3 años desde el vencimiento (Art. 96)."
        ),
    },
    {
        "article": "Cheque",
        "section_path": "Ley 27287 > Cheque",
        "content": (
            "Artículos 172-215 Ley 27287 — Cheque.\n"
            "Orden incondicional de pago dirigida por el GIRADOR (titular de cuenta corriente) "
            "al BANCO GIRADO para que pague a la vista al BENEFICIARIO una suma determinada "
            "con cargo a fondos disponibles del girador.\n\n"
            "REQUISITOS (Art. 174):\n"
            "1. Número o código del cheque.\n"
            "2. Lugar y fecha de emisión.\n"
            "3. Orden 'páguese a la orden de [beneficiario]'.\n"
            "4. Cantidad en cifras y en letras.\n"
            "5. Nombre del banco girado.\n"
            "6. Firma del girador.\n\n"
            "PLAZO DE PRESENTACIÓN: 30 días desde la fecha de emisión (Art. 207). Después de "
            "ese plazo el banco puede negarse al pago aún con fondos disponibles, pero el "
            "cheque conserva su carácter ejecutivo.\n\n"
            "CHEQUE SIN FONDOS: si la falta de pago se debe a falta de provisión, configura "
            "delito de libramiento indebido (Art. 215 CP) y se aplican sanciones del Art. 215 "
            "de la Ley 27287 (cierre de cuenta corriente).\n\n"
            "ACCIÓN CAMBIARIA: prescribe al año contado desde el vencimiento del plazo de "
            "presentación."
        ),
    },
    {
        "article": "Pagare",
        "section_path": "Ley 27287 > Pagaré",
        "content": (
            "Artículos 158-171 Ley 27287 — Pagaré.\n"
            "Promesa PURA y SIMPLE del EMITENTE de pagar una cantidad determinada de dinero "
            "al beneficiario o a su orden en una fecha y lugar determinados.\n\n"
            "REQUISITOS (Art. 158):\n"
            "1. Denominación 'Pagaré' inserta en el texto.\n"
            "2. Indicación del lugar y fecha de emisión.\n"
            "3. Promesa incondicional de pagar una cantidad determinada de dinero (cifras + letras).\n"
            "4. Nombre del beneficiario.\n"
            "5. Indicación del vencimiento (a la vista, a cierto plazo, a fecha fija).\n"
            "6. Indicación del lugar de pago.\n"
            "7. Nombre, documento de identidad y firma del emitente.\n\n"
            "DIFERENCIA CON LETRA: en el pagaré, el emitente promete pagar; en la letra, "
            "el girador ordena al girado pagar. El pagaré no requiere aceptación.\n\n"
            "USO TÍPICO: instrumento de crédito en operaciones bancarias y financieras (consumo, "
            "hipotecario, comercial). Goza de mérito ejecutivo (Art. 18 Ley 27287 + CPC).\n\n"
            "ACCIÓN CAMBIARIA: 3 años desde el vencimiento."
        ),
    },
    {
        "article": "Factura-Negociable",
        "section_path": "Ley 29623 > Factura Negociable",
        "content": (
            "Ley 29623 (2010) modificada por Ley 30308 / DS 047-2011-EF — Factura Negociable.\n"
            "Es el tercer ejemplar de la factura comercial o del recibo por honorarios que se "
            "puede transferir como TÍTULO VALOR A LA ORDEN, conteniendo la información del "
            "crédito comercial generado por la venta del bien o prestación del servicio.\n\n"
            "OBLIGATORIEDAD (Ley 30308): toda factura comercial debe contener el tercer "
            "ejemplar destinado a la factura negociable. La emisión electrónica de factura "
            "negociable se realiza mediante CAVALI (Institución de Compensación y Liquidación "
            "de Valores).\n\n"
            "TRANSFERENCIA: por endoso (físico) o por anotación en cuenta (electrónica). Una "
            "vez transferida, el adquirente (factor) tiene acción de cobranza directa contra "
            "el deudor.\n\n"
            "ACCEPTANCIÓN PRESUNTA: si el deudor no formula observación en 8 días hábiles "
            "desde la recepción, se considera aceptada la factura.\n\n"
            "FACTORING: el endoso de factura negociable al factor (banco o empresa de factoring) "
            "permite obtener liquidez inmediata sobre cuentas por cobrar (descuento financiero)."
        ),
    },
    {
        "article": "Warrant",
        "section_path": "Ley 27287 > Warrant y CDA",
        "content": (
            "Artículos 224-239 Ley 27287 — Certificado de Depósito (CDA) y Warrant.\n"
            "Son títulos valores emitidos por los Almacenes Generales de Depósito (AGD) "
            "como representativos de mercaderías depositadas.\n\n"
            "CERTIFICADO DE DEPÓSITO (CDA): acredita el derecho de propiedad del depositante "
            "sobre las mercaderías. Transferible por endoso.\n\n"
            "WARRANT: confiere derecho de prenda sobre las mercaderías por la cuantía y "
            "naturaleza del crédito. El primer endoso del warrant equivale a la constitución de "
            "prenda (sin desplazamiento ni inscripción).\n\n"
            "EJECUCIÓN: en caso de incumplimiento, el AGD procede a la venta directa en remate "
            "público a solicitud del acreedor prendario. El producto se aplica al pago del "
            "crédito; el remanente corresponde al titular del CDA."
        ),
    },
    {
        "article": "Ley-27809-Concursal",
        "section_path": "Ley 27809 > Sistema concursal",
        "content": (
            "Ley 27809 (2002) — Ley General del Sistema Concursal.\n"
            "Regula los procedimientos para enfrentar la crisis patrimonial de las personas "
            "naturales con negocio y jurídicas en general, bajo competencia de la Comisión de "
            "Procedimientos Concursales (CCO) de INDECOPI.\n\n"
            "TIPOS DE PROCEDIMIENTO:\n"
            "1. PROCEDIMIENTO CONCURSAL ORDINARIO (Art. 24): iniciado por el deudor o por uno "
            "o más acreedores cuyas obligaciones excedan las 50 UIT. La Junta de Acreedores "
            "decide entre reestructuración patrimonial o disolución y liquidación.\n\n"
            "2. PROCEDIMIENTO CONCURSAL PREVENTIVO (Art. 103): iniciado por el deudor que aún "
            "no se encuentra en cesación de pagos. Permite negociar un acuerdo global de "
            "refinanciación con sus acreedores antes de la insolvencia.\n\n"
            "EFECTOS DEL CONCURSO:\n"
            "- Suspensión de la exigibilidad de las obligaciones pre-concursales.\n"
            "- Suspensión de procesos individuales de cobranza.\n"
            "- Designación de Administración / Liquidación bajo control de Junta de Acreedores.\n"
            "- Orden de prelación de créditos (laborales, garantizados, comunes)."
        ),
    },
    {
        "article": "DL-1071-Arbitraje",
        "section_path": "DL 1071 > Arbitraje comercial",
        "content": (
            "DL 1071 (2008) — Decreto Legislativo que norma el Arbitraje.\n"
            "Regula el arbitraje nacional e internacional en el Perú, sustentado en la Ley "
            "Modelo CNUDMI (UNCITRAL).\n\n"
            "PRINCIPIOS:\n"
            "- Autonomía del convenio arbitral (separabilidad).\n"
            "- Kompetenz-kompetenz: el tribunal arbitral decide sobre su propia competencia.\n"
            "- Inversión limitada del Poder Judicial: cooperación y control.\n"
            "- Confidencialidad (salvo arbitrajes con el Estado, públicos).\n\n"
            "CONVENIO ARBITRAL (Art. 13): debe constar por escrito (papel, electrónico, "
            "intercambio de comunicaciones). Su existencia impide el conocimiento de la "
            "controversia por el Poder Judicial — excepción de convenio arbitral.\n\n"
            "LAUDO ARBITRAL (Art. 56): pone fin al arbitraje, tiene autoridad de cosa "
            "juzgada. Solo es impugnable mediante RECURSO DE ANULACIÓN ante la Corte Superior "
            "competente, en plazo de 20 días desde notificado (Art. 64). Las causales de "
            "anulación son taxativas (Art. 63).\n\n"
            "EJECUCIÓN: el laudo se ejecuta por la propia Corte Superior conforme al CPC. "
            "Laudos internacionales se ejecutan conforme a la Convención de Nueva York 1958."
        ),
    },
    {
        "article": "Leasing",
        "section_path": "DL 299 > Arrendamiento financiero (leasing)",
        "content": (
            "DL 299 (1984) — Arrendamiento financiero (leasing).\n"
            "Contrato por el cual una empresa autorizada (banco, financiera o empresa de "
            "leasing) cede el uso de un bien mueble o inmueble al ARRENDATARIO (cliente) a "
            "cambio de una renta periódica, otorgándole la OPCIÓN DE COMPRA al término del "
            "contrato por un valor residual.\n\n"
            "TIPOS:\n"
            "- Leasing financiero: el arrendador adquiere el bien para arrendarlo y existe "
            "opción de compra.\n"
            "- Leaseback: el cliente vende un bien propio a la financiera y simultáneamente lo "
            "toma en leasing (financiamiento garantizado).\n\n"
            "TRATAMIENTO TRIBUTARIO (DS 559-84-EFC):\n"
            "- Las cuotas son deducibles del IR del arrendatario como gasto.\n"
            "- Beneficio de depreciación acelerada para la financiera (3 años inmuebles, 1-3 años bienes muebles según vida útil).\n\n"
            "INCUMPLIMIENTO: la financiera puede ejecutar las garantías y obtener la "
            "restitución del bien por la vía del proceso de ejecución de obligaciones."
        ),
    },
    {
        "article": "Garantia-Mobiliaria",
        "section_path": "DL 1400 > Garantía Mobiliaria",
        "content": (
            "DL 1400 (2018) — Régimen de Garantía Mobiliaria.\n"
            "Reemplaza a la Ley 28677 e instaura un Sistema Informativo de Garantías "
            "Mobiliarias (SIGM) gestionado por SUNARP.\n"
            "OBJETO: garantizar el cumplimiento de obligaciones afectando bienes muebles "
            "presentes o futuros (créditos, inventarios, vehículos, maquinaria, propiedad "
            "intelectual, acciones).\n\n"
            "CONSTITUCIÓN: contrato escrito entre el constituyente (deudor o tercero) y el "
            "acreedor garantizado. Inscripción en el SIGM otorga publicidad y prelación.\n\n"
            "EJECUCIÓN:\n"
            "- Ejecución NOTARIAL EXTRAJUDICIAL: el acreedor toma la posesión del bien y lo "
            "vende directamente o por subasta privada notarial (más rápida).\n"
            "- Ejecución JUDICIAL: a través del proceso de ejecución del CPC.\n\n"
            "PRIORIDAD: por orden de inscripción en el SIGM. Las garantías mobiliarias prevalecen "
            "sobre los embargos y otras medidas cautelares posteriores."
        ),
    },
    {
        "article": "Contratos-Modernos",
        "section_path": "Derecho mercantil > Contratos modernos",
        "content": (
            "Contratos mercantiles atípicos modernos.\n"
            "FACTORING: contrato por el cual el FACTOR adquiere los créditos comerciales "
            "del cliente, anticipándole su valor descontado y asumiendo (factoring sin "
            "recurso) o no asumiendo (factoring con recurso) el riesgo de insolvencia del "
            "deudor. Resolución SBS 1021-98 regula a las empresas de factoring.\n\n"
            "FRANQUICIA: el franquiciante cede al franquiciado el derecho a explotar un "
            "modelo de negocio bajo su marca, know-how y soporte continuo, a cambio de un "
            "fee inicial y royalties periódicos. Regulado supletoriamente por el CC y la "
            "Ley de PI (DL 1075).\n\n"
            "FIDEICOMISO: contrato por el que el FIDEICOMITENTE transfiere bienes a una "
            "empresa autorizada (FIDUCIARIO — banco, empresa de fideicomiso) para que los "
            "administre en beneficio de un FIDEICOMISARIO. Regulado por Ley 26702 y "
            "Resoluciones SBS. Modalidades: fideicomiso de garantía, de administración, en "
            "titulización, testamentario.\n\n"
            "JOINT VENTURE: contrato asociativo no societario donde dos o más partes aportan "
            "recursos para un proyecto común sin constituir una persona jurídica. Regulado "
            "supletoriamente por la LGS (Art. 423-436 — contratos asociativos)."
        ),
    },
    {
        "article": "Prescripcion-Mercantil",
        "section_path": "Ley 27287 + Código Comercio > Prescripción",
        "content": (
            "Prescripción de acciones mercantiles.\n"
            "ACCIONES CAMBIARIAS DERIVADAS DE TÍTULOS VALORES (Art. 96 Ley 27287):\n"
            "- Letra de cambio y pagaré: 3 años desde la fecha de vencimiento.\n"
            "- Cheque: 1 año desde el vencimiento del plazo de presentación.\n"
            "- Facturas negociables: 3 años desde el vencimiento.\n\n"
            "ACCIONES POR ENRIQUECIMIENTO SIN CAUSA contra el girado de letra y pagaré: "
            "1 año desde que prescribió la acción cambiaria.\n\n"
            "ACCIONES MERCANTILES GENERALES (Art. 2001 CC supletorio):\n"
            "- Acciones personales: 10 años (acción personal contractual).\n"
            "- Acciones ejecutivas sobre obligaciones documentadas: 10 años.\n\n"
            "INTERRUPCIÓN DE LA PRESCRIPCIÓN: protesto, intimación notarial, demanda judicial, "
            "reconocimiento del deudor, ejecución de garantías."
        ),
    },
]
