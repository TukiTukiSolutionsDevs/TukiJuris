"""
Seed: Derecho Registral — Expansion de conocimiento registral peruano.

Normas cubiertas:
- Ley 26366 — Ley de Creacion del SINARP y SUNARP
- Reglamento General de los Registros Publicos (Res. 126-2012-SUNARP-SN)
- Codigo Civil Arts. 2008-2045 (Registros Publicos)
- Directivas SUNARP: inscripcion de predios, sociedades, vehiculos, personas naturales
- Procedimiento registral: titulo, calificacion, inscripcion, tacha, observacion, recursos
"""

REGISTRAL_EXT_ARTICLES = [
    # === LEY 26366 — SINARP Y SUNARP ===
    {
        "article": "LEY26366-1",
        "section_path": "Ley 26366 > SINARP > Creacion y objeto",
        "content": (
            "Ley 26366 — Ley de Creacion del Sistema Nacional de los Registros Publicos y de la "
            "Superintendencia Nacional de los Registros Publicos (SUNARP), promulgada el 14 de octubre de 1994.\n\n"
            "Articulo 1.- Crease el Sistema Nacional de los Registros Publicos (SINARP), el cual tiene por objeto "
            "dictar las politicas tecnico-administrativas de los Registros Publicos que lo integran, coordinando y "
            "supervisando la inscription de los actos o contratos en los Registros que lo conforman.\n\n"
            "El SINARP integra en un sistema unitario a todos los Registros Publicos del pais, bajo la supervision "
            "y gestion de la SUNARP. Los Registros integrantes son:\n"
            "1. Registro de Propiedad Inmueble (predios urbanos y rusticos)\n"
            "2. Registro de Personas Juridicas (SA, SRL, asociaciones, fundaciones)\n"
            "3. Registro de Personas Naturales (estado civil, sucesiones, mandatos)\n"
            "4. Registro de Bienes Muebles (vehiculos, embarcaciones, aeronaves, garantias mobiliarias)\n\n"
            "La SUNARP es el ente rector del SINARP, con personeria juridica de derecho publico, autonomia "
            "registral, tecnica, economica, financiera y administrativa."
        ),
    },
    {
        "article": "LEY26366-2",
        "section_path": "Ley 26366 > SUNARP > Funciones y atribuciones",
        "content": (
            "Funciones y atribuciones de la SUNARP (Ley 26366, Art. 12 y siguientes):\n\n"
            "a) Planificar, organizar, normar, dirigir, coordinar y supervisar la inscription de los actos y "
            "contratos en los Registros Publicos que conforman el SINARP.\n"
            "b) Dictar las politicas, normas tecnico-registrales y administrativas que regulan la actividad "
            "de los Registros integrantes del Sistema.\n"
            "c) Capacitar y acreditar a los Registradores Publicos y al personal registral.\n"
            "d) Promover la interconexion registral a nivel nacional y la publicidad registral formal "
            "(certificados, copias literales, informes).\n"
            "e) El Tribunal Registral es el organo de segunda instancia que resuelve las apelaciones "
            "contra las observaciones, tachas y denegatoria de inscripcion emitidas por los Registradores.\n\n"
            "La SUNARP tiene presencia a traves de Zonas Registrales en todo el pais, siendo la Zona "
            "Registral IX - Sede Lima la de mayor volumen de titulos."
        ),
    },
    # === REGLAMENTO GENERAL — PRINCIPIOS REGISTRALES ===
    {
        "article": "RG-LEGALIDAD",
        "section_path": "Reglamento General > Principios Registrales > Legalidad",
        "content": (
            "Principio de Legalidad — Reglamento General de los Registros Publicos "
            "(Res. 126-2012-SUNARP-SN, Art. V).\n\n"
            "El Registrador Publico y el Tribunal Registral, en sus respectivas instancias, calificaran la "
            "legalidad de los documentos en cuya virtud se solicita la inscripcion, la capacidad de los "
            "otorgantes y la validez del acto, por lo que resulte de ellos, de sus antecedentes y de los "
            "asientos de los Registros Publicos.\n\n"
            "El alcance de la calificacion comprende:\n"
            "1. Legalidad de los documentos presentados (escritura publica, resolucion judicial, etc.)\n"
            "2. Capacidad juridica y legitimidad de los otorgantes\n"
            "3. Validez del acto o contrato materia de inscripcion\n"
            "4. Compatibilidad con los asientos registrales existentes\n"
            "5. Cumplimiento de los requisitos establecidos en las normas registrales\n\n"
            "El Registrador no puede calificar el fondo del asunto cuando el titulo proviene de resolucion "
            "judicial firme, salvo que contradiga un asiento vigente."
        ),
    },
    {
        "article": "RG-ROGACION",
        "section_path": "Reglamento General > Principios Registrales > Rogacion y especialidad",
        "content": (
            "Principio de Rogacion (Art. IV Reglamento General SUNARP):\n"
            "Los asientos registrales se extienden a instancia de los otorgantes del acto o derecho, "
            "o de la persona a favor de quien se haya establecido, o de quien tenga interes en asegurar "
            "el derecho que se trate de inscribir. Excepcionalmente, la inscripcion puede realizarse "
            "de oficio por mandato de la ley.\n\n"
            "Principio de Especialidad (Art. IX Reglamento General SUNARP):\n"
            "Por cada bien o persona juridica se abre una partida registral independiente, en donde se "
            "extienden los asientos referentes a los actos inscribibles. Cada partida constituye la "
            "historia juridica del bien o persona.\n\n"
            "La partida registral se identifica con un numero unico (Partida Electronica N°...) y contiene:\n"
            "- Asiento de inscripcion inicial (dominio, constitucion, matricula)\n"
            "- Asientos de inscripcion sucesivos (transferencias, cargas, gravamenes)\n"
            "- Asientos de cancelacion\n"
            "Cada asiento registral consigna: numero correlativo, descripcion del acto, datos del titulo, "
            "nombre del Registrador y fecha de inscripcion."
        ),
    },
    {
        "article": "RG-TRACTO",
        "section_path": "Reglamento General > Principios Registrales > Tracto sucesivo y prioridad",
        "content": (
            "Principio de Tracto Sucesivo (Art. VI Reglamento General SUNARP):\n"
            "Ningun inscripcion, salvo la primera, se efectuara sin que este inscrito o se inscriba "
            "el derecho de donde emana o el acto previo necesario o adecuado para su extension.\n\n"
            "Ejemplo: Para inscribir una hipoteca, debe estar inscrito el dominio a favor del hipotecante. "
            "Para inscribir una transferencia, debe estar inscrito el dominio a favor del transferente.\n\n"
            "Excepciones al tracto sucesivo:\n"
            "- Tracto abreviado (Art. 11 Reglamento): permite omitir inscripcion de actos "
            "previos cuando existe causa justificada (herencias, reorganizacion de sociedades).\n\n"
            "Principio de Prioridad (Art. X Reglamento General SUNARP):\n"
            "La prioridad en el tiempo de la inscripcion determina la preferencia de los derechos que "
            "otorga el Registro. El titulo que ingresa primero al Registro tiene prioridad sobre los "
            "titulos que ingresen posteriormente que sean incompatibles. La prioridad se determina "
            "por la fecha y hora del asiento de presentacion."
        ),
    },
    {
        "article": "RG-FEPUBLICA",
        "section_path": "Reglamento General > Principios Registrales > Fe publica registral y legitimacion",
        "content": (
            "Principio de Legitimacion (Art. VII Reglamento General SUNARP):\n"
            "Los asientos de los Registros Publicos se presumen exactos y validos. Producen todos "
            "sus efectos y legitiman al titular registral para actuar conforme a ellos, mientras no "
            "se rectifiquen en los terminos establecidos en este Reglamento o se declare judicialmente "
            "su invalidez.\n\n"
            "Principio de Fe Publica Registral (Art. 2014 CC y Art. VIII Reglamento SUNARP):\n"
            "El tercero que de buena fe adquiere a titulo oneroso algun derecho de persona que en el "
            "Registro aparece con facultades para otorgarlo, mantiene su adquisicion una vez inscrito "
            "su derecho, aunque despues se anule, rescinda, cancele o resuelva el del otorgante por "
            "virtud de causas que no consten en los asientos registrales y los titulos archivados.\n\n"
            "Requisitos para invocar la fe publica registral:\n"
            "1. Adquisicion a titulo oneroso\n"
            "2. Buena fe del adquirente (desconocimiento de vicios no publicitados)\n"
            "3. Inscripcion del derecho adquirido\n"
            "4. El transmitente debe aparecer en el Registro con facultades para transferir\n\n"
            "La buena fe se presume mientras no se pruebe que el adquirente conocia la inexactitud del Registro."
        ),
    },
    # === PROCEDIMIENTO REGISTRAL ===
    {
        "article": "PROC-REG-1",
        "section_path": "Reglamento General > Procedimiento Registral > Titulo y presentacion",
        "content": (
            "Procedimiento registral — Titulo y presentacion (Arts. 7-23 Reglamento General SUNARP).\n\n"
            "TITULO: Es el documento o documentos en que se fundamenta inmediatamente el derecho de la "
            "persona a cuyo favor ha de practicarse la inscripcion, y que induce directamente a la "
            "misma. Pueden ser:\n"
            "- Escritura publica (ante Notario Publico)\n"
            "- Resolucion judicial (sentencia, auto, exhorto)\n"
            "- Resolucion administrativa (resolucion de gobierno regional, municipal, etc.)\n"
            "- Formulario registral (para actos de menor cuantia)\n\n"
            "ASIENTO DE PRESENTACION: Al ingresar el titulo, el diario del registro genera un asiento "
            "de presentacion que contiene:\n"
            "- Numero de titulo\n"
            "- Fecha y hora de ingreso (determina la prioridad)\n"
            "- Oficina Registral receptora\n"
            "- Acto a inscribir y partida registral afectada\n"
            "La vigencia del asiento de presentacion es de 35 dias habiles, prorrogable por 25 dias habiles adicionales."
        ),
    },
    {
        "article": "PROC-REG-2",
        "section_path": "Reglamento General > Procedimiento Registral > Calificacion e inscripcion",
        "content": (
            "Calificacion registral e inscripcion (Arts. 31-48 Reglamento General SUNARP).\n\n"
            "CALIFICACION: El Registrador tiene un plazo de 7 dias habiles para calificar el titulo. "
            "Puede resultar en:\n"
            "1. INSCRIPCION: El titulo cumple todos los requisitos. Se extiende el asiento registral.\n"
            "2. OBSERVACION: El titulo tiene defectos subsanables. El Registrador indica los documentos "
            "o requisitos adicionales. El usuario tiene el plazo de vigencia del asiento de presentacion "
            "para subsanar.\n"
            "3. TACHA SUSTANTIVA: El titulo adolece de defecto insubsanable (acto prohibido, nulo de "
            "pleno derecho, incompatible con asiento vigente).\n"
            "4. TACHA POR CADUCIDAD: El asiento de presentacion vencio sin subsanacion.\n"
            "5. LIQUIDACION: Se requiere pago adicional de derechos registrales.\n\n"
            "INSCRIPCION: El asiento registral es la constancia escrita en la partida registral del acto "
            "o derecho inscrito. Es definitivo e inatacable salvo por resolucion judicial o del Tribunal Registral."
        ),
    },
    {
        "article": "PROC-REG-3",
        "section_path": "Reglamento General > Procedimiento Registral > Recursos > Apelacion",
        "content": (
            "Recursos en el procedimiento registral (Arts. 142-158 Reglamento General SUNARP).\n\n"
            "RECURSO DE APELACION ante el Tribunal Registral:\n"
            "Procede contra:\n"
            "- Observaciones del Registrador\n"
            "- Tachas sustantivas\n"
            "- Denegatoria de inscripcion\n\n"
            "Plazo para apelar: 15 dias habiles desde la notificacion de la observacion o tacha. "
            "La apelacion se interpone ante el Registrador que emitio la calificacion, quien eleva "
            "el expediente al Tribunal Registral sin emitir nuevo pronunciamiento.\n\n"
            "El Tribunal Registral esta integrado por Salas conformadas por 3 Vocales. Resuelve en "
            "pleno o en sala. Sus resoluciones:\n"
            "1. Revocan la observacion/tacha del Registrador y ordenan la inscripcion\n"
            "2. Confirman la observacion o tacha\n"
            "3. Amplian los fundamentos de la observacion\n\n"
            "Las resoluciones del Tribunal Registral constituyen precedentes de observancia obligatoria "
            "cuando asi lo aprueben. Solo son impugnables en via judicial (accion contencioso-administrativa)."
        ),
    },
    # === CODIGO CIVIL — REGISTROS PUBLICOS ===
    {
        "article": "CC-2008",
        "section_path": "Codigo Civil > Libro IX > Registros Publicos > Art. 2008-2016",
        "content": (
            "Codigo Civil, Libro IX — Registros Publicos (Arts. 2008-2016).\n\n"
            "Art. 2008.- Los derechos reales sobre inmuebles inscritos en el Registro "
            "de la Propiedad Inmueble se sujetan a las disposiciones de este Libro y a "
            "las del Codigo respectivo.\n\n"
            "Art. 2010.- La inscripcion se hace en virtud de titulo que conste en instrumento "
            "publico, salvo disposicion contraria.\n\n"
            "Art. 2012.- Se presume, sin admitirse prueba en contrario, que toda persona "
            "tiene conocimiento del contenido de las inscripciones (principio de publicidad).\n\n"
            "Art. 2013.- El contenido de la inscripcion se presume cierto y produce todos "
            "sus efectos, mientras no se rectifique o se declare judicialmente su invalidez "
            "(principio de legitimacion).\n\n"
            "Art. 2014.- El tercero que de buena fe adquiere a titulo oneroso algun derecho "
            "de persona que en el Registro aparece con facultades para otorgarlo, mantiene su "
            "adquisicion una vez inscrito su derecho, aunque despues se anule el del otorgante "
            "(fe publica registral).\n\n"
            "Art. 2016.- La prioridad en el tiempo de la inscripcion determina la preferencia de "
            "los derechos que otorga el Registro."
        ),
    },
    {
        "article": "CC-2019",
        "section_path": "Codigo Civil > Libro IX > Registros Publicos > Actos inscribibles",
        "content": (
            "Codigo Civil, Art. 2019 — Actos y derechos inscribibles en el Registro de Predios:\n\n"
            "Son inscribibles en el Registro de Propiedad Inmueble:\n"
            "1. Los actos y contratos que constituyen, declaren, transmitan, extingan, modifiquen "
            "o limiten los derechos reales sobre inmuebles.\n"
            "2. Los contratos de opcion.\n"
            "3. Los pactos de reserva de propiedad y los de retroventa.\n"
            "4. El cumplimiento total o parcial de las condiciones de las cuales dependan los "
            "efectos de los actos o contratos registrados.\n"
            "5. Las restricciones en las facultades del titular del derecho inscrito.\n"
            "6. Los contratos de arrendamiento.\n"
            "7. Los embargos y demandas verosimilmente acreditadas.\n"
            "8. Las sentencias u otras resoluciones que a criterio del juez se refieran a actos "
            "o contratos inscribibles.\n"
            "9. Las autorizaciones judiciales que permitan practicar actos inscribibles sobre inmuebles.\n\n"
            "Art. 2022.- Para oponer derechos reales sobre inmuebles a quienes tambien tienen derechos "
            "reales sobre los mismos, es preciso que el derecho que se opone este inscrito con anterioridad "
            "al de aquel a quien se opone (oponibilidad registral)."
        ),
    },
    {
        "article": "CC-2034",
        "section_path": "Codigo Civil > Libro IX > Registros Publicos > Inscripcion de PJ",
        "content": (
            "Codigo Civil, Art. 2025 y ss. — Inscripciones en el Registro de Personas Juridicas.\n\n"
            "Art. 2025.- Se inscribe en el Registro de Personas Juridicas:\n"
            "a) El pacto social y los estatutos de las personas juridicas de derecho privado, "
            "asi como su modificacion.\n"
            "b) El nombramiento de representantes legales de personas juridicas y su revocacion.\n"
            "c) Los poderes otorgados y su revocacion.\n"
            "d) La transformacion, fusion, escision, disolucion y liquidacion de personas juridicas.\n\n"
            "Art. 2026.- La inscripcion en el Registro de Personas Juridicas produce efecto "
            "declarativo respecto a terceros desde el momento de la inscripcion.\n\n"
            "Art. 2027.- El Registro de Personas Naturales comprende:\n"
            "- Registro de Mandatos y Poderes\n"
            "- Registro de Testamentos\n"
            "- Registro de Sucesiones Intestadas\n"
            "- Registro Personal (sentencias, resoluciones)\n"
            "- Registro de Comerciantes\n\n"
            "El Registro de Bienes Muebles comprende el Registro Vehicular y el Registro "
            "de Garantias Mobiliarias (Ley 28677)."
        ),
    },
    # === DIRECTIVAS SUNARP ===
    {
        "article": "SUNARP-PREDIOS",
        "section_path": "SUNARP > Directivas > Registro de Predios",
        "content": (
            "Registro de Predios — Directiva N° 013-2003-SUNARP-SN y normas complementarias.\n\n"
            "El Registro de Predios unifica el Registro de Propiedad Inmueble, el Registro Predial "
            "Urbano y la Seccion Especial de Predios Rurales.\n\n"
            "Actos inscribibles mas frecuentes:\n"
            "1. INMATRICULACION: Primera inscripcion del predio en el Registro. Requiere titulo "
            "de dominio, plano catastral y verificacion de no duplicidad de partidas.\n"
            "2. COMPRAVENTA: Transferencia de propiedad. Requiere escritura publica ante notario.\n"
            "3. HIPOTECA: Gravamen sobre el inmueble para garantizar una deuda. Se inscribe en la "
            "partida del inmueble hipotecado.\n"
            "4. EMBARGO: Medida cautelar o ejecutiva que afecta el inmueble. Se inscribe por "
            "mandato judicial.\n"
            "5. INDEPENDIZACION: Division de un predio en dos o mas. Requiere plano y autorizacion.\n"
            "6. ACUMULACION: Union de dos o mas predios en uno. Requiere que los predios sean "
            "colindantes y pertenezcan al mismo propietario.\n"
            "7. ANTICRETICO y SUPERFICIE: Derechos reales inscribibles sobre el predio.\n\n"
            "La SUNARP implemento el sistema de georeferenciacion (Catastro Registral) para "
            "identificar la ubicacion exacta de los predios y evitar duplicidades."
        ),
    },
    {
        "article": "SUNARP-VEHICULOS",
        "section_path": "SUNARP > Directivas > Registro de Vehiculos",
        "content": (
            "Registro de Vehiculos (Registro de Bienes Muebles) — Reglamento DS 017-2009-MTC.\n\n"
            "La inscripcion registral de vehiculos es obligatoria y constitutiva de derechos. "
            "Los principales actos inscribibles son:\n\n"
            "1. MATRICULA INICIAL: Primera inscripcion del vehiculo nuevo. La realiza el concesionario "
            "o importador con los documentos de nacionalizacion o factura original.\n"
            "2. TRANSFERENCIA DE PROPIEDAD: Compraventa de vehiculo usado. Requiere la firma del "
            "transferente y adquirente ante Notario o en formato de la SUNARP.\n"
            "3. HIPOTECA VEHICULAR: Garantia sobre el vehiculo para creditos. Muy comun en "
            "leasing y creditos vehiculares.\n"
            "4. PRENDA: Garantia mobiliaria sobre el vehiculo (antes regida por el CC, ahora por "
            "la Ley de Garantias Mobiliarias - Ley 28677).\n\n"
            "Plazos para inscribir transferencias:\n"
            "- El adquirente tiene 30 dias habiles para inscribir la transferencia.\n"
            "- La falta de inscripcion no afecta la validez entre las partes pero genera "
            "inoponibilidad frente a terceros (ex. otro acreedor que embargue el vehiculo).\n\n"
            "ALERTA REGISTRAL: SUNARP ofrece el servicio de Alerta Registral que notifica al "
            "propietario registral cuando se presenta un titulo sobre su bien."
        ),
    },
    {
        "article": "SUNARP-SOCIEDADES",
        "section_path": "SUNARP > Directivas > Registro de Sociedades",
        "content": (
            "Registro de Personas Juridicas — Seccion Sociedades (LGS Ley 26887 y Reglamento SUNARP).\n\n"
            "Proceso de inscripcion de una sociedad:\n"
            "1. Minuta de constitucion (elaborada por abogado)\n"
            "2. Escritura publica de constitucion (ante Notario)\n"
            "3. Presentacion del titulo al Registro de Personas Juridicas\n"
            "4. Calificacion registral (7 dias habiles)\n"
            "5. Inscripcion en el Registro y obtencion de la partida registral\n\n"
            "Actos inscribibles posteriores:\n"
            "- Modificacion de estatuto (aumento/reduccion de capital, cambio de denominacion)\n"
            "- Nombramiento y remocion de directores y gerentes\n"
            "- Emision de poderes\n"
            "- Transferencia de acciones (para SA sin directorio puede constar en libro de matricula)\n"
            "- Reorganizacion (fusion, escision, transformacion)\n"
            "- Disolucion, nombramiento de liquidador y extincion\n\n"
            "Publicidad registral:\n"
            "- Copia literal de partida: documento que reproduce los asientos registrales\n"
            "- Vigencia de poder: certifica quien tiene la representacion legal vigente\n"
            "- Certificado literal: para uso en tramites judiciales, notariales y bancarios"
        ),
    },
    {
        "article": "SUNARP-GARANTIAS",
        "section_path": "SUNARP > Garantias Mobiliarias > Ley 28677",
        "content": (
            "Ley de la Garantia Mobiliaria (Ley 28677) y su reglamento (DS 006-2015-JUS).\n\n"
            "La Garantia Mobiliaria puede constituirse sobre toda clase de bienes muebles, "
            "presentes o futuros, corporales o incorporales (cuentas por cobrar, derechos, "
            "inventarios, equipos, software, marcas, entre otros).\n\n"
            "Registro Mobiliario de Contratos (RMC): inscripcion de garantias mobiliarias que "
            "no son vehiculos ni aeronaves. Se inscribe en el Registro de Bienes Muebles de SUNARP.\n\n"
            "Requisitos para la inscripcion de garantia mobiliaria:\n"
            "1. Acto constitutivo (escritura publica o documento privado con firma legalizada)\n"
            "2. Descripcion del bien gravado\n"
            "3. Identificacion del garante y del acreedor garantizado\n"
            "4. Monto de la obligacion garantizada\n"
            "5. Plazo de la garantia\n\n"
            "Efectos de la inscripcion:\n"
            "- Oponibilidad frente a terceros desde la inscripcion\n"
            "- Prioridad frente a otras garantias constituidas posteriormente\n"
            "- Permite la ejecucion extrajudicial de la garantia (venta directa del bien)\n"
            "segun el procedimiento de ejecucion mobiliaria."
        ),
    },
    {
        "article": "SUNARP-PUBLICIDAD",
        "section_path": "SUNARP > Publicidad Registral > Formas y efectos",
        "content": (
            "Publicidad Registral Formal — Directiva N° 003-2023-SUNARP-SN.\n\n"
            "La publicidad registral formal son los mecanismos que permiten a cualquier persona "
            "conocer el contenido de los asientos registrales. Las principales formas son:\n\n"
            "1. COPIA LITERAL: Reproduccion fiel del contenido de la partida registral. "
            "Sirve como prueba de los actos y derechos inscritos. Puede ser:\n"
            "   - Copia literal simple: para informacion\n"
            "   - Copia literal con sello de seguridad: para tramites oficiales\n\n"
            "2. CERTIFICADO REGISTRAL INMOBILIARIO (CRI): Documento que acredita el estado "
            "de un predio (titular registral, cargas, gravamenes, medidas cautelares).\n\n"
            "3. VIGENCIA DE PODER: Certifica que el poder inscrito se encuentra vigente y quien "
            "es el representante legal con sus facultades.\n\n"
            "4. CERTIFICADO NEGATIVO DE BIENES: Certifica que una persona no tiene bienes "
            "inscritos en el Registro (util en tramites de beneficios sociales).\n\n"
            "5. PUBLICIDAD EN LINEA: A traves del portal SUNARP (www.sunarp.gob.pe) se pueden "
            "consultar partidas electronicas e indice de personas en linea.\n\n"
            "El principio de publicidad registral implica que la ignorancia del contenido del "
            "Registro no puede ser alegada por nadie (Art. 2012 CC)."
        ),
    },
    {
        "article": "SUNARP-CATASTRO",
        "section_path": "SUNARP > Catastro Registral > Georeferenciacion",
        "content": (
            "Catastro Registral y georeferenciacion de predios — SUNARP.\n\n"
            "El Catastro Registral es el conjunto de informacion de los predios inscritos en el "
            "Registro de Predios. Su funcion principal es identificar fisicamente los predios para "
            "evitar duplicidad de partidas y superposicion de areas.\n\n"
            "Normas que regulan el catastro:\n"
            "- DL 1166 (2013): Aprueba la implementacion y prestacion de los servicios del Sistema "
            "  Nacional Integrado de Informacion Catastral Predial (SNCP).\n"
            "- DS 005-2006-JUS: Reglamento de organizacion del catastro registral.\n\n"
            "Procedimientos vinculados al catastro registral:\n"
            "1. GEOREFERENCIACION: Vinculacion del predio registral con coordenadas UTM. "
            "Permite identificar el predio en el mapa catastral.\n"
            "2. DETERMINACION DE AREAS, LINDEROS Y MEDIDAS PERIMETRICAS: Actualizacion de "
            "la descripcion fisica del predio inscrito.\n"
            "3. ACUMULACION E INDEPENDIZACION: Deben contar con plano catastral visado.\n\n"
            "El COFOPRI (Organismo de Formalizacion de la Propiedad Informal) y las municipalidades "
            "son las principales entidades que generan titulos de propiedad para inmatriculacion, "
            "especialmente en zonas urbano-marginales."
        ),
    },
    {
        "article": "SUNARP-TRIBUNAL",
        "section_path": "SUNARP > Tribunal Registral > Precedentes de observancia obligatoria",
        "content": (
            "Tribunal Registral de SUNARP — Precedentes de Observancia Obligatoria.\n\n"
            "El Tribunal Registral es el organo de segunda instancia registral. Sus resoluciones "
            "pueden constituir precedentes de observancia obligatoria cuando son aprobadas "
            "en pleno y publicadas en el Diario Oficial El Peruano.\n\n"
            "Los precedentes vinculan a todos los registradores del pais y no pueden ser "
            "desconocidos en la calificacion registral. Los mas importantes se refieren a:\n\n"
            "- Calificacion de poderes y representacion\n"
            "- Transferencias de inmuebles (limites de la calificacion de escrituras publicas)\n"
            "- Inscripcion de sociedades (acuerdos de JGA, quorum, representacion)\n"
            "- Independizacion y acumulacion de predios\n"
            "- Hipotecas y garantias mobiliarias\n"
            "- Embargos y medidas cautelares judiciales\n\n"
            "IMPUGNACION DE RESOLUCIONES DEL TRIBUNAL:\n"
            "Las resoluciones del Tribunal Registral solo son impugnables en la via judicial "
            "mediante demanda contencioso-administrativa ante el Poder Judicial. El Tribunal "
            "no puede ser obligado a cambiar su criterio por via administrativa.\n\n"
            "PLENOS REGISTRALES: El Tribunal se reune en pleno para unificar criterios y emitir "
            "acuerdos que vinculan a todos los registradores. Hay plenos ordinarios (trimestrales) "
            "y extraordinarios."
        ),
    },
    {
        "article": "CC-2022-OPONIBILIDAD",
        "section_path": "Codigo Civil > Libro IX > Registros > Art. 2022 > Oponibilidad",
        "content": (
            "Oponibilidad de Derechos sobre Inmuebles — Codigo Civil Art. 2022.\n\n"
            "Art. 2022 CC: Para oponer derechos reales sobre inmuebles a quienes tambien tienen "
            "derechos reales sobre los mismos, es preciso que el derecho que se opone este "
            "inscrito con anterioridad al de aquel a quien se opone. Si se trata de derechos "
            "de diferente naturaleza se aplican las disposiciones del Derecho comun.\n\n"
            "INTERPRETACION DEL ART. 2022 (jurisprudencia y doctrina):\n"
            "El primer parrafo aplica cuando compiten dos derechos reales de igual naturaleza "
            "(ej. dos compradores del mismo inmueble): gana quien inscribe primero, con "
            "independencia de quien firmo el contrato antes.\n\n"
            "El segundo parrafo (derechos de diferente naturaleza) ha generado debate sobre "
            "si se aplica la inscripcion registral o el Derecho comun para resolver conflictos "
            "entre, por ejemplo, un acreedor con embargo inscrito vs. un comprador con contrato "
            "anterior sin inscribir. La mayoria de la jurisprudencia ha optado por la inscripcion "
            "registral como criterio determinante.\n\n"
            "TRACTO ABREVIADO (Art. 11 Reglamento General): Permite omitir la inscripcion de "
            "actos intermedios cuando hay una sola persona que interviene como transmitente "
            "y adquirente en actos sucesivos (reorganizaciones societarias, herencias)."
        ),
    },
]
