"""
Seed: Derecho Tributario — Expansion del conocimiento tributario peruano.

Normas cubiertas:
- Codigo Tributario TUO (DS 133-2013-EF):
  - Libro I: Obligacion tributaria (nacimiento, exigibilidad, deudor)
  - Libro II: Administracion tributaria (SUNAT, facultades de fiscalizacion)
  - Libro III: Procedimientos tributarios (reclamacion, apelacion, Tribunal Fiscal)
  - Libro IV: Infracciones y sanciones, gradualidad
- Impuesto a la Renta TUO (DS 179-2004-EF): categorias, tasas, deducciones
- IGV TUO (DS 055-99-EF): operaciones gravadas, credito fiscal, exportacion
- Regimenes especiales: RUS, RER, MYPE Tributario, Regimen General
"""

TRIBUTARIO_EXT_ARTICLES = [
    # === CODIGO TRIBUTARIO — LIBRO I: OBLIGACION TRIBUTARIA ===
    {
        "article": "CT-OBL-1",
        "section_path": "TUO CT DS 133-2013-EF > Libro I > Titulo I > Obligacion tributaria > Nacimiento",
        "content": (
            "Codigo Tributario (TUO aprobado por DS 133-2013-EF).\n\n"
            "Art. 1: La obligacion tributaria, que es de derecho publico, es el vinculo entre el "
            "acreedor y el deudor tributario, establecido por ley, que tiene por objeto el "
            "cumplimiento de la prestacion tributaria, siendo exigible coactivamente.\n\n"
            "Art. 2: NACIMIENTO DE LA OBLIGACION TRIBUTARIA. La obligacion tributaria nace cuando "
            "se realiza el hecho previsto en la ley, como generador de dicha obligacion.\n\n"
            "Art. 3: EXIGIBILIDAD DE LA OBLIGACION TRIBUTARIA. La obligacion tributaria es exigible:\n"
            "a) Cuando deba ser determinada por el deudor tributario, desde el dia siguiente al "
            "   vencimiento del plazo fijado por Ley o reglamento.\n"
            "b) Cuando deba ser determinada por la Administracion Tributaria, desde el dia siguiente "
            "   al vencimiento del plazo para el pago que figure en la resolucion que contenga la "
            "   determinacion de la deuda tributaria.\n\n"
            "Art. 6: DEUDOR TRIBUTARIO. Es la persona obligada al cumplimiento de la prestacion "
            "tributaria como contribuyente o responsable.\n"
            "- Contribuyente: aquel que realiza el hecho generador de la obligacion tributaria.\n"
            "- Responsable: aquel que sin realizar el hecho generador tiene obligacion de cumplir "
            "  con la prestacion tributaria (agentes de retencion, agentes de percepcion)."
        ),
    },
    {
        "article": "CT-DETERMINACION",
        "section_path": "TUO CT > Libro I > Titulo III > Determinacion y declaracion tributaria",
        "content": (
            "Determinacion de la Obligacion Tributaria (Arts. 59-81 CT).\n\n"
            "Art. 59: Por la determinacion de la obligacion tributaria, el deudor tributario "
            "verifica la realizacion del hecho generador de la obligacion tributaria, seniala la "
            "base imponible y la cuantia del tributo.\n\n"
            "DECLARACION TRIBUTARIA (Art. 88): Es la manifestacion de hechos comunicados a la "
            "Administracion Tributaria en la forma y lugar establecidos. La declaracion referida "
            "a la determinacion de la obligacion tributaria puede ser sustituida o rectificada "
            "mediante otra declaracion posterior.\n\n"
            "DECLARACION RECTIFICATORIA:\n"
            "- Si aumenta la deuda: surte efectos desde el dia siguiente de presentacion.\n"
            "- Si disminuye la deuda: surte efectos si SUNAT no la impugna en 45 dias habiles. "
            "  Si SUNAT fiscaliza y encuentra diferencias, emite Resolucion de Determinacion.\n\n"
            "DETERMINACION DE OFICIO (Art. 59): La Administracion Tributaria puede determinar "
            "la deuda de oficio cuando:\n"
            "- El deudor no presenta declaracion.\n"
            "- La declaracion presentada ofrece dudas respecto a su veracidad o exactitud.\n"
            "- Se puede recurrir a la determinacion sobre base cierta (documentos) o base presunta."
        ),
    },
    {
        "article": "CT-SUNAT-FACULT",
        "section_path": "TUO CT > Libro II > Titulo II > SUNAT > Facultades de la Administracion Tributaria",
        "content": (
            "Facultades de la Administracion Tributaria — SUNAT (Arts. 55-89 CT).\n\n"
            "Art. 55: Es funcion de la Administracion Tributaria recaudar los tributos. "
            "A tal efecto, puede contratar directamente los servicios de las entidades del "
            "sistema bancario y financiero para recibir el pago de deudas tributarias.\n\n"
            "FACULTAD DE FISCALIZACION (Art. 62):\n"
            "SUNAT tiene la facultad de fiscalizar el cumplimiento de las obligaciones "
            "tributarias. Esta facultad incluye:\n"
            "1. Exigir a los deudores la exhibicion y/o presentacion de libros y registros "
            "   contables, documentos, informes y analisis.\n"
            "2. Requerir informacion a terceros (proveedores, clientes, entidades financieras).\n"
            "3. Realizar inspecciones, tomas de inventario o practicar arqueos de caja.\n"
            "4. Inmovilizar libros y documentos (por 5 dias habiles, prorrogables).\n"
            "5. Incautar bienes (con medida cautelar del Poder Judicial).\n"
            "6. Practicar inspecciones en locales ocupados.\n\n"
            "PLAZO MAXIMO DE FISCALIZACION (Art. 62-A): 1 ano desde la entrega de la "
            "documentacion requerida. Se puede ampliar a 2 anos cuando existan indicios de "
            "evasion y a 3 anos para precios de transferencia."
        ),
    },
    {
        "article": "CT-RECLAMACION",
        "section_path": "TUO CT > Libro III > Titulo III > Procedimiento contencioso-tributario > Reclamacion",
        "content": (
            "Procedimiento Contencioso Tributario — Reclamacion (Arts. 132-143 CT).\n\n"
            "Art. 132: Los deudores tributarios directamente afectados por actos de la "
            "Administracion Tributaria podran interponer reclamacion.\n\n"
            "ACTOS RECLAMABLES (Art. 135):\n"
            "- Resoluciones de Determinacion (RD): por diferencias de impuestos detectadas en fiscalizacion.\n"
            "- Ordenes de Pago (OP): por tributos autoliquidados y no pagados.\n"
            "- Resoluciones de Multa (RM): por infracciones tributarias.\n"
            "- Resoluciones sobre acogimiento indebido a regimenes especiales.\n\n"
            "PLAZO PARA RECLAMAR:\n"
            "- Resoluciones de Determinacion y Multa: 20 dias habiles desde notificacion.\n"
            "- Si se interpone fuera de plazo: debe pagarse la deuda o presentar carta fianza.\n\n"
            "PLAZO PARA RESOLVER:\n"
            "SUNAT tiene 9 meses para resolver la reclamacion (12 meses para precios de "
            "transferencia). Si no resuelve en ese plazo, el contribuyente puede considerar "
            "denegada su reclamacion (silencio negativo) e interponer apelacion ante el "
            "Tribunal Fiscal."
        ),
    },
    {
        "article": "CT-APELACION-TF",
        "section_path": "TUO CT > Libro III > Titulo III > Apelacion > Tribunal Fiscal",
        "content": (
            "Apelacion ante el Tribunal Fiscal (Arts. 143-156 CT).\n\n"
            "Art. 143: El Tribunal Fiscal es el organo resolutivo del Ministerio de Economia "
            "y Finanzas que depende administrativamente del Ministro, con independencia en "
            "sus resoluciones. Constituye la ultima instancia administrativa en materia tributaria.\n\n"
            "RECURSO DE APELACION ante el Tribunal Fiscal:\n"
            "Plazo: 15 dias habiles de notificada la Resolucion de Reclamacion (30 dias para "
            "precios de transferencia, o cuando la apelacion supere las 5 UIT). Si se interpone "
            "fuera de plazo, se puede regularizar pagando la deuda o presentando carta fianza.\n\n"
            "La apelacion se interpone ante SUNAT, que la eleva al Tribunal Fiscal en 30 dias habiles.\n\n"
            "PLAZO DE RESOLUCION del Tribunal Fiscal: 12 meses desde la fecha en que el expediente "
            "ha sido ingresado a la Sala competente (18 meses para precios de transferencia).\n\n"
            "APELACION DE PURO DERECHO (Art. 151): Cuando la apelacion se sustenta en "
            "cuestiones de puro derecho, puede interponerse directamente al Tribunal sin "
            "haber reclamado previamente.\n\n"
            "DEMANDA CONTENCIOSO-ADMINISTRATIVA: Agotada la via administrativa, se puede "
            "acudir al Poder Judicial mediante demanda ante la Sala Contencioso-Administrativa "
            "de la Corte Superior (Ley 27584, TUO DS 011-2019-JUS)."
        ),
    },
    {
        "article": "CT-INFRACCIONES",
        "section_path": "TUO CT > Libro IV > Titulo I > Infracciones y sanciones tributarias",
        "content": (
            "Infracciones y Sanciones Tributarias (Arts. 164-188 CT).\n\n"
            "Art. 164: Es infraccion tributaria, toda accion u omision que importe la violacion "
            "de normas tributarias, siempre que se encuentre tipificada como tal en el Codigo "
            "o en otras leyes o decretos legislativos.\n\n"
            "La infraccion tributaria es de responsabilidad objetiva (no requiere dolo o culpa).\n\n"
            "INFRACCIONES MAS FRECUENTES (Art. 176-178):\n"
            "- No presentar la declaracion jurada en los plazos establecidos (Art. 176.1): "
            "  Multa: 1 UIT (disminuible por gradualidad hasta 40%).\n"
            "- Presentar declaracion que contenga datos falsos (Art. 178.1): "
            "  Multa: 50% del tributo omitido.\n"
            "- No pagar dentro de los plazos establecidos (Art. 178.4): "
            "  Multa: 50% del tributo no pagado.\n"
            "- No emitir y/u otorgar comprobantes de pago (Art. 174.1): "
            "  Multa: 1 UIT o cierre temporal del establecimiento.\n\n"
            "REGIMEN DE GRADUALIDAD: Las multas pueden reducirse en un porcentaje segun la "
            "oportunidad de subsanacion:\n"
            "- Si subsana antes de la notificacion: reduccion del 95%.\n"
            "- Si subsana dentro del plazo otorgado por SUNAT: reduccion del 70%.\n"
            "- Si subsana antes de la interposicion del recurso impugnatorio: reduccion del 60%."
        ),
    },
    # === IMPUESTO A LA RENTA ===
    {
        "article": "IR-CATEGORIAS",
        "section_path": "LIR DS 179-2004-EF > Categorias de Renta > 1ra y 2da",
        "content": (
            "Impuesto a la Renta — Primera y Segunda Categoria (LIR DS 179-2004-EF).\n\n"
            "PRIMERA CATEGORIA — RENTAS DE PREDIOS:\n"
            "Rentas por arrendamiento, subarrendamiento y cesion de bienes inmuebles.\n"
            "- Base imponible: Valor del arriendo pactado (renta real) o el 6% del valor del "
            "  predio segun el autoavaluo municipal (renta ficta), el que sea mayor.\n"
            "- Tasa: 5% del importe mensual del alquiler (pago a cuenta).\n"
            "- Declaracion: mensual mediante PDT 616 y anual en la Declaracion Jurada Anual.\n\n"
            "SEGUNDA CATEGORIA — RENTAS DEL CAPITAL:\n"
            "Intereses, dividendos, regalias, ganancias de capital por venta de inmuebles y acciones.\n"
            "- Intereses: 5% de tasa efectiva (sobre el monto bruto).\n"
            "- Dividendos: 5% (distribuidos por personas juridicas domiciliadas).\n"
            "- Ganancias de capital por venta de inmuebles (precio de venta - costo computable): "
            "  5% sobre la ganancia neta.\n"
            "- Ganancias por venta de acciones no exoneradas: 5% para personas naturales "
            "  domiciliadas."
        ),
    },
    {
        "article": "IR-3RA-CATEGORIA",
        "section_path": "LIR DS 179-2004-EF > Tercera Categoria > Renta empresarial",
        "content": (
            "Impuesto a la Renta de Tercera Categoria — Renta Empresarial (Arts. 28-57 LIR).\n\n"
            "Constituyen rentas de tercera categoria:\n"
            "- Las derivadas del comercio, la industria o mineria.\n"
            "- Las derivadas de la actividad agropecuaria.\n"
            "- Las derivadas de actividades de servicios comerciales, industriales o de cualquier "
            "  tipo que se realicen en asociacion o en sociedad.\n\n"
            "BASE IMPONIBLE: Renta Neta = Ingresos - Costos - Gastos deducibles.\n\n"
            "PRINCIPIO DE CAUSALIDAD (Art. 37 LIR): Solo son deducibles los gastos necesarios "
            "para producir la renta o mantener su fuente generadora. Los gastos deben ser "
            "fehacientes, necesarios, razonables y proporcionales.\n\n"
            "GASTOS NO DEDUCIBLES (Art. 44 LIR): multas e intereses moratorios pagados al "
            "Estado, gastos personales, depreciaciones superiores a las tasas permitidas, "
            "provisiones no admitidas, entre otros.\n\n"
            "TASA (Art. 55): 29.5% sobre la renta neta imponible para contribuyentes del "
            "Regimen General y del Regimen MYPE Tributario (escalonada: 10% hasta 15 UIT "
            "y 29.5% sobre el exceso).\n\n"
            "PAGOS A CUENTA MENSUALES (Art. 85): 1.5% de los ingresos netos mensuales "
            "(metodo A) o coeficiente determinado de ejercicio anterior (metodo B)."
        ),
    },
    {
        "article": "IR-4TA-5TA",
        "section_path": "LIR DS 179-2004-EF > Cuarta y Quinta Categoria > Trabajo",
        "content": (
            "Impuesto a la Renta de Cuarta y Quinta Categoria (Arts. 33-34 LIR).\n\n"
            "CUARTA CATEGORIA — TRABAJO INDEPENDIENTE:\n"
            "Rentas de profesionales liberales, artistas, directores, notarios, mandatarios, "
            "gestores de negocios y arbitros.\n"
            "- Renta bruta - Deduccion del 20% (maximo 24 UIT) = Renta neta de 4ta categoria.\n"
            "- Adicionalmente, deduccion de 7 UIT en conjunto con rentas de 5ta categoria.\n"
            "- Tasa: Escala progresiva acumulativa (igual que persona natural).\n"
            "- El pagador retiene el 8% del monto bruto de honorarios (si supera S/ 1,500 mensual).\n"
            "- Si retenciones + pagos directos superan el IR anual, procede devolucion.\n\n"
            "QUINTA CATEGORIA — TRABAJO EN RELACION DE DEPENDENCIA:\n"
            "Sueldos, salarios, bonificaciones, gratificaciones y todo concepto remunerativo "
            "pagado por el empleador.\n"
            "- El empleador retiene mensualmente el IR segun la escala progresiva.\n"
            "- Calculo: Renta anual proyectada - 7 UIT = Renta neta imponible, aplicando escala.\n"
            "- No se puede compensar perdidas de ejercicios anteriores.\n"
            "- El empleador debe presentar PDT 601 y proporcionar la Certificacion de Retenciones "
            "al trabajador (Art. 45 LIR)."
        ),
    },
    # === IGV ===
    {
        "article": "IGV-CREDITO",
        "section_path": "TUO IGV DS 055-99-EF > Credito Fiscal > Requisitos y uso",
        "content": (
            "Credito Fiscal del IGV (Arts. 18-24 TUO Ley IGV DS 055-99-EF).\n\n"
            "Art. 18: El credito fiscal esta constituido por el IGV consignado separadamente en "
            "el comprobante de pago, correspondiente a las adquisiciones de bienes y servicios "
            "aceptadas como gasto o costo por la LIR y que se destinen a operaciones gravadas.\n\n"
            "REQUISITOS SUSTANCIALES (Art. 18):\n"
            "1. Que el IGV sea permitido como costo o gasto.\n"
            "2. Que se destine a operaciones por las que se deba pagar el IGV.\n\n"
            "REQUISITOS FORMALES (Art. 19):\n"
            "1. El IGV debe estar discriminado en el comprobante de pago.\n"
            "2. El comprobante debe cumplir con los requisitos del Reglamento de Comprobantes de Pago.\n"
            "3. El comprobante debe estar anotado en el Registro de Compras.\n\n"
            "PROPORCION DEL CREDITO (Art. 23): Cuando el contribuyente realiza operaciones "
            "gravadas y no gravadas, el credito se determina en proporcion a las operaciones "
            "gravadas sobre el total (prorrata del credito fiscal).\n\n"
            "SALDO A FAVOR DEL EXPORTADOR: El IGV pagado en adquisiciones para exportacion "
            "genera un credito (saldo a favor del exportador) que puede aplicarse contra "
            "otros tributos, compensarse o solicitarse en devolucion (IVAP, Drawback de IGV)."
        ),
    },
    {
        "article": "IGV-EXONERACIONES",
        "section_path": "TUO IGV > Apendices I y II > Exoneraciones e inafectaciones",
        "content": (
            "Operaciones exoneradas, inafectas y exportacion de servicios — IGV.\n\n"
            "EXONERACIONES (Apendice I — bienes y Apendice II — servicios):\n"
            "Las exoneraciones son tratamientos que liberan al sujeto del pago del IGV pero "
            "no del gravamen en si. El Congreso las aprueba por plazo determinado. Principales:\n"
            "- Venta de bienes del Apendice I: alimentos de primera necesidad (papas, maiz, "
            "  arroz, pollo vivo, entre otros), libros y revistas, insumos agricolas.\n"
            "- Servicios del Apendice II: servicios medicos y odontologicos, ensenanza, "
            "  transporte publico, seguros de vida.\n\n"
            "INAFECTACIONES: Operaciones que no estan dentro del ambito de aplicacion del IGV.\n"
            "- Transferencias de bienes realizadas a titulo gratuito.\n"
            "- Servicios prestados a titulo gratuito.\n"
            "- Importacion de bienes donados a entidades religiosas.\n\n"
            "EXPORTACION DE SERVICIOS (Art. 33 y Apendice V TUO IGV):\n"
            "Los servicios del Apendice V son considerados exportacion cuando se cumplen "
            "todos los requisitos (prestador domiciliado en Peru, usuario no domiciliado, "
            "uso fuera del pais, pago recibido en moneda extranjera o equivalente). "
            "Estos servicios generan saldo a favor del exportador."
        ),
    },
    # === REGIMENES ESPECIALES ===
    {
        "article": "RUS-REGIMEN",
        "section_path": "DL 937 > Nuevo RUS > Regimen Unico Simplificado",
        "content": (
            "Nuevo Regimen Unico Simplificado (NRUS) — DL 937 y modificatorias.\n\n"
            "El NRUS es el regimen mas simple para pequenos negocios y personas naturales.\n\n"
            "SUJETOS COMPRENDIDOS:\n"
            "- Personas naturales y sucesiones indivisas domiciliadas.\n"
            "- Solo pueden realizar actividades de venta de bienes o prestacion de servicios "
            "  al consumidor final.\n\n"
            "VEDADOS DEL NRUS: Personas juridicas (sociedades), profesionales independientes, "
            "actividades de importacion, empresas con mas de 1 establecimiento o activos fijos "
            "superiores a S/ 70,000.\n\n"
            "CATEGORIAS Y CUOTAS MENSUALES (para 2024):\n"
            "- Categoria 1: Ingresos o compras hasta S/ 5,000/mes — Cuota: S/ 20.\n"
            "- Categoria 2: Ingresos o compras hasta S/ 8,000/mes — Cuota: S/ 50.\n"
            "Hay una categoria especial (S/ 0) para productores agricolas y piscicultores "
            "con ingresos hasta S/ 60,000 al ano.\n\n"
            "La cuota mensual sustituye el pago del IR y el IGV. No pueden emitir facturas, "
            "solo boletas de venta y tickets de maquina registradora."
        ),
    },
    {
        "article": "RER-REGIMEN",
        "section_path": "LIR > Capitulo XV > Regimen Especial del Impuesto a la Renta",
        "content": (
            "Regimen Especial del Impuesto a la Renta (RER) — Art. 117-124 LIR y DS 179-2004-EF.\n\n"
            "SUJETOS COMPRENDIDOS:\n"
            "Personas naturales, sociedades conyugales, sucesiones indivisas y personas juridicas "
            "domiciliadas que obtengan rentas de tercera categoria y cuyos ingresos anuales no "
            "superen S/ 525,000.\n\n"
            "VEDADOS: Contribuyentes con ingresos mayores a S/ 525,000, que realicen actividades "
            "como contratos de construccion, transporte de carga o pasajeros, casinos, tragamonedas, "
            "agencias de viaje, propaganda, espectaculos, notarias, entre otras.\n\n"
            "OBLIGACIONES EN EL RER:\n"
            "- IR: 1.5% de los ingresos netos mensuales (pago definitivo, no hay declaracion anual).\n"
            "- IGV: 18% (si los ingresos superan S/ 30,000 en el ano, deben inscribirse al IGV).\n"
            "- Libros contables: solo Registro de Ventas e Ingresos y Registro de Compras.\n"
            "- Pueden emitir facturas y boletas de venta.\n\n"
            "EXCLUSION DEL RER: Si en el curso del ejercicio superan el limite de ingresos o "
            "realizan actividades vedadas, deben incorporarse al Regimen General o al Regimen "
            "MYPE Tributario a partir del periodo en que superen el limite."
        ),
    },
    {
        "article": "MYPE-TRIBUTARIO",
        "section_path": "DL 1269 > Regimen MYPE Tributario > Tasas y obligaciones",
        "content": (
            "Regimen MYPE Tributario (RMT) — Decreto Legislativo 1269.\n\n"
            "Creado en 2017 como regimen intermedio entre el RER y el Regimen General, "
            "especificamente para MYPE.\n\n"
            "SUJETOS COMPRENDIDOS: Personas naturales y juridicas domiciliadas con ingresos "
            "anuales que no superen 1700 UIT (aprox. S/ 8,755,000 en 2024).\n\n"
            "VEDADOS: Contribuyentes vinculados con otras empresas que en conjunto superen "
            "1700 UIT, quienes tengan sucursales o agencias en el exterior.\n\n"
            "TASAS DEL IR EN EL RMT:\n"
            "- Hasta 15 UIT de renta neta: 10%.\n"
            "- Exceso de 15 UIT: 29.5%.\n\n"
            "PAGOS A CUENTA (Art. 6 DL 1269):\n"
            "- 1% de los ingresos netos mensuales hasta el mes en que se supere las 300 UIT "
            "  de ingresos acumulados en el ejercicio.\n"
            "- Luego del limite, se aplica el coeficiente o 1.5%, el que sea mayor.\n\n"
            "LIBROS CONTABLES (Art. 11 DL 1269):\n"
            "- Hasta 300 UIT de ingresos: Registro de Ventas, Registro de Compras, Libro Diario "
            "  de Formato Simplificado.\n"
            "- De 300 a 500 UIT: Registro de Ventas, Registro de Compras, Libro Diario y Libro Mayor.\n"
            "- De 500 a 1700 UIT: contabilidad completa."
        ),
    },
    {
        "article": "PRECIOS-TRANSFERENCIA",
        "section_path": "LIR > Titulo VI > Precios de transferencia > Principio arm's length",
        "content": (
            "Precios de Transferencia (Arts. 32-A LIR y Reglamento DS 122-94-EF modificado).\n\n"
            "DEFINICION: Las transacciones entre partes vinculadas (empresas del mismo grupo) "
            "deben pactarse a valores de mercado (principio arm's length), como si fueran "
            "entre partes independientes.\n\n"
            "PARTES VINCULADAS (Art. 24 Reglamento LIR): Se consideran vinculadas cuando "
            "una empresa controla a otra (participacion directa o indirecta superior al 30%), "
            "cuando ambas son controladas por una misma empresa, cuando hay directores comunes, "
            "o cuando existe una relacion de dependencia economica o financiera.\n\n"
            "METODOS DE PRECIOS DE TRANSFERENCIA (Art. 32-A LIR, alineados con OCDE):\n"
            "1. Precio Comparable No Controlado (CUP)\n"
            "2. Precio de Reventa\n"
            "3. Costo Adicionado\n"
            "4. Profit Split (Particion de Utilidades)\n"
            "5. Margen Neto Transaccional\n\n"
            "DECLARACION INFORMATIVA DE PRECIOS DE TRANSFERENCIA: Obligatoria para "
            "contribuyentes con ingresos mayores a 2300 UIT o transacciones con vinculadas "
            "que superen 400 UIT. Se presenta en SUNAT mediante PDT 3560.\n\n"
            "Country-by-Country Report (CbCR): Para grupos multinacionales con ingresos "
            "consolidados mayores a 2,700 millones de soles."
        ),
    },
    {
        "article": "SUNAT-COMPROBANTES",
        "section_path": "Reglamento Comprobantes de Pago RS 007-99-SUNAT > Tipos y emisores",
        "content": (
            "Comprobantes de Pago — Reglamento aprobado por RS 007-99-SUNAT y modificatorias. "
            "Sistema de Emision Electronica (SEE) — RS 300-2014/SUNAT.\n\n"
            "TIPOS DE COMPROBANTES:\n"
            "- FACTURA: Para operaciones entre empresas o con personas naturales con negocio. "
            "  Genera derecho a credito fiscal del IGV y deduccion del IR.\n"
            "- BOLETA DE VENTA: Para consumidor final (personas naturales sin negocio). "
            "  No genera credito fiscal ni deduccion de IR (salvo algunos regimenes).\n"
            "- NOTA DE CREDITO: Para anular, reducir o devolver operaciones ya facturadas.\n"
            "- NOTA DE DEBITO: Para aumentar el valor de operaciones ya facturadas.\n"
            "- TICKET / BOLETA MAQUINA REGISTRADORA: Para ventas al publico en general.\n"
            "- LIQUIDACION DE COMPRA: Para adquisiciones a productores agricolas informales.\n\n"
            "FACTURACION ELECTRONICA (SEE):\n"
            "Desde 2023, la emision electronica es obligatoria para practicamente todos los "
            "contribuyentes. Los comprobantes son validados por SUNAT (OSE o SFS). "
            "El XML firmado digitalmente es el documento valido; el PDF (representacion impresa) "
            "es solo una representacion visual."
        ),
    },
    {
        "article": "CT-PRESCRIPCION",
        "section_path": "TUO CT > Libro I > Titulo III > Prescripcion tributaria",
        "content": (
            "Prescripcion de la Obligacion Tributaria (Arts. 43-49 TUO CT DS 133-2013-EF).\n\n"
            "PLAZOS DE PRESCRIPCION (Art. 43):\n"
            "- 4 anos: Para contribuyentes que presentaron la declaracion respectiva.\n"
            "- 6 anos: Para quienes no presentaron la declaracion jurada en plazo.\n"
            "- 10 anos: Para agentes de retencion o percepcion que no han pagado el tributo "
            "  retenido o percibido.\n"
            "- 4 anos: Para solicitar devolucion de pagos en exceso o indebidos.\n\n"
            "COMPUTO DEL PLAZO:\n"
            "La prescripcion se computa desde el 1 de enero del ano siguiente a la "
            "fecha en que la obligacion fue exigible (ejemplo: el plazo para el IR del "
            "ejercicio 2023 empieza a correr el 1 de enero de 2024).\n\n"
            "SUSPENSION DE LA PRESCRIPCION (Art. 46): Se suspende durante:\n"
            "- El tramite de un procedimiento contencioso-tributario.\n"
            "- La notificacion de la Resolucion de Determinacion o multa.\n"
            "- El plazo de fraccionamiento tributario (Art. 36 CT).\n\n"
            "INTERRUPCION DE LA PRESCRIPCION (Art. 45): Se interrumpe con:\n"
            "- La notificacion de cualquier acto de SUNAT que reconozca o requiera la obligacion.\n"
            "- El pago parcial de la deuda.\n"
            "- La solicitud de fraccionamiento o aplazamiento.\n\n"
            "La prescripcion no opera de oficio; el contribuyente debe invocarla expresamente."
        ),
    },
    {
        "article": "IGV-NACIMIENTO",
        "section_path": "TUO IGV DS 055-99-EF > Nacimiento de la obligacion y base imponible",
        "content": (
            "Nacimiento de la Obligacion Tributaria del IGV (Arts. 3-12 TUO Ley IGV).\n\n"
            "NACIMIENTO DE LA OBLIGACION (Art. 4):\n"
            "- En la venta de bienes: en la fecha en que se emite el comprobante de pago o "
            "  en la fecha en que se entregue el bien, lo que ocurra primero.\n"
            "- En la prestacion de servicios: en la fecha en que se emite el comprobante de "
            "  pago o en la fecha en que se percibe la retribucion, lo que ocurra primero.\n"
            "- En los contratos de construccion: en la fecha de emision del comprobante o "
            "  en la fecha de percepcion del ingreso, lo que ocurra primero.\n"
            "- En la primera venta de inmuebles: en la fecha de percepcion del ingreso.\n"
            "- En la importacion: en la fecha en que se solicita el despacho aduanero.\n\n"
            "BASE IMPONIBLE (Art. 13):\n"
            "- Venta de bienes: valor de venta (precio convenido).\n"
            "- Prestacion de servicios: suma total pactada.\n"
            "- Contratos de construccion: valor de la construccion.\n"
            "- Primera venta de inmuebles: valor de transferencia, descontando el valor del terreno "
            "  (terreno no esta gravado con IGV).\n"
            "- Importacion: Valor en Aduana + Ad Valorem + ISC.\n\n"
            "TASA: 16% (IGV) + 2% (IPM) = 18% total sobre la base imponible."
        ),
    },
    {
        "article": "SUNAT-COBRANZA",
        "section_path": "TUO CT > Libro II > Titulo III > Cobranza coactiva tributaria",
        "content": (
            "Procedimiento de Cobranza Coactiva (Arts. 114-121 TUO CT).\n\n"
            "La cobranza coactiva es el procedimiento por el cual la Administracion Tributaria "
            "ejecuta la deuda exigible coactivamente sin necesidad de acudir al Poder Judicial.\n\n"
            "DEUDA EXIGIBLE COACTIVAMENTE (Art. 115):\n"
            "- La establecida en Resolucion de Determinacion o Resolucion de Multa notificada "
            "  y no reclamada en plazo.\n"
            "- La establecida por Resolucion de Determinacion o Multa reclamada y resuelta "
            "  sin recurso pendiente.\n"
            "- Orden de Pago notificada y no pagada.\n\n"
            "MEDIDAS CAUTELARES (Art. 118):\n"
            "El Ejecutor Coactivo puede trabar:\n"
            "1. Embargo en forma de intervencion en recaudacion (sobre ingresos).\n"
            "2. Embargo en forma de deposito (sobre bienes muebles).\n"
            "3. Embargo en forma de inscripcion (sobre inmuebles y vehiculos en SUNARP).\n"
            "4. Embargo en forma de retencion (sobre cuentas bancarias, CTS, etc.).\n\n"
            "SUSPENSION DE LA COBRANZA (Art. 119): Procede cuando:\n"
            "- Exista proceso de amparo admitido.\n"
            "- Exista recurso de reclamacion o apelacion que haya determinado la interposicion "
            "  de una medida cautelar en el proceso contencioso-administrativo.\n"
            "- El deudor obtiene autorizacion de aplazamiento o fraccionamiento."
        ),
    },
    {
        "article": "BENEFICIOS-TRIBUTARIOS",
        "section_path": "Derecho Tributario > Beneficios tributarios > Tipos y control",
        "content": (
            "Beneficios Tributarios en el Peru — Tipos y Control Constitucional.\n\n"
            "Los beneficios tributarios son tratamientos preferenciales establecidos en la ley "
            "para determinadas actividades, sectores o contribuyentes. En Peru existen:\n\n"
            "EXONERACIONES: El contribuyente esta dentro del ambito de aplicacion del tributo "
            "pero se le dispensa del pago por un plazo determinado. Requieren ley expresa.\n\n"
            "INAFECTACIONES: Las operaciones o personas estan fuera del ambito del tributo "
            "de forma permanente (no requieren renovacion).\n\n"
            "CREDITOS TRIBUTARIOS: Reducen directamente la cuota tributaria (ej. ITAN como "
            "pago a cuenta del IR).\n\n"
            "PRINCIPALES BENEFICIOS VIGENTES:\n"
            "- Regimen de Amazonia (Ley 27037): tasas reducidas de IGV e IR para actividades "
            "  en la selva alta y baja del Peru.\n"
            "- Sector Agrario (Ley 31110): IR al 15%, depreciacion acelerada.\n"
            "- Zona Franca de Tacna (ZOFRATACNA): exoneraciones para empresas instaladas.\n"
            "- Investigacion Cientifica (Ley 30309): deduccion adicional del 175% o 150%.\n\n"
            "CONTROL: El Ministerio de Economia y Finanzas (MEF) elabora un marco "
            "macrofiscal que evalua el impacto de los beneficios tributarios en la "
            "recaudacion (gasto tributario)."
        ),
    },
    {
        "article": "AUDITORIA-TRIBUTARIA",
        "section_path": "TUO CT > Libro II > Titulo II > Fiscalizacion > Auditoria y cierre",
        "content": (
            "Procedimiento de Fiscalizacion Tributaria (DS 085-2007-EF — Reglamento del "
            "Procedimiento de Fiscalizacion de SUNAT).\n\n"
            "TIPOS DE FISCALIZACION:\n"
            "1. FISCALIZACION DEFINITIVA: Revision integral de un periodo y tributo. "
            "   SUNAT solo puede realizarla una vez por periodo y tributo.\n"
            "2. FISCALIZACION PARCIAL: Revision de uno o varios elementos de la obligacion. "
            "   No impide una fiscalizacion definitiva posterior.\n"
            "3. FISCALIZACION PARCIAL ELECTRONICA: Mediante el cruce de informacion de "
            "   declaraciones, comprobantes electronicos y registros electronicos.\n\n"
            "INICIO Y DOCUMENTOS DEL PROCEDIMIENTO:\n"
            "- Carta de presentacion: notifica al contribuyente del inicio de la fiscalizacion.\n"
            "- Requerimiento: solicita documentos, libros, información.\n"
            "- Resultado del Requerimiento: comunica los hallazgos.\n\n"
            "CIERRE DE LA FISCALIZACION:\n"
            "Concluida la fiscalizacion, SUNAT puede:\n"
            "a) Emitir Resolucion de Determinacion (RD): por diferencias de tributos.\n"
            "b) Emitir Resolucion de Multa (RM): por infracciones detectadas.\n"
            "c) Archivar el expediente sin formular cargos.\n\n"
            "El contribuyente tiene 20 dias habiles para reclamar las RD y RM ante SUNAT."
        ),
    },
]
