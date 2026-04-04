"""
Seed: Comercio Exterior — Expansion de conocimiento aduanero y de comercio internacional peruano.

Normas cubiertas:
- Ley General de Aduanas (DL 1053) y su Reglamento (DS 010-2009-EF)
- Regimenes aduaneros principales
- TLC Peru-EEUU, Peru-China, Peru-UE (principios y certificados de origen)
- MINCETUR funciones y competencias
- SUNAT-Aduanas: procedimientos INTA, despacho anticipado, canales de control
- Infracciones y sanciones aduaneras
"""

COMERCIO_EXT_ARTICLES = [
    # === LEY GENERAL DE ADUANAS — DL 1053 ===
    {
        "article": "LGA-1",
        "section_path": "DL 1053 > Ley General de Aduanas > Titulo Preliminar > Definiciones",
        "content": (
            "Decreto Legislativo 1053 — Ley General de Aduanas (vigente desde junio 2008, "
            "modificada por DL 1433 y otras normas).\n\n"
            "Definiciones fundamentales (Art. 2 LGA):\n"
            "ADUANA: Lugar habilitado donde se realizan operaciones aduaneras y control del "
            "trafico internacional de mercancias.\n\n"
            "DESPACHO ADUANERO: Cumplimiento del conjunto de formalidades aduaneras para que "
            "las mercancias sean sometidas a un regimen aduanero.\n\n"
            "DECLARACION ADUANERA: Acto efectuado en la forma prescrita por la autoridad "
            "aduanera mediante el cual el declarante indica el regimen aduanero y los datos "
            "exigidos para su aplicacion.\n\n"
            "MERCANCIAS: Bienes corporales e incorporales objeto de operaciones aduaneras.\n\n"
            "OBLIGACION TRIBUTARIA ADUANERA: Vinculo entre el acreedor tributario (Estado) "
            "y el deudor tributario (importador/exportador) en razon del ingreso o salida de "
            "mercancias del territorio aduanero.\n\n"
            "TERRITORIO ADUANERO: Parte del territorio nacional que incluye el espacio acuatico "
            "y aereo donde se aplica la legislacion aduanera peruana."
        ),
    },
    {
        "article": "LGA-IMPORTACION",
        "section_path": "DL 1053 > Regimenes Aduaneros > Importacion para el consumo",
        "content": (
            "Importacion para el Consumo — Regimen definitivo (Arts. 49-57 LGA y DS 010-2009-EF).\n\n"
            "Definicion: Regimen aduanero que permite el ingreso de mercancias al territorio "
            "aduanero para su consumo, luego del pago o garantia de los derechos arancelarios "
            "y demas impuestos aplicables, asi como el pago de los recargos y multas.\n\n"
            "Tributos aplicables en importacion:\n"
            "1. Ad Valorem CIF: porcentaje sobre el valor CIF de la mercancia (0%, 4% o 6% "
            "segun el arancel vigente DS 342-2011-EF y modificatorias).\n"
            "2. IGV: 16% sobre base imponible (Valor en Aduana + Ad Valorem + ISC si aplica).\n"
            "3. IPM: 2% (Impuesto de Promocion Municipal).\n"
            "4. ISC: aplica segun la partida arancelaria (bebidas, cigarrillos, combustibles).\n"
            "5. Derechos antidumping o compensatorios: cuando corresponda.\n\n"
            "Modalidades de despacho:\n"
            "- DESPACHO ANTICIPADO: Numeracion de la DAM antes del arribo del buque. Plazo: "
            "  numeracion hasta 30 dias antes del arribo.\n"
            "- DESPACHO URGENTE: Para mercancias que requieren despacho inmediato por su "
            "  naturaleza (animales vivos, perecederos, medicamentos).\n"
            "- DESPACHO EXCEPCIONAL: Para mercancias que quedaron en situacion de abandono "
            "  legal (sin declarar en 30 dias del termino de descarga)."
        ),
    },
    {
        "article": "LGA-EXPORTACION",
        "section_path": "DL 1053 > Regimenes Aduaneros > Exportacion definitiva",
        "content": (
            "Exportacion Definitiva (Arts. 60-69 LGA y Procedimiento INTA-PE.02.01).\n\n"
            "Definicion: Regimen aduanero que permite la salida del territorio aduanero de "
            "las mercancias nacionales o nacionalizadas para su uso o consumo definitivo en el "
            "exterior. No esta afecto al pago de tributos.\n\n"
            "La exportacion definitiva no genera obligacion tributaria aduanera. La mercancia "
            "sale libre de aranceles e IGV.\n\n"
            "DRAWBACK: Regimen que permite la restitucion de los derechos arancelarios pagados "
            "en la importacion de insumos incorporados en productos exportados. Tasa actual: "
            "3% del valor FOB exportado (DS 282-2016-EF y modificatorias). Maximo US$ 20,000 "
            "por exportacion.\n\n"
            "Documentos para exportacion:\n"
            "1. Declaracion Aduanera de Mercancias (DAM)\n"
            "2. Factura comercial o documento equivalente\n"
            "3. Lista de empaque (packing list)\n"
            "4. Certificado de origen (si aplica TLC)\n"
            "5. Documentos especificos por tipo de mercancia (fitosanitarios, sanitarios, etc.)\n\n"
            "EXPORTACION DE SERVICIOS: Los servicios exportados estan exonerados del IGV segun "
            "el Art. 33 de la Ley del IGV (apendice V), siempre que se cumplan los requisitos "
            "de exportacion de servicios."
        ),
    },
    {
        "article": "LGA-ADMISION",
        "section_path": "DL 1053 > Regimenes Aduaneros > Admision temporal y deposito",
        "content": (
            "Regimenes Aduaneros Suspensivos (Arts. 67-98 LGA).\n\n"
            "ADMISION TEMPORAL PARA REEXPORTACION EN EL MISMO ESTADO:\n"
            "Permite el ingreso al territorio aduanero de mercancias extranjeras con suspension "
            "del pago de tributos, por un plazo determinado, con el fin de ser reexportadas "
            "sin modificacion (stands, equipos de exposicion, muestras).\n"
            "Plazo maximo: 18 meses (prorrogable hasta 18 meses adicionales).\n\n"
            "ADMISION TEMPORAL PARA PERFECCIONAMIENTO ACTIVO:\n"
            "Permite ingresar mercancias para ser transformadas, elaboradas o reparadas, "
            "con suspension de tributos, y luego exportar el producto resultante.\n"
            "Plazo maximo: 24 meses.\n\n"
            "DEPOSITO ADUANERO:\n"
            "Permite almacenar mercancias extranjeras en depositos autorizados bajo control "
            "aduanero, sin pago de tributos, por un plazo de 12 meses prorrogables.\n\n"
            "TRANSITO ADUANERO:\n"
            "Permite el traslado de mercancias extranjeras de una aduana a otra bajo control "
            "aduanero. Puede ser interno (entre aduanas del Peru) o internacional (pais de "
            "origen a pais destino atravesando Peru)."
        ),
    },
    {
        "article": "LGA-OPERADORES",
        "section_path": "DL 1053 > Operadores de Comercio Exterior",
        "content": (
            "Operadores de Comercio Exterior (Arts. 15-32 LGA).\n\n"
            "Son operadores de comercio exterior las personas naturales o juridicas que "
            "intervienen en el despacho aduanero. Principales:\n\n"
            "1. IMPORTADOR / EXPORTADOR: Principal obligado tributario y responsable de la "
            "declaracion. Puede actuar directamente o a traves de un agente de aduana.\n\n"
            "2. AGENTE DE ADUANA: Profesional auxiliar de la funcion publica aduanera. "
            "Actua como representante del importador/exportador ante SUNAT-Aduanas. "
            "Requiere autorizacion de SUNAT. Responsable solidario por los tributos. "
            "Su designacion puede ser para un despacho especifico o por poder general.\n\n"
            "3. TRANSPORTISTA: Empresa que realiza el transporte internacional de mercancias "
            "(naviera, aerolinea). Responsable de presentar el manifiesto de carga.\n\n"
            "4. DEPOSITO ADUANERO AUTORIZADO: Almacen habilitado para depositar mercancias "
            "bajo regimen de deposito.\n\n"
            "5. ALMACEN ADUANERO (TERMINAL DE ALMACENAMIENTO): Donde se almacenan las "
            "mercancias durante el proceso de despacho.\n\n"
            "6. EMPRESA DE SERVICIO POSTAL: Habilitada para efectuar despachos de importaciones "
            "y exportaciones por correo."
        ),
    },
    {
        "article": "LGA-CANALES",
        "section_path": "DL 1053 > Despacho Aduanero > Canales de control",
        "content": (
            "Canales de control en el despacho aduanero — SUNAT-Aduanas.\n\n"
            "El sistema de selectividad de SUNAT asigna un canal de control a cada declaracion "
            "aduanera (DAM) numerada:\n\n"
            "CANAL VERDE: Despacho libre sin revision documental ni fisica. La mercancia puede "
            "ser retirada del almacen inmediatamente tras la numeracion y pago de tributos. "
            "Se asigna a importadores con alto nivel de cumplimiento y mercancias de bajo riesgo.\n\n"
            "CANAL NARANJA (DOCUMENTARIO): Se requiere revision de los documentos de la "
            "declaracion (facturas, packing list, certificados de origen, permisos especiales). "
            "No incluye revision fisica de la mercancia.\n\n"
            "CANAL ROJO (FISICO): Requiere revision fisica de la mercancia por el especialista "
            "en aduanas. El reconocimiento fisico verifica:\n"
            "- Clasificacion arancelaria correcta (subpartida)\n"
            "- Descripcion y cantidad de la mercancia\n"
            "- Valoracion aduanera\n"
            "- Cumplimiento de normas tecnicas y permisos\n\n"
            "IMPORTADOR CONFIABLE: SUNAT otorga esta certificacion a importadores con "
            "alto cumplimiento tributario y aduanero. Tienen mayor acceso al canal verde "
            "y gozan de facilidades como el despacho en 48 horas."
        ),
    },
    {
        "article": "LGA-VALORACION",
        "section_path": "DL 1053 > Obligacion Tributaria Aduanera > Valoracion > Acuerdo OMC",
        "content": (
            "Valoracion Aduanera — Acuerdo de Valoracion de la OMC (DS 186-99-EF).\n\n"
            "La base imponible para calcular los derechos arancelarios es el Valor en Aduana, "
            "determinado siguiendo los metodos del Acuerdo de Valoracion de la OMC en orden "
            "de prelacion:\n\n"
            "1. METODO DEL VALOR DE TRANSACCION: Precio realmente pagado o por pagar "
            "(valor de la factura) + ajustes (flete, seguro hasta puerto peruano = CIF).\n"
            "Es el metodo principal; aplica cuando hay transaccion comercial real.\n\n"
            "2. VALOR DE TRANSACCION DE MERCANCIAS IDENTICAS: Se usa el valor CIF de "
            "mercancias identicas importadas en el mismo periodo.\n\n"
            "3. VALOR DE TRANSACCION DE MERCANCIAS SIMILARES: Similar al anterior con "
            "mercancias similares.\n\n"
            "4. METODO DEDUCTIVO: Se parte del precio de venta en el mercado interno.\n\n"
            "5. METODO COMPUTADO: Se parte del costo de produccion.\n\n"
            "6. METODO DE ULTIMA INSTANCIA: Criterio razonable basado en datos disponibles.\n\n"
            "SUNAT puede ajustar el valor declarado si existen dudas razonables sobre la veracidad "
            "del valor de transaccion (Duda Razonable — Procedimiento INTA-PE.01.10)."
        ),
    },
    {
        "article": "LGA-INFRACCIONES",
        "section_path": "DL 1053 > Infracciones y Sanciones Aduaneras",
        "content": (
            "Infracciones y Sanciones Aduaneras (Arts. 188-212 LGA y DS 010-2009-EF).\n\n"
            "TIPOLOGIA DE INFRACCIONES ADUANERAS:\n\n"
            "INFRACCIONES ADMINISTRATIVAS: Incumplimiento de obligaciones formales "
            "(presentacion tardia de documentos, errores en la DAM, no presentacion del "
            "manifiesto). Sancion: multa calculada en porcentaje del valor CIF o UIT.\n\n"
            "CONTRABANDO: Ingreso o salida de mercancias eludiendo el control aduanero "
            "(Ley 28008). Puede ser delito penal (pena privativa de libertad 5-12 anos) "
            "o infraccion administrativa segun el monto.\n\n"
            "DEFRAUDACION ADUANERA (Art. 8 Ley 28008): Declaracion falsa para pagar menos "
            "tributos o acogerse a beneficios. Pena: 5-8 anos.\n\n"
            "INFRACCIONES DEL TRANSPORTISTA: No presentar el manifiesto en plazo, "
            "no devolver el duplicado del conocimiento de embarque, etc.\n\n"
            "SANCIONES:\n"
            "- Multa (porcentaje del valor CIF o UIT segun infraccion)\n"
            "- Suspension de habilitacion del operador de comercio exterior\n"
            "- Cancelacion de la habilitacion\n"
            "- Comiso definitivo de la mercancia\n\n"
            "Regimen de incentivos: se puede reducir la multa hasta en 80% si se paga "
            "voluntariamente antes de la notificacion del valor."
        ),
    },
    # === TLC PERU-EEUU ===
    {
        "article": "TLC-EEUU-1",
        "section_path": "TLC Peru-EEUU > Acuerdo de Promocion Comercial > Acceso a mercados",
        "content": (
            "Acuerdo de Promocion Comercial (APC) Peru — Estados Unidos de America.\n"
            "Vigente desde el 1 de febrero de 2009. Suscrito en Washington D.C. en abril de 2006.\n\n"
            "Ambito y cobertura:\n"
            "El APC Peru-EEUU abarca:\n"
            "- Acceso preferencial para bienes (eliminacion de aranceles)\n"
            "- Comercio de servicios (servicios financieros, telecomunicaciones, profesionales)\n"
            "- Inversion (proteccion a inversiones estadounidenses en Peru y viceversa)\n"
            "- Propiedad intelectual\n"
            "- Compras gubernamentales\n"
            "- Asuntos laborales y medioambientales\n\n"
            "Beneficios arancelarios:\n"
            "El 80% de las exportaciones peruanas a EEUU ingresaron libres de arancel desde el "
            "primer dia de vigencia. El resto sigue un cronograma de desgravacion progresiva. "
            "Los principales productos beneficiados: textiles, confecciones, esparragos, "
            "mangos, uvas, palta, arandanos, quinua.\n\n"
            "El APC es administrado por el MINCETUR en coordinacion con el MEF, el Ministerio "
            "de Relaciones Exteriores y SUNAT."
        ),
    },
    {
        "article": "TLC-ORIGEN",
        "section_path": "TLC Peru-EEUU > Reglas de Origen > Certificacion",
        "content": (
            "Reglas de Origen en el APC Peru-EEUU (Capitulo IV y Anexos).\n\n"
            "Para acceder a la preferencia arancelaria, la mercancia debe:\n"
            "1. ORIGINARSE en Peru o EEUU: Ser totalmente obtenida en el pais, o sufrir una "
            "transformacion sustancial que cambie la clasificacion arancelaria, o cumplir con "
            "el requisito de contenido regional (valor de contenido regional - VCR).\n\n"
            "CERTIFICACION DE ORIGEN:\n"
            "A diferencia de otros TLC, el APC Peru-EEUU NO exige certificado de origen emitido "
            "por una autoridad gubernamental. En su lugar, el exportador emite una DECLARACION "
            "DE ORIGEN en la factura comercial u otro documento de envio, bajo su propia "
            "responsabilidad.\n\n"
            "Entidad certificadora en Peru: MINCETUR supervisa las reglas, pero el exportador "
            "emite la declaracion directamente.\n\n"
            "ACUMULACION: Los materiales originarios de cualquiera de los paises del TLC pueden "
            "considerarse como originarios del otro pais (acumulacion bilateral).\n\n"
            "Conservacion de documentos: 5 anos desde la importacion en EEUU o exportacion de Peru."
        ),
    },
    {
        "article": "TLC-CHINA-UE",
        "section_path": "TLC Peru > Acuerdos Peru-China y Peru-UE > Principios",
        "content": (
            "Otros Acuerdos Comerciales Vigentes del Peru.\n\n"
            "TLC PERU - CHINA (vigente desde el 1 de marzo de 2010):\n"
            "Es el acuerdo comercial mas importante en volumen para el Peru. China es el "
            "principal socio comercial peruano. El TLC cubre:\n"
            "- Acceso a mercados: Desgravacion arancelaria progresiva para el 95% del comercio.\n"
            "- Peru exporta principalmente: minerales (cobre, oro, zinc), harina de pescado, "
            "  uvas, palta y otros productos agropecuarios.\n"
            "- Peru importa de China: maquinaria, textiles, electronica, manufactura.\n"
            "Las reglas de origen exigen certificado de origen emitido por la Camara de Comercio "
            "de Lima u otras entidades habilitadas por el MINCETUR.\n\n"
            "TLC PERU - UNION EUROPEA (Acuerdo Comercial vigente desde 2013, "
            "modificado como Acuerdo de Asociacion 2024):\n"
            "- Cubre bienes, servicios, inversion y propiedad intelectual.\n"
            "- 0% arancel para la mayoria de exportaciones peruanas hacia la UE.\n"
            "- Exige cumplimiento de normas de sostenibilidad (medioambiente, laboral).\n"
            "- Sistema REX (Exportador Registrado) para auto-certificacion de origen "
            "  desde 2017 en reemplazo del Certificado EUR.1."
        ),
    },
    {
        "article": "MINCETUR-FUNC",
        "section_path": "MINCETUR > Funciones > Comercio Exterior",
        "content": (
            "Ministerio de Comercio Exterior y Turismo (MINCETUR) — Funciones en comercio exterior.\n\n"
            "El MINCETUR es el organismo del Poder Ejecutivo rector del sector Comercio Exterior "
            "y Turismo. Fue creado por Ley 27790 (2002).\n\n"
            "Funciones principales en comercio exterior:\n"
            "1. NEGOCIACION DE ACUERDOS COMERCIALES: Coordina y conduce las negociaciones de "
            "tratados de libre comercio y acuerdos comerciales bilaterales y multilaterales.\n"
            "2. ADMINISTRACION DE TLC: Supervisa el cumplimiento de los TLC vigentes, atiende "
            "consultas del sector privado sobre reglas de origen y preferencias.\n"
            "3. HABILITACION DE CERTIFICADORES DE ORIGEN: Autoriza a la Camara de Comercio "
            "de Lima, ADEX, Camara de Comercio de Lima, SNI y otras entidades para emitir "
            "certificados de origen.\n"
            "4. PROMOTION DE EXPORTACIONES: A traves de PROMPERÚ (organismo adscrito), "
            "promueve las exportaciones peruanas en el exterior.\n"
            "5. DEFENSA COMERCIAL: Coordina con el MEF y el INDECOPI los procedimientos "
            "antidumping y de salvaguardia.\n\n"
            "El Plan Estrategico Nacional Exportador (PENX) es el instrumento de politica "
            "de Estado para las exportaciones."
        ),
    },
    {
        "article": "SUNAT-ADUANAS",
        "section_path": "SUNAT > Intendencia de Aduanas > Procedimientos INTA",
        "content": (
            "SUNAT — Intendencia Nacional de Desarrollo e Implementacion Aduanera (INDA). "
            "Procedimientos INTA de despacho aduanero.\n\n"
            "Los principales Procedimientos Aduaneros de Importacion (INTA) son:\n\n"
            "INTA-PE.01.01: Importacion para el Consumo — Regula el despacho de importacion "
            "definitiva, incluyendo despacho anticipado, urgente y excepcional.\n\n"
            "INTA-PE.01.10: Valoracion Aduanera — Regula la determinacion del valor en aduana "
            "y el procedimiento de duda razonable.\n\n"
            "INTA-PG.01: Despacho Anticipado — El importador puede numerar la DAM hasta 30 dias "
            "antes del arribo del transporte. Ventajas:\n"
            "- Retiro de la mercancia en 48 horas del arribo\n"
            "- Menor tiempo en almacen = menores gastos de almacenaje\n"
            "- Preferencia en la asignacion de canales verdes\n\n"
            "PROCEDIMIENTO DE CANAL ROJO (reconocimiento fisico):\n"
            "- El especialista de aduana efectua el aforo fisico en el almacen\n"
            "- Puede resultado en: conforme, discrepancia en cantidad, diferencia en clasificacion\n"
            "- El importador puede presentar descargo antes de la liquidacion\n\n"
            "DRAWBACK: INTA-PE.11.06 — Regula la restitucion simplificada de derechos arancelarios."
        ),
    },
    {
        "article": "ARANCEL-NCCA",
        "section_path": "Arancel de Aduanas > Nomenclatura > SA y NANDINA",
        "content": (
            "Arancel de Aduanas del Peru — Nomenclatura y clasificacion arancelaria.\n\n"
            "El Peru utiliza la NANDINA (Nomenclatura Arancelaria Comun de la CAN — Comunidad "
            "Andina), basada en el Sistema Armonizado de Designacion y Codificacion de "
            "Mercancias (SA) de la OMA (Organizacion Mundial de Aduanas).\n\n"
            "Estructura de la subpartida arancelaria:\n"
            "XX.XX.XX.XX.XX\n"
            "- 2 digitos: Capitulo (ej. 61 = Prendas de vestir de punto)\n"
            "- 4 digitos: Partida\n"
            "- 6 digitos: Subpartida del SA (nivel internacional)\n"
            "- 8 digitos: Subpartida NANDINA (nivel CAN)\n"
            "- 10 digitos: Subpartida Nacional (nivel Peru, cuando aplica)\n\n"
            "CLASSIFICATION ADUANERA: El Registrador Aduanero (INDA) puede revisar la "
            "clasificacion declarada. Si hay discrepancia en la clasificacion, puede generar "
            "diferencia en tributos pagados y, potencialmente, una infraccion aduanera.\n\n"
            "Recursos contra clasificacion: El importador puede interponer reclamacion ante "
            "el Intendente de Aduana y apelacion ante el Tribunal Fiscal (en materia tributaria) "
            "o recurrir a la OMC para consultas tecnicas sobre clasificacion."
        ),
    },
    {
        "article": "COMERCIO-INCOTERMS",
        "section_path": "Comercio Exterior > Contratos > Incoterms 2020",
        "content": (
            "Incoterms 2020 (International Commercial Terms) — Reglas de la Camara de Comercio "
            "Internacional (CCI/ICC). Aunque no son normas peruanas, son de aplicacion generalizada "
            "en el comercio exterior peruano.\n\n"
            "Principales Incoterms para el comercio internacional peruano:\n\n"
            "FOB (Free On Board): El vendedor entrega la mercancia a bordo del buque en el puerto "
            "de origen. Los costos y riesgos se transfieren al comprador desde ese momento. "
            "Es el Incoterm mas usado en exportaciones peruanas.\n\n"
            "CIF (Cost, Insurance and Freight): El vendedor paga el flete y seguro hasta el puerto "
            "de destino. Es la base para calcular el Valor en Aduana en importaciones al Peru.\n\n"
            "EXW (Ex Works): El vendedor pone la mercancia a disposicion del comprador en sus "
            "instalaciones. El comprador asume todos los costos desde la fabrica.\n\n"
            "DDP (Delivered Duty Paid): El vendedor asume todos los costos, incluyendo los "
            "derechos de importacion en el pais del comprador.\n\n"
            "La eleccion del Incoterm afecta directamente la base imponible aduanera y la "
            "distribucion de responsabilidades entre exportador e importador."
        ),
    },
    {
        "article": "COMERCIO-FINANCIAMIENTO",
        "section_path": "Comercio Exterior > Financiamiento > COFIDE y banca de comercio exterior",
        "content": (
            "Financiamiento del Comercio Exterior en el Peru.\n\n"
            "COFIDE (Corporacion Financiera de Desarrollo S.A.):\n"
            "Banco de desarrollo del Estado peruano que canaliza recursos hacia el sector "
            "productivo y exportador a traves de intermediarios financieros. Ofrece:\n"
            "- Lineas de credito para capital de trabajo exportador\n"
            "- Financiamiento de mediano y largo plazo para inversion productiva\n"
            "- Programas de apoyo a MIPYMES exportadoras\n\n"
            "INSTRUMENTOS DE FINANCIAMIENTO:\n"
            "1. CARTA DE CREDITO (L/C): Instrumento bancario por el que el banco del importador "
            "garantiza el pago al exportador cuando presenta documentos conformes. "
            "Es el instrumento de mayor seguridad para el exportador.\n\n"
            "2. COBRANZA DOCUMENTARIA: El banco actua como intermediario para el cobro.\n\n"
            "3. SEGURO DE CREDITO A LA EXPORTACION: SECREX y otras aseguradoras cubren el "
            "riesgo de incumplimiento del comprador extranjero.\n\n"
            "4. FACTORING INTERNACIONAL: El exportador vende sus cuentas por cobrar "
            "a un factor (banco o empresa especializada) para obtener liquidez inmediata."
        ),
    },
    {
        "article": "COMERCIO-DRAWBACK",
        "section_path": "DL 1053 > Regimenes Aduaneros > Regimen de Perfeccionamiento > Drawback",
        "content": (
            "Drawback — Restitucion de Derechos Arancelarios (DS 282-2016-EF y modificatorias).\n\n"
            "El Drawback es el regimen por el cual se restituyen, total o parcialmente, los "
            "tributos que gravaron la importacion de mercancias incorporadas o consumidas en la "
            "produccion de bienes exportados definitivamente.\n\n"
            "TASA ACTUAL: 3% del valor FOB de las exportaciones, con un maximo de US$ 20,000 "
            "por exportacion (o serie de exportaciones de la misma mercancia).\n\n"
            "REQUISITOS:\n"
            "1. Exportar el producto manufacturado dentro de los 36 meses de importados los insumos.\n"
            "2. El valor CIF de los insumos importados no debe superar el 50% del valor FOB exportado.\n"
            "3. No pueden acogerse: las empresas que importen y reexporten sin transformacion.\n\n"
            "PROCEDIMIENTO:\n"
            "1. El exportador presenta la solicitud de restitucion ante SUNAT.\n"
            "2. SUNAT evalua la solicitud y realiza el deposito en 5 dias habiles.\n"
            "3. SUNAT puede realizar verificacion posterior de las exportaciones beneficiadas.\n\n"
            "DEFRAUDACION EN DRAWBACK: Solicitar drawback sobre mercancias que no incorporan "
            "insumos importados o que lo hacen en porcentaje inferior, constituye delito de "
            "defraudacion de rentas de aduana (Ley 28008)."
        ),
    },
    {
        "article": "COMERCIO-ADMISION-TEMP",
        "section_path": "DL 1053 > Regimenes Aduaneros > Exportacion temporal y reimportacion",
        "content": (
            "Exportacion Temporal para Reimportacion y Regimenes Especiales.\n\n"
            "EXPORTACION TEMPORAL PARA REIMPORTACION EN EL MISMO ESTADO:\n"
            "Permite la salida temporal de mercancias nacionales o nacionalizadas para ser "
            "reimportadas sin modificacion. Ejemplos: maquinaria que sale para reparacion, "
            "muestras para exposicion en ferias internacionales.\n"
            "Plazo maximo: 12 meses. No genera pago de tributos en la salida ni en el retorno "
            "(si se reimporta dentro del plazo).\n\n"
            "EXPORTACION TEMPORAL PARA PERFECCIONAMIENTO PASIVO:\n"
            "Mercancias que salen del Peru para ser transformadas o reparadas en el exterior "
            "y luego reimportadas. Los tributos se calculan solo sobre el valor agregado "
            "realizado en el exterior (la transformacion o reparacion), no sobre el total.\n\n"
            "ZONA FRANCA (CETICOS y ZOFRATACNA):\n"
            "Zonas de tratamiento aduanero especial donde las mercancias ingresan sin pago de "
            "tributos. Principales:\n"
            "- ZOFRATACNA (Tacna): zona franca comercial e industrial.\n"
            "- CETICOS (Ilo, Matarani, Paita): zonas de procesamiento industrial.\n"
            "Las mercancias producidas en zonas francas que ingresan al resto del Peru pagan "
            "tributos como si fueran importaciones."
        ),
    },
]
