"""
Seed: Derecho Administrativo — Expansion de conocimiento en derecho administrativo peruano.

Normas cubiertas:
- TUO de la Ley 27444 — Ley del Procedimiento Administrativo General (DS 004-2019-JUS)
- Principios del procedimiento administrativo (Arts. 1-12)
- Acto administrativo: validez, nulidad, eficacia, revision
- Silencio administrativo (Ley 29060)
- Recursos administrativos (Arts. 218-228)
- Procedimiento sancionador (Arts. 245-257)
- Ley de Contrataciones del Estado (Ley 30225 y DL 1341)
- DL 1246 — Simplificacion administrativa
"""

ADMINISTRATIVO_EXT_ARTICLES = [
    # === TUO LPAG — PRINCIPIOS ===
    {
        "article": "LPAG-1",
        "section_path": "TUO LPAG DS 004-2019-JUS > Titulo Preliminar > Principios > Legalidad y debido procedimiento",
        "content": (
            "TUO de la Ley del Procedimiento Administrativo General (DS 004-2019-JUS, que aprueba el "
            "TUO de la Ley 27444).\n\n"
            "Principio de Legalidad (Art. IV.1.1): Las autoridades administrativas deben actuar con "
            "respeto a la Constitucion, la ley y al derecho, dentro de las facultades que le esten "
            "atribuidas y de acuerdo con los fines para los que les fueron conferidas.\n\n"
            "Principio del Debido Procedimiento (Art. IV.1.2): Los administrados gozan de los derechos "
            "y garantias implicitos al debido procedimiento administrativo, que comprende el derecho "
            "a exponer sus argumentos, a ofrecer y producir pruebas y a obtener una decision "
            "motivada y fundada en derecho. La institucion del debido procedimiento administrativo "
            "se rige por los principios del Derecho Administrativo. La regulacion propia del Derecho "
            "Procesal Civil es aplicable solo en cuanto sea compatible con el regimen administrativo."
        ),
    },
    {
        "article": "LPAG-2",
        "section_path": "TUO LPAG > Titulo Preliminar > Principios > Impulso de oficio, razonabilidad e imparcialidad",
        "content": (
            "Principios del procedimiento administrativo — TUO LPAG DS 004-2019-JUS.\n\n"
            "Principio de Impulso de Oficio (Art. IV.1.3): Las autoridades deben dirigir e impulsar "
            "de oficio el procedimiento y ordenar la realizacion o practica de los actos que resulten "
            "convenientes para el esclarecimiento y resolucion de las cuestiones necesarias.\n\n"
            "Principio de Razonabilidad (Art. IV.1.4): Las decisiones de la autoridad administrativa, "
            "cuando creen obligaciones, califiquen infracciones, impongan sanciones, o establezcan "
            "restricciones a los administrados, deben adaptarse dentro de los limites de la facultad "
            "atribuida y manteniendo la debida proporcion entre los medios a emplear y los fines "
            "publicos que deba tutelar, a fin de que respondan a lo estrictamente necesario para la "
            "satisfaccion de su cometido.\n\n"
            "Principio de Imparcialidad (Art. IV.1.5): Las autoridades administrativas actuan sin "
            "ningun tipo de discriminacion entre los administrados, otorgandoles tratamiento y tutela "
            "igualitarios frente al procedimiento, resolviendo conforme al ordenamiento juridico "
            "y con atencion al interes general."
        ),
    },
    {
        "article": "LPAG-3",
        "section_path": "TUO LPAG > Titulo Preliminar > Principios > Informalismo, presuncion veracidad, conducta procedimental",
        "content": (
            "Principios adicionales del procedimiento administrativo — TUO LPAG.\n\n"
            "Principio de Informalismo (Art. IV.1.6): Las normas de procedimiento deben ser "
            "interpretadas en forma favorable a la admision y decision final de las pretensiones "
            "de los administrados, de modo que sus derechos e intereses no sean afectados por la "
            "exigencia de aspectos formales que puedan ser subsanados dentro del procedimiento.\n\n"
            "Principio de Presuncion de Veracidad (Art. IV.1.7): En la tramitacion del procedimiento "
            "administrativo, se presume que los documentos y declaraciones formulados por los "
            "administrados en la forma prescrita responden a la verdad de los hechos que ellos afirman. "
            "Esta presuncion admite prueba en contrario.\n\n"
            "Principio de Buena Fe Procedimental (Art. IV.1.8): La autoridad administrativa, los "
            "administrados, sus representantes o abogados y, en general, todos los participes del "
            "procedimiento, realizan sus respectivos actos procedimentales guiados por el respeto "
            "mutuo, la colaboracion y la buena fe.\n\n"
            "Principio de Celeridad (Art. IV.1.9): Quienes participan en el procedimiento deben "
            "ajustar su actuacion de tal modo que se dote al tramite de la maxima dinamica posible."
        ),
    },
    # === ACTO ADMINISTRATIVO ===
    {
        "article": "LPAG-ACTO",
        "section_path": "TUO LPAG > Titulo I > Capitulo I > Acto Administrativo > Definicion y elementos",
        "content": (
            "Acto Administrativo — Definicion y elementos de validez (Arts. 1-3 TUO LPAG).\n\n"
            "Art. 1.1: Son actos administrativos, las declaraciones de las entidades que, en el "
            "marco de normas de derecho publico, estan destinadas a producir efectos juridicos "
            "sobre los intereses, obligaciones o derechos de los administrados dentro de una "
            "situacion concreta.\n\n"
            "NO SON ACTOS ADMINISTRATIVOS: Los actos de administracion interna, los "
            "comportamientos y actuaciones materiales, los actos normativos (reglamentos), ni los "
            "actos de simple constancia o certificacion.\n\n"
            "ELEMENTOS DE VALIDEZ del acto administrativo (Art. 3):\n"
            "1. Competencia: emitido por el organo con competencia legal para dictarlo.\n"
            "2. Objeto o contenido: licito, preciso, posible fisicamente y real.\n"
            "3. Finalidad publica: debe satisfacer el interes general.\n"
            "4. Motivacion: expresar en forma concisa las razones de hecho y de derecho que lo fundan.\n"
            "5. Procedimiento regular: respetando el procedimiento establecido en la ley.\n\n"
            "Todo acto administrativo se considera valido en tanto su pretendida nulidad no sea "
            "declarada por autoridad administrativa o jurisdiccional."
        ),
    },
    {
        "article": "LPAG-NULIDAD",
        "section_path": "TUO LPAG > Titulo I > Capitulo II > Nulidad del acto administrativo",
        "content": (
            "Nulidad del Acto Administrativo (Art. 10 TUO LPAG).\n\n"
            "Son vicios del acto administrativo que causan su NULIDAD DE PLENO DERECHO:\n\n"
            "1. La contravención a la Constitución, a las leyes o a las normas reglamentarias.\n"
            "2. El defecto o la omision de alguno de sus requisitos de validez, salvo que "
            "se presenten algunos de los supuestos de conservacion del acto.\n"
            "3. Los actos expresos o los que resulten como consecuencia de la aprobacion automatica "
            "o por silencio administrativo positivo, por los que se adquiere facultades, o derechos "
            "cuando son contrarios al ordenamiento juridico, o cuando no se cumplen los requisitos, "
            "documentacion o tramites esenciales para su adquisicion.\n"
            "4. Los actos administrativos que sean constitutivos de infraccion penal, o que se "
            "dicten como consecuencia de la misma.\n\n"
            "CONSERVACION DEL ACTO (Art. 14): Los vicios incurridos en la emision de un acto "
            "administrativo que no lo hagan nulo de pleno derecho pueden ser convalidados por la "
            "propia entidad emisora, subsanando los vicios que lo afecten.\n\n"
            "PRESCRIPCION DE LA ACCION DE NULIDAD DE OFICIO (Art. 213): Las entidades "
            "solo pueden declarar la nulidad de oficio dentro del plazo de dos anos contado desde la "
            "fecha en que el acto quedo firme."
        ),
    },
    {
        "article": "LPAG-EFICACIA",
        "section_path": "TUO LPAG > Titulo I > Capitulo III > Eficacia del acto > Notificacion",
        "content": (
            "Eficacia del Acto Administrativo y Notificacion (Arts. 16-26 TUO LPAG).\n\n"
            "Art. 16.1: El acto administrativo es eficaz a partir de que la notificacion "
            "legalmente realizada produce sus efectos. Regla general: retroactividad NO.\n\n"
            "FORMAS DE NOTIFICACION (Art. 20), en orden de preferencia:\n"
            "1. Notificacion personal al administrado o su representante legal (en domicilio).\n"
            "2. Mediante correo certificado, telegrama u otros medios que acrediten fehacientemente "
            "el acuse de recibo.\n"
            "3. Por publicacion en el Diario Oficial El Peruano (cuando no es posible personal o "
            "cuando el administrado es indeterminado).\n"
            "4. Notificacion electronica (cuando el administrado lo haya consentido expresamente).\n\n"
            "PLAZO DE NOTIFICACION: Las notificaciones deben realizarse dentro de los cinco dias "
            "habiles posteriores a la expedicion del acto.\n\n"
            "NOTIFICACION DEFECTUOSA (Art. 26): La notificacion que incumpla los requisitos "
            "no surte efecto. El interesado puede alegar la falta de notificacion para "
            "interponer recursos administrativos sin que haya prescrito el plazo."
        ),
    },
    # === SILENCIO ADMINISTRATIVO ===
    {
        "article": "SILENCIO-ADM",
        "section_path": "TUO LPAG > Titulo I > Silencio Administrativo > Ley 29060",
        "content": (
            "Silencio Administrativo (Arts. 35-37 TUO LPAG y Ley 29060).\n\n"
            "SILENCIO ADMINISTRATIVO POSITIVO:\n"
            "Si la entidad no resuelve dentro del plazo legal establecido, se entiende aprobada "
            "la solicitud del administrado. Opera como regla general para procedimientos de "
            "aprobacion automatica y para los procedimientos listados en el TUPA de cada entidad.\n\n"
            "Plazos: El plazo maximo para resolver procedimientos administrativos es de 30 dias "
            "habiles, salvo disposicion expresa en contrario.\n\n"
            "SILENCIO ADMINISTRATIVO NEGATIVO:\n"
            "Si la entidad no resuelve dentro del plazo, se entiende denegada la solicitud "
            "(ficcion de denegacion). Opera excepcionalmente cuando:\n"
            "a) La solicitud involucra recursos naturales, medio ambiente, bienes culturales.\n"
            "b) Afecta la salud o seguridad publica.\n"
            "c) Involucra actividades de gran impacto economico.\n\n"
            "EFECTOS DEL SILENCIO POSITIVO:\n"
            "- El administrado puede solicitar la Constancia de Silencio Positivo a la entidad.\n"
            "- La Contraloria General de la Republica puede dejar sin efecto el acto ficto "
            "si contravia normas legales.\n\n"
            "DL 1246 (2016): Simplifica procedimientos y amplia los casos de silencio positivo "
            "y declaraciones juradas en lugar de certificados y documentos."
        ),
    },
    # === RECURSOS ADMINISTRATIVOS ===
    {
        "article": "LPAG-RECURSOS",
        "section_path": "TUO LPAG > Capitulo III > Recursos Administrativos > Tipos y plazos",
        "content": (
            "Recursos Administrativos (Arts. 218-228 TUO LPAG).\n\n"
            "Los recursos administrativos son mecanismos de impugnacion de actos administrativos. "
            "La interposicion es voluntaria, salvo cuando la ley exija el agotamiento de la via "
            "administrativa como requisito previo para la via judicial.\n\n"
            "RECURSO DE RECONSIDERACION (Art. 208 renum.): Se interpone ante el mismo organo "
            "que dicto el primer acto. Requiere nueva prueba no presentada anteriormente. "
            "Plazo de interposicion: 15 dias habiles. Plazo para resolver: 30 dias habiles.\n\n"
            "RECURSO DE APELACION (Art. 209 renum.): Se interpone cuando la impugnacion se "
            "sustenta en diferente interpretacion de las pruebas producidas o cuando se trate de "
            "cuestiones de puro derecho. Se dirige al superior jerarquico. "
            "Plazo: 15 dias habiles. El superior tiene 30 dias para resolver.\n\n"
            "RECURSO DE REVISION (Art. 210 renum.): Procede cuando las entidades no se "
            "encuentran sometidas a subordinacion jerarquica respecto a la que expidio el acto. "
            "Se interpone ante el Ministro del sector correspondiente.\n\n"
            "AGOTAMIENTO DE LA VIA ADMINISTRATIVA: Se produce con la decision del "
            "recurso de apelacion (o reconsideracion cuando no hay apelacion). Luego procede "
            "la demanda contencioso-administrativa ante el Poder Judicial (Ley 27584)."
        ),
    },
    # === PROCEDIMIENTO SANCIONADOR ===
    {
        "article": "LPAG-SANCION",
        "section_path": "TUO LPAG > Capitulo II > Procedimiento Sancionador > Principios",
        "content": (
            "Procedimiento Administrativo Sancionador — Principios (Arts. 245-257 TUO LPAG).\n\n"
            "Principios del procedimiento sancionador:\n\n"
            "1. LEGALIDAD: Solo por norma con rango de ley puede atribuirse la potestad "
            "sancionadora a las entidades. La tipificacion de infracciones y sanciones requiere "
            "norma legal habilitante.\n\n"
            "2. TIPICIDAD: Solo constituyen conductas sancionables administrativamente las "
            "infracciones previstas expresamente en normas con rango de ley, sin admitir "
            "interpretacion extensiva o analogica.\n\n"
            "3. IRRETROACTIVIDAD: Son aplicables las disposiciones sancionadoras vigentes en el "
            "momento de incurrirse en la conducta a sancionar. Excepcion: retroactividad benigna.\n\n"
            "4. CONCURSO DE INFRACCIONES: Cuando una misma conducta califique como mas de una "
            "infraccion, se aplicara la sancion prevista para la infraccion de mayor gravedad.\n\n"
            "5. PRESUNCION DE LICITUD: Las entidades deben presumir que los administrados han "
            "actuado apegados a sus deberes mientras no cuenten con evidencia en contrario.\n\n"
            "6. CULPABILIDAD: La responsabilidad administrativa es subjetiva; exige dolo o culpa.\n\n"
            "7. NON BIS IN IDEM: No se puede imponer dos sanciones a la misma persona por los "
            "mismos hechos cuando exista identidad de sujeto, hecho y fundamento."
        ),
    },
    {
        "article": "LPAG-SANCION-PROC",
        "section_path": "TUO LPAG > Capitulo II > Procedimiento Sancionador > Etapas",
        "content": (
            "Etapas del Procedimiento Sancionador (Arts. 254-257 TUO LPAG).\n\n"
            "El procedimiento sancionador se sujeta a la separacion entre la fase instructora "
            "y la fase sancionadora:\n\n"
            "FASE INSTRUCTORA:\n"
            "1. Inicio de oficio por la autoridad instructora (puede ser por denuncia, control, "
            "inspeccion o de propia iniciativa).\n"
            "2. Notificacion de la imputacion de cargos al administrado: debe indicar los "
            "hechos imputados, norma infringida, sancion posible, nombre del instructor y "
            "organo sancionador.\n"
            "3. Plazo para descargos: no menor de 5 ni mayor de 15 dias habiles.\n"
            "4. Actuacion de pruebas.\n"
            "5. Informe final del instructor (propone sancion o archivo).\n\n"
            "FASE SANCIONADORA:\n"
            "6. El organo sancionador (distinto al instructor) emite resolucion dentro de 10 dias.\n"
            "7. Resolucion de sancion: debe contener hechos probados, norma infringida, "
            "sancion impuesta y motivacion.\n\n"
            "RECURSO CONTRA LA SANCION: Recurso de apelacion ante el superior jerarquico. "
            "La interposicion del recurso suspende la ejecucion de la sancion (salvo medida cautelar)."
        ),
    },
    # === PROCEDIMIENTO TRILATERAL ===
    {
        "article": "LPAG-TRILATERAL",
        "section_path": "TUO LPAG > Capitulo III > Procedimiento Trilateral",
        "content": (
            "Procedimiento Administrativo Trilateral (Arts. 219-229 TUO LPAG).\n\n"
            "El procedimiento trilateral es aquel iniciado por un administrado contra otro "
            "administrado ante una entidad administrativa. Se llama 'trilateral' porque "
            "intervienen tres partes: la entidad (que resuelve), el administrado reclamante "
            "y el administrado reclamado.\n\n"
            "Caracteristicas:\n"
            "1. La entidad actua como arbitro o juez administrativo entre privados.\n"
            "2. Se aplican los principios del debido proceso: contradiccion, prueba, motivacion.\n"
            "3. La carga de la prueba corresponde al reclamante, salvo que la entidad tenga "
            "poderes investigatorios.\n\n"
            "Ejemplos tipicos de procedimientos trilaterales en el Peru:\n"
            "- Procedimientos ante INDECOPI (proteccion al consumidor, competencia desleal)\n"
            "- Procedimientos ante OSIPTEL, OSINERGMIN, SUNASS, OSITRAN (quejas entre usuarios "
            "y empresas reguladas)\n"
            "- Procedimientos ante OSCE (controversias en contratos estatales)\n"
            "- Procedimientos ante SUNARP (oposicion a inscripciones)\n\n"
            "La resolucion que pone fin al procedimiento trilateral es impugnable en via "
            "administrativa y luego en via judicial."
        ),
    },
    # === CONTRATACIONES DEL ESTADO ===
    {
        "article": "LCE-PRINCIPIOS",
        "section_path": "Ley 30225 > Ley de Contrataciones del Estado > Principios y ambito",
        "content": (
            "Ley de Contrataciones del Estado (Ley 30225, modificada por DL 1341 y DL 1444) "
            "y su Reglamento (DS 344-2018-EF, modificado por DS 162-2021-EF).\n\n"
            "Principios que rigen las contrataciones publicas (Art. 2 Ley 30225):\n"
            "1. Libertad de concurrencia: promover la mayor cantidad de postores.\n"
            "2. Igualdad de trato: igualdad de condiciones entre postores.\n"
            "3. Transparencia: informacion accesible al publico.\n"
            "4. Publicidad: difusion de los procesos de seleccion.\n"
            "5. Competencia: fomentar la libre competencia entre postores.\n"
            "6. Eficacia y eficiencia: mejores resultados con menor costo.\n"
            "7. Vigencia tecnologica: adoptar tecnologia adecuada.\n"
            "8. Sostenibilidad ambiental y social.\n"
            "9. Equidad: trato justo entre partes.\n"
            "10. Integridad: conducta honesta de los participantes.\n\n"
            "AMBITO DE APLICACION: Aplica a todas las entidades del Poder Ejecutivo, "
            "Legislativo, Judicial, organismos autonomos, gobiernos regionales y locales, "
            "empresas del Estado. Se utiliza el SEACE (Sistema Electronico de Contrataciones "
            "del Estado) para publicar todos los procesos."
        ),
    },
    {
        "article": "LCE-PROCESOS",
        "section_path": "Ley 30225 > Procesos de Seleccion > Tipos y umbrales",
        "content": (
            "Procesos de Seleccion — Ley de Contrataciones del Estado.\n\n"
            "Los tipos de proceso de seleccion (Art. 21 Ley 30225 y Reglamento) dependen del "
            "objeto y valor estimado de la contratacion. Para el 2024:\n\n"
            "LICITACION PUBLICA: Para obras y bienes superiores a 400 UIT (aprox. S/ 2,060,000). "
            "Proceso mas riguroso y con mayor publicidad.\n\n"
            "CONCURSO PUBLICO: Para servicios superiores a 400 UIT.\n\n"
            "ADJUDICACION SIMPLIFICADA: Para bienes, servicios y obras entre 8 y 400 UIT.\n\n"
            "SUBASTA INVERSA ELECTRONICA: Para bienes y servicios en el Listado de Bienes y "
            "Servicios Comunes (fichas tecnicas). El postor que ofrezca el menor precio gana.\n\n"
            "SELECCION DE CONSULTORES INDIVIDUALES: Para consultores personas naturales (sin equipo).\n\n"
            "COMPARACION DE PRECIOS: Para bienes y servicios disponibles en el mercado, hasta 15 UIT.\n\n"
            "CONTRATACION DIRECTA: En los casos previstos en la ley (emergencia, exclusividad, "
            "secreto, etc.). Requiere aprobacion del Titular de la Entidad.\n\n"
            "ACUERDO MARCO: El OSCE licita y establece un catalogo de proveedores pre-calificados "
            "de los que las entidades pueden contratar directamente."
        ),
    },
    {
        "article": "LCE-CONTRATOS",
        "section_path": "Ley 30225 > Contratos > Suscripcion, penalidades y resolucion",
        "content": (
            "Contratos en la Ley de Contrataciones del Estado (Arts. 32-46 Ley 30225).\n\n"
            "SUSCRIPCION DEL CONTRATO:\n"
            "Tras la buena pro, el postor ganador suscribe el contrato con la entidad. Plazos:\n"
            "- El postor ganador presenta documentos en un plazo de 3-5 dias habiles.\n"
            "- La entidad suscribe el contrato dentro de los 8 dias habiles siguientes.\n\n"
            "GARANTIAS:\n"
            "- Garantia de fiel cumplimiento: 10% del monto contractual. Carta fianza bancaria.\n"
            "- Garantia por adelanto: cuando se otorga adelanto directo o de materiales.\n\n"
            "ADICIONALES Y REDUCCIONES: Hasta el 25% del monto del contrato original, "
            "con aprobacion del Titular de la Entidad y cuando sea indispensable.\n\n"
            "PENALIDADES:\n"
            "- Por mora: 0.10% del contrato por dia de atraso, hasta un tope del 10%.\n"
            "- Otras penalidades: tipificadas en los documentos de los procedimientos.\n\n"
            "RESOLUCION DEL CONTRATO:\n"
            "Puede ser por incumplimiento del contratista (si penalidades superan 10%), por "
            "caso fortuito, fuerza mayor, o por mutuo acuerdo.\n\n"
            "El TRIBUNAL DE CONTRATACIONES DEL ESTADO (adscrito al OSCE) resuelve las "
            "controversias derivadas de los contratos. Sus resoluciones son de ultima instancia "
            "administrativa y solo impugnables en via judicial."
        ),
    },
    {
        "article": "LCE-TRIBUNAL",
        "section_path": "Ley 30225 > OSCE > Tribunal de Contrataciones del Estado",
        "content": (
            "Organismo Supervisor de las Contrataciones del Estado (OSCE) y Tribunal de "
            "Contrataciones del Estado.\n\n"
            "El OSCE es el organismo tecnico especializado encargado de promover el cumplimiento "
            "de la normativa de contrataciones del Estado. Es adscrito al MEF.\n\n"
            "Funciones del OSCE:\n"
            "- Supervisar los procesos de contratacion\n"
            "- Gestionar el SEACE (Sistema Electronico de Contrataciones)\n"
            "- Registrar proveedores en el Registro Nacional de Proveedores (RNP)\n"
            "- Emitir directivas, circulares y opiniones legales\n"
            "- Capacitar a los funcionarios publicos en contrataciones\n\n"
            "TRIBUNAL DE CONTRATACIONES DEL ESTADO:\n"
            "Es el organo resolutivo del OSCE. Conoce:\n"
            "- Recursos de apelacion contra actos del proceso de seleccion (cuando el valor "
            "supera 50 UIT; los inferiores se apelan ante la propia entidad).\n"
            "- Procedimientos administrativos sancionadores contra proveedores y funcionarios.\n\n"
            "SANCIONES DEL TRIBUNAL:\n"
            "- Inhabilitacion temporal para contratar con el Estado (1 a 36 meses)\n"
            "- Inhabilitacion definitiva (en casos graves)\n"
            "- Multas (hasta 50 UIT)"
        ),
    },
    {
        "article": "DL1246-SIMPLIF",
        "section_path": "DL 1246 > Simplificacion Administrativa",
        "content": (
            "Decreto Legislativo 1246 — Aprueban diversas medidas de simplificacion administrativa "
            "(publicado el 10 de noviembre de 2016).\n\n"
            "Medidas principales de simplificacion:\n\n"
            "1. PROHIBICION DE REQUERIR DOCUMENTOS A CIUDADANOS que la entidad puede "
            "obtener por sus propios medios o de otras entidades. Las entidades del Estado "
            "deben compartir informacion entre si sin cargar al ciudadano.\n\n"
            "2. INTEROPERABILIDAD: Las entidades deben implementar plataformas tecnologicas "
            "para el intercambio de informacion (Plataforma de Interoperabilidad del Estado - PIDE).\n\n"
            "3. DECLARACIONES JURADAS: Sustituyen a documentos que acreditan hechos conocidos "
            "por el ciudadano, bajo responsabilidad. La administracion puede verificar posteriormente.\n\n"
            "4. SILENCIO ADMINISTRATIVO POSITIVO: Se amplia a nuevos procedimientos.\n\n"
            "5. COSTOS DE TRAMITES: Los TUPA deben actualizarse para reducir costos. Solo "
            "se puede cobrar el costo real del servicio administrativo.\n\n"
            "6. PLATAFORMA DE TRAMITES: El Estado debe habilitar tramites en linea.\n\n"
            "El incumplimiento de las medidas de simplificacion puede ser sancionado por la "
            "Secretaria de Gestion Publica de la PCM."
        ),
    },
    {
        "article": "EJECUCION-FORZOSA",
        "section_path": "TUO LPAG > Titulo I > Capitulo IV > Ejecucion Forzosa del acto administrativo",
        "content": (
            "Ejecucion Forzosa del Acto Administrativo (Arts. 191-199 TUO LPAG).\n\n"
            "Cuando el obligado no cumple voluntariamente un acto administrativo firme, "
            "la entidad puede ejecutarlo coactivamente por los siguientes medios:\n\n"
            "1. EJECUCION COACTIVA (Ley 26979 — Ley de Procedimiento de Ejecucion Coactiva):\n"
            "   Aplica para la cobranza de obligaciones tributarias, multas y creditos de "
            "   derecho publico. El Ejecutor Coactivo traba embargos sobre bienes del obligado.\n"
            "   Medidas de embargo: en forma de intervencion en recaudacion, deposito, "
            "   inscripcion o retencion.\n\n"
            "2. EJECUCION SUBSIDIARIA: La entidad realiza el acto por cuenta del obligado "
            "   y le cobra los gastos incurridos.\n\n"
            "3. MULTA COERCITIVA: Se impone multa por cada dia de incumplimiento hasta "
            "   que el obligado cumpla (diferente de la sancion por infraccion).\n\n"
            "4. COMPULSION SOBRE LAS PERSONAS: Solo para obligaciones de dar (restituir "
            "   bienes), sujeta a la autorizacion judicial cuando implique afectacion de "
            "   derechos fundamentales.\n\n"
            "Las medidas de ejecucion se adoptaran observando el principio de proporcionalidad "
            "y sin crear mayores trabas que las necesarias para el cumplimiento."
        ),
    },
    {
        "article": "LPAG-QUEJA",
        "section_path": "TUO LPAG > Queja > Art. 158 > Recurso de queja",
        "content": (
            "Recurso de Queja (Art. 158 TUO LPAG).\n\n"
            "Art. 158: El recurso de queja se interpone contra los defectos de tramitacion "
            "y, en especial, los que supongan paralización del procedimiento, infracciones de "
            "los plazos establecidos legalmente, omision de tramites que deben ser cumplidos "
            "o insistencia en la expedicion de actos administrativos ya anulados por el superior.\n\n"
            "CARACTERISTICAS:\n"
            "- Se interpone ante el superior jerarquico del que incurre en el defecto.\n"
            "- NO suspende el procedimiento principal.\n"
            "- Debe ser resuelta en 3 dias habiles.\n"
            "- No se requiere el agotamiento de la via administrativa para interponerla.\n\n"
            "DIFERENCIA CON OTROS RECURSOS:\n"
            "La queja NO es un recurso impugnatorio (no ataca el fondo de la decision), sino "
            "un mecanismo de control del procedimiento. Busca corregir irregularidades de "
            "tramite, no revocar un acto administrativo.\n\n"
            "RESPONSABILIDAD: Si la queja se declara fundada, la autoridad superior puede "
            "imponer medidas correctivas y reportar al funcionario infractor para efecto de "
            "responsabilidad administrativa (Ley del Servicio Civil, Ley 30057)."
        ),
    },
    {
        "article": "LPAG-ACCESORIEDADES",
        "section_path": "TUO LPAG > Principio de informalismo > Subsanacion y conservacion",
        "content": (
            "Subsanacion, Convalidacion y Conservacion del Acto Administrativo (Arts. 11-14 TUO LPAG).\n\n"
            "SUBSANACION DE VICIOS (Art. 11):\n"
            "Los vicios incurridos en la emision del acto que no lo hagan nulo de pleno derecho "
            "pueden ser convalidados por la propia entidad emisora. La convalidacion retroactua "
            "a la fecha del acto convalidado.\n\n"
            "CONSERVACION (Art. 14): Los actos administrativos afectados por vicios no "
            "esenciales se conservan. Son vicios no esenciales los que no afectan el fondo "
            "de la decision: error en la mencion del organo emisor, motivacion incompleta "
            "cuando el administrado conoce las razones.\n\n"
            "CONVERSION (Art. 12): El acto nulo puede ser convertido si contiene los requisitos "
            "de otro acto diferente valido.\n\n"
            "TEORIA DE CONSERVACION: Favorece la estabilidad de los actos administrativos "
            "cuando su anulacion causaria mayor perjuicio al interes publico que su conservacion. "
            "Es compatible con el principio de seguridad juridica y el principio de informalismo.\n\n"
            "En la practica administrativa peruana, este principio se aplica frecuentemente en "
            "la convalidacion de actos de nombramiento o designacion de funcionarios que "
            "adolecen de vicios formales pero cuya invalidacion causaria caos institucional."
        ),
    },
    {
        "article": "CONTRATO-ADMON",
        "section_path": "Derecho Administrativo > Contratos administrativos > Caracteres y potestades",
        "content": (
            "Contratos Administrativos — Caracteres y Potestades Exorbitantes.\n\n"
            "El contrato administrativo es el acuerdo de voluntades entre una entidad publica "
            "y un particular para satisfacer un interes publico. Se diferencia del contrato "
            "civil por las potestades exorbitantes que tiene la Administracion:\n\n"
            "1. PODER DE DIRECCION Y CONTROL: La entidad puede impartir instrucciones al "
            "   contratista sobre la ejecucion del contrato sin necesidad de acudir al juez.\n\n"
            "2. PODER DE MODIFICACION UNILATERAL (ius variandi): En la Ley de Contrataciones "
            "   del Estado, la entidad puede modificar unilateralmente el contrato hasta el "
            "   25% del monto, con compensacion economica al contratista.\n\n"
            "3. PODER DE RESOLUCION UNILATERAL: La entidad puede resolver el contrato por "
            "   incumplimiento del contratista, con penalidades.\n\n"
            "4. EJECUTORIEDAD: Las decisiones de la entidad sobre el contrato se ejecutan "
            "   sin necesidad de acudir al Poder Judicial.\n\n"
            "5. PODER SANCIONADOR: La entidad puede aplicar penalidades sin necesidad de "
            "   resolucion judicial previa.\n\n"
            "El equilibrio del contratista se mantiene mediante la compensacion economica "
            "por modificaciones unilaterales (teoria del hecho del principe), el arbitraje "
            "como mecanismo de solucion de controversias y el principio de intangibilidad "
            "de la ecuacion economica-financiera del contrato."
        ),
    },
    {
        "article": "SERVICIO-CIVIL",
        "section_path": "Ley 30057 > Servicio Civil > Carrera administrativa",
        "content": (
            "Ley del Servicio Civil — Ley 30057 (2013) y Reglamento DS 040-2014-PCM.\n\n"
            "La Ley Servir crea un regimen unico para los servidores civiles del Estado "
            "peruano, con el objetivo de mejorar el desempeno de las entidades publicas.\n\n"
            "GRUPOS DEL SERVICIO CIVIL:\n"
            "1. Funcionarios publicos: ministros, viceministros, titulares de organismos, etc.\n"
            "2. Directivos publicos: gerentes generales, directores de linea.\n"
            "3. Servidores civiles de carrera: el grueso de los servidores.\n"
            "4. Servidores de actividades complementarias: limpieza, seguridad, conductores.\n"
            "5. Servidores bajo regimenes especiales: docentes, medicos, FFAA, PNP.\n\n"
            "PAD — Procedimiento Administrativo Disciplinario (Arts. 91-107 Ley 30057):\n"
            "Las faltas disciplinarias se sancionan con: amonestacion escrita, suspension "
            "sin goce de remuneraciones (1-12 meses), terminacion de la relacion de trabajo.\n\n"
            "TRIBUNAL DEL SERVICIO CIVIL (SERVIR): Resuelve las impugnaciones de los "
            "servidores civiles en segunda instancia. Es la ultima instancia administrativa. "
            "Luego procede demanda contencioso-administrativa.\n\n"
            "AUTORIDAD NACIONAL DEL SERVICIO CIVIL (SERVIR): Organismo tecnico especializado "
            "que ejerce la rectoria del sistema de gestion de recursos humanos del Estado."
        ),
    },
    {
        "article": "RESPONSABILIDAD-ESTADO",
        "section_path": "Derecho Administrativo > Responsabilidad del Estado > Bases constitucionales",
        "content": (
            "Responsabilidad del Estado por Actos Administrativos (Arts. 238-239 TUO LPAG).\n\n"
            "Art. 238: Sin perjuicio de las responsabilidades previstas en el derecho comun y "
            "en las leyes especiales, las entidades son patrimonialmente responsables frente a "
            "los administrados por los danos directos e inmediatos causados por los actos de la "
            "administracion o los servicios publicos directamente prestados por aquellas.\n\n"
            "REQUISITOS PARA LA RESPONSABILIDAD:\n"
            "1. Actuacion de la Administracion (accion u omision).\n"
            "2. Dano real y efectivo al administrado.\n"
            "3. Nexo causal entre la actuacion y el dano.\n\n"
            "INDEMNIZACION:\n"
            "La entidad debe indemnizar los danos causados. La responsabilidad puede ser:\n"
            "- Por funcionamiento normal del servicio (danos causados por actividad licita).\n"
            "- Por funcionamiento anormal (errores, negligencia, arbitrariedad).\n\n"
            "RESPONSABILIDAD DEL FUNCIONARIO (Art. 239): La entidad puede repetir contra "
            "el funcionario que actuó con dolo, culpa inexcusable o culpa leve causando dano.\n\n"
            "VIA PARA RECLAMAR: Proceso contencioso-administrativo ante el Poder Judicial "
            "(Ley 27584). El plazo de prescripcion es de 3 anos."
        ),
    },
    {
        "article": "REGIMEN-CONCESION",
        "section_path": "Derecho Administrativo > Concesiones > DL 757 y servicios publicos",
        "content": (
            "Concesiones Administrativas y Contratos de Concesion en Peru.\n\n"
            "La concesion administrativa es el acto juridico mediante el cual el Estado "
            "otorga a un particular el derecho a prestar un servicio publico o explotar "
            "un bien de dominio publico, por un plazo determinado y bajo ciertas condiciones.\n\n"
            "MARCO NORMATIVO:\n"
            "- DL 757 — Marco para el Crecimiento de la Inversion Privada (1991).\n"
            "- DL 839 — Marco para la Promocion de la Inversion Privada en obras de "
            "  Infraestructura y de Servicios Publicos (reemplazado por DL 1362 — OPIC).\n"
            "- DL 1362 — Ley que regula la Promocion de la Inversion Privada mediante APP "
            "  y Proyectos en Activos.\n\n"
            "ASOCIACIONES PUBLICO-PRIVADAS (APP):\n"
            "Las APP son modalidades de participacion de la inversion privada en proyectos de "
            "infraestructura y servicios publicos donde se distribuyen riesgos entre el Estado "
            "y el privado. Tipos:\n"
            "- APP autofinanciadas: se recuperan con tarifas del proyecto.\n"
            "- APP cofinanciadas: requieren recursos publicos.\n\n"
            "ProInversion es el organismo promotor de inversiones privadas en el Peru. "
            "Supervisa los procesos de concesion y los contratos de concesion suscritos."
        ),
    },
]
