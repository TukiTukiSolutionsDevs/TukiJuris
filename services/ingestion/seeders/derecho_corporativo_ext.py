"""
Seed: Derecho Corporativo — Expansion de conocimiento societario y empresarial peruano.

Normas cubiertas:
- Ley General de Sociedades (Ley 26887):
  - Tipos societarios: SA, SAC, SAA, SRL, colectiva, comandita
  - Constitucion: escritura publica, inscripcion, capital social
  - Organos sociales: JGA, directorio, gerencia
  - Acciones: transferencia, suscripcion preferente
  - Modificacion de estatuto, aumento y reduccion de capital
  - Disolucion, liquidacion
  - Reorganizacion: fusion, escision, transformacion
- Ley MYPE (Ley 28015 y DL 1086)
- Codigo de Comercio (normas vigentes)
"""

CORPORATIVO_EXT_ARTICLES = [
    # === LEY GENERAL DE SOCIEDADES ===
    {
        "article": "LGS-1",
        "section_path": "Ley 26887 > LGS > Titulo I > Reglas aplicables a todas las sociedades",
        "content": (
            "Ley General de Sociedades — Ley 26887 (vigente desde el 1 de enero de 1998, "
            "modificada por diversas leyes incluyendo DL 1061, Ley 29874, entre otras).\n\n"
            "Art. 1: Toda sociedad debe adoptar alguna de las formas previstas en esta Ley. "
            "Las sociedades extranjeras de cualquier tipo tienen existencia legal en el Peru.\n\n"
            "Art. 2: Las personas que actuan en nombre de la sociedad antes de su inscripcion "
            "en el Registro responden solidariamente frente a terceros.\n\n"
            "Tipos de sociedades regulados en la LGS:\n"
            "1. Sociedad Anonima (SA) — Seccion Segunda\n"
            "   - Sociedad Anonima Cerrada (SAC) — Seccion Cuarta\n"
            "   - Sociedad Anonima Abierta (SAA) — Seccion Quinta\n"
            "2. Sociedad Comercial de Responsabilidad Limitada (SRL) — Seccion Septima\n"
            "3. Sociedad Colectiva — Seccion Primera\n"
            "4. Sociedad en Comandita Simple — Seccion Segunda del Libro Cuarto\n"
            "5. Sociedad en Comandita por Acciones\n"
            "6. Sociedad Civil (ordinaria y de responsabilidad limitada) — Libro Quinto\n\n"
            "La forma mas utilizada en Peru es la SAC (para empresas pequenas y medianas) "
            "y la SA (para empresas que requieren estructura mas compleja o acceso a mercado)."
        ),
    },
    {
        "article": "LGS-CONSTITUCION",
        "section_path": "Ley 26887 > LGS > Titulo I > Constitucion > Escritura publica y estatuto",
        "content": (
            "Constitucion de Sociedades (Arts. 5-10 LGS).\n\n"
            "Art. 5: La sociedad se constituye por escritura publica, en la que se inserta el "
            "pacto social con los estatutos. Para la validez del acto constitutivo se requiere:\n"
            "- La declaracion de voluntad de los socios fundadores.\n"
            "- La suscripcion de todas las acciones o participaciones.\n"
            "- El pago de al menos el 25% del valor de cada accion (para SA) o el pago "
            "  integro en SRL.\n\n"
            "CONTENIDO DEL ESTATUTO (Art. 55 para SA):\n"
            "1. Denominacion social\n"
            "2. Descripcion del objeto social\n"
            "3. Domicilio social\n"
            "4. Plazo de duracion (determinado o indeterminado)\n"
            "5. Monto del capital social y numero de acciones\n"
            "6. Regimen de los organos de la sociedad\n"
            "7. Requisitos para acordar modificacion del estatuto\n"
            "8. Normas para la distribucion de utilidades\n"
            "9. Regimen para la disolucion y liquidacion\n\n"
            "La escritura publica se eleva ante Notario y se presenta al Registro de Personas "
            "Juridicas de SUNARP para su inscripcion. La sociedad adquiere personalidad "
            "juridica desde su inscripcion registral."
        ),
    },
    {
        "article": "LGS-JGA",
        "section_path": "Ley 26887 > LGS > SA > Junta General de Accionistas",
        "content": (
            "Junta General de Accionistas (Arts. 111-140 LGS).\n\n"
            "Art. 111: La junta general es el organo supremo de la sociedad. Los accionistas "
            "constituidos en junta general debidamente convocada, y con el quorum correspondiente, "
            "deciden por la mayoria que establece la Ley los asuntos propios de su competencia.\n\n"
            "TIPOS DE JUNTA:\n"
            "- JUNTA OBLIGATORIA ANUAL (Art. 114): Se realiza dentro de los 3 meses siguientes "
            "al cierre del ejercicio. Agenda obligatoria: memoria del directorio, estados "
            "financieros, distribucion de utilidades, eleccion del directorio y revisores.\n"
            "- JUNTA ESPECIAL (Art. 116): Para acuerdos que afecten solo a una clase de acciones.\n\n"
            "CONVOCATORIA (Art. 116): Por el directorio (y la gerencia si lo prevee el estatuto) "
            "con una anticipacion minima de 10 dias para SA y 3 dias para SAC. Se publica en "
            "el Diario Oficial El Peruano y en un diario de circulacion.\n\n"
            "QUORUM:\n"
            "- Primera convocatoria: accionistas que representen al menos el 50% del capital "
            "  suscrito con derecho a voto.\n"
            "- Segunda convocatoria: cualquier numero de acciones.\n"
            "- Quorum calificado (para modificacion de estatutos, fusion, etc.): 2/3 partes.\n\n"
            "MAYORIA: La mayoria absoluta del capital suscrito con derecho a voto presente "
            "(mayoria simple de los presentes), salvo mayoria calificada para ciertos acuerdos."
        ),
    },
    {
        "article": "LGS-DIRECTORIO",
        "section_path": "Ley 26887 > LGS > SA > Directorio y Gerencia",
        "content": (
            "Directorio y Gerencia (Arts. 153-195 LGS).\n\n"
            "DIRECTORIO (Arts. 153-172):\n"
            "Art. 153: El directorio es el organo colegiado elegido por la junta general. "
            "Esta investido de las facultades de gestion y de representacion legal necesarias "
            "para la administracion de la sociedad.\n\n"
            "Caracteristicas del directorio:\n"
            "- Numero minimo de directores: 3 (para SA ordinaria), puede ser 1 en SAC.\n"
            "- Los directores pueden ser accionistas o terceros.\n"
            "- Duracion: segun estatuto (maxima 3 anos, con posibilidad de reeleccion).\n"
            "- Los directores tienen responsabilidad personal y solidaria frente a la sociedad, "
            "  accionistas y terceros por los dahos causados por acuerdos o actos contrarios a "
            "  la ley o al estatuto.\n\n"
            "GERENCIA (Arts. 175-195):\n"
            "Art. 175: La sociedad cuenta con uno o mas gerentes designados por el directorio. "
            "Si el estatuto lo permite, la junta puede designar al gerente general.\n\n"
            "El gerente general tiene las facultades de representacion legal de la sociedad. "
            "Puede celebrar contratos, contratar personal, abrir cuentas bancarias, entre otros. "
            "Responde frente a la sociedad, accionistas y terceros por los danos que cause "
            "por el incumplimiento de sus obligaciones, dolo, abuso de facultades o negligencia grave."
        ),
    },
    {
        "article": "LGS-ACCIONES",
        "section_path": "Ley 26887 > LGS > SA > Acciones > Tipos y transferencia",
        "content": (
            "Acciones y Participaciones Sociales (Arts. 82-107 LGS).\n\n"
            "Art. 82: Las acciones representan partes alicuotas del capital social. Todas las "
            "acciones tienen el mismo valor nominal y dan derecho a un voto, salvo estipulacion "
            "diferente del estatuto.\n\n"
            "TIPOS DE ACCIONES (Art. 88):\n"
            "- Acciones comunes: con derecho a voto y participacion en utilidades.\n"
            "- Acciones preferentes: pueden carecer de voto pero tienen preferencia en el pago "
            "  de dividendos y en la cuota de liquidacion.\n\n"
            "TRANSFERENCIA DE ACCIONES (SA):\n"
            "En la SA ordinaria, las acciones son libremente transferibles salvo restriccion "
            "estatutaria (clausulas de prevencion, preferencia o consentimiento).\n\n"
            "DERECHO DE SUSCRIPCION PREFERENTE (Art. 95): Ante un aumento de capital, los "
            "accionistas existentes tienen derecho preferente a suscribir nuevas acciones en "
            "proporcion a su participacion actual. Plazo para ejercer: no menor de 10 dias.\n\n"
            "SAC — RESTRICCIONES A LA TRANSFERENCIA (Art. 237 LGS): El estatuto puede "
            "establecer que las transferencias de acciones requieran consentimiento de la junta "
            "o del directorio. El plazo maximo para dar o negar el consentimiento es 30 dias, "
            "tras los cuales se presume aprobado. La sociedad no puede tener mas de 20 accionistas."
        ),
    },
    {
        "article": "LGS-CAPITAL",
        "section_path": "Ley 26887 > LGS > SA > Capital social > Aumento y reduccion",
        "content": (
            "Capital Social — Aumento y Reduccion (Arts. 201-219 LGS).\n\n"
            "AUMENTO DE CAPITAL (Art. 201):\n"
            "El aumento del capital se acuerda por la junta general con los requisitos del "
            "estatuto y puede realizarse por:\n"
            "1. Nuevos aportes (en efectivo o en especie).\n"
            "2. Capitalizacion de creditos contra la sociedad.\n"
            "3. Capitalizacion de utilidades, reservas, beneficios o primas de capital.\n"
            "4. Los demas casos que permita la ley.\n\n"
            "El aumento por nuevos aportes requiere el ejercicio del derecho de suscripcion "
            "preferente de los accionistas existentes (Art. 208 LGS).\n\n"
            "REDUCCION DE CAPITAL (Art. 215):\n"
            "Se acuerda por junta general con quorum y mayoria calificados. Puede realizarse por:\n"
            "1. Amortizacion de acciones (recompra y cancelacion).\n"
            "2. Disminucion del valor nominal de las acciones.\n"
            "3. Reduccion para absorber perdidas.\n\n"
            "CREDITO A ACREEDORES: Ante una reduccion de capital con devolucion a accionistas, "
            "los acreedores pueden oponerse si sus creditos son anteriores a la reduccion y no "
            "estan debidamente garantizados. El plazo para oponerse es 30 dias desde la "
            "publicacion del acuerdo."
        ),
    },
    {
        "article": "LGS-REORGANIZACION",
        "section_path": "Ley 26887 > LGS > Reorganizacion > Fusion, escision y transformacion",
        "content": (
            "Reorganizacion de Sociedades — Fusion, Escision y Transformacion (Arts. 333-413 LGS).\n\n"
            "FUSION (Arts. 344-359 LGS):\n"
            "Art. 344: Por la fusion dos o mas sociedades se integran para formar una sola "
            "cumpliendo los requisitos prescritos por la Ley.\n\n"
            "Modalidades:\n"
            "- FUSION POR ABSORCION: Una sociedad existente absorbe a otra(s) que se disuelven "
            "  sin liquidarse. La absorbente aumenta su capital.\n"
            "- FUSION POR INCORPORACION: Varias sociedades se disuelven para crear una nueva.\n\n"
            "ESCISION (Arts. 367-397 LGS):\n"
            "Art. 367: Por la escision una sociedad fracciona su patrimonio en dos o mas partes.\n"
            "Modalidades:\n"
            "- ESCISION TOTAL: La sociedad se divide en dos o mas partes que se transfieren a "
            "  sociedades beneficiarias. La escindida se disuelve.\n"
            "- ESCISION PARCIAL: La sociedad transfiere uno o mas bloques patrimoniales a "
            "  otras sociedades, sin disolverse.\n\n"
            "TRANSFORMACION (Arts. 333-343 LGS):\n"
            "Art. 333: La sociedad puede transformarse en otro tipo societario (ej. SA a SRL). "
            "No se disuelve ni crea nueva persona juridica, solo cambia de forma. Los socios "
            "mantienen sus derechos proporcionales."
        ),
    },
    {
        "article": "LGS-DISOLUCION",
        "section_path": "Ley 26887 > LGS > Disolucion y Liquidacion",
        "content": (
            "Disolucion y Liquidacion de Sociedades (Arts. 407-432 LGS).\n\n"
            "CAUSALES DE DISOLUCION (Art. 407):\n"
            "1. Vencimiento del plazo de duracion.\n"
            "2. Conclusion de su objeto social.\n"
            "3. Continuada inactividad de la junta general.\n"
            "4. Perdidas que reduzcan el patrimonio neto a menos de la tercera parte del capital pagado.\n"
            "5. Acuerdo de la junta de acreedores (quiebra) o decision de la junta.\n"
            "6. Falta de pluralidad de socios (si no se supera en 6 meses).\n"
            "7. Resolucion adoptada por la Corte Suprema.\n"
            "8. Acuerdo de la junta general.\n\n"
            "PROCESO DE LIQUIDACION (Arts. 413-432):\n"
            "1. La junta aprueba la disolucion y designa a los liquidadores.\n"
            "2. Se publican los acuerdos y se da plazo a acreedores para presentar creditos.\n"
            "3. Los liquidadores realizan los activos, pagan las deudas y distribuyen el remanente.\n"
            "4. Se aprueban los estados finales de liquidacion.\n"
            "5. Se inscribe la extincion de la sociedad en el Registro.\n\n"
            "QUIEBRA: Si las deudas superan el patrimonio, los liquidadores deben solicitar "
            "la declaracion de insolvencia ante INDECOPI (Ley General del Sistema Concursal, "
            "Ley 27809)."
        ),
    },
    {
        "article": "LGS-SRL",
        "section_path": "Ley 26887 > LGS > SRL > Sociedad de Responsabilidad Limitada",
        "content": (
            "Sociedad Comercial de Responsabilidad Limitada (SRL) — Seccion Septima LGS.\n\n"
            "Art. 283: En la SRL el capital esta dividido en participaciones iguales, acumulables "
            "e indivisibles, que no pueden ser incorporadas en titulos valores, ni denominarse "
            "acciones. Los socios no pueden exceder de veinte.\n\n"
            "Caracteristicas principales:\n"
            "- La responsabilidad de los socios se limita al monto de sus aportes.\n"
            "- No puede emitir acciones ni cotizar en bolsa.\n"
            "- Numero minimo de socios: 2; maximo: 20.\n"
            "- No tiene directorio obligatorio (a diferencia de la SA).\n"
            "- El organo de administracion es el Gerente (o la Junta de Socios en aspectos "
            "  relevantes).\n\n"
            "TRANSFERENCIA DE PARTICIPACIONES (Art. 291):\n"
            "Las participaciones son transferibles, pero el estatuto puede limitar la "
            "transferencia. Ante transferencia a terceros ajenos a la sociedad, los socios "
            "tienen derecho de adquisicion preferente. El procedimiento previsto en la ley "
            "garantiza que la sociedad o los socios tengan preferencia sobre terceros.\n\n"
            "JUNTA DE SOCIOS: Es el organo supremo. Se reune al menos una vez al ano para "
            "aprobar la gestion y cuentas del ejercicio anterior. Los acuerdos se toman "
            "por mayoria de participaciones (salvo quorum especial para ciertos acuerdos)."
        ),
    },
    {
        "article": "MYPE-LEY",
        "section_path": "Ley 28015 > MYPE > Definicion y categorias",
        "content": (
            "Ley MYPE — Regimen de la Micro y Pequena Empresa.\n"
            "Ley 28015 (Ley de Promocion y Formalizacion de la Micro y Pequena Empresa, 2003) "
            "y DL 1086 (Decreto Legislativo que aprueba la Ley de Promocion de la Competitividad, "
            "Formalizacion y Desarrollo de la MYPE, 2008).\n\n"
            "Definiciones segun ventas anuales (actualizadas DS 013-2013-PRODUCE):\n\n"
            "MICROEMPRESA: Ventas anuales hasta 150 UIT (aprox. S/ 772,500 en 2024). "
            "Puede tener de 1 a 10 trabajadores.\n\n"
            "PEQUENA EMPRESA: Ventas anuales desde 150 hasta 1700 UIT (aprox. hasta S/ 8,755,000). "
            "Puede tener hasta 100 trabajadores.\n\n"
            "MEDIANA EMPRESA: Ventas desde 1701 hasta 2300 UIT (no forma parte del regimen MYPE "
            "estrictamente, pero tiene regimen tributario propio).\n\n"
            "Registro: Las MYPE deben inscribirse en el Registro Nacional de la Micro y Pequena "
            "Empresa (REMYPE), actualmente administrado por SUNAT. La inscripcion es gratuita "
            "y se realiza en linea. Tiene vigencia indefinida."
        ),
    },
    {
        "article": "MYPE-LABORAL",
        "section_path": "DL 1086 > MYPE > Regimen laboral especial",
        "content": (
            "Regimen Laboral Especial de la MYPE (DL 1086, modificado por Ley 30056).\n\n"
            "El regimen laboral especial MYPE otorga menores costos laborales para las empresas "
            "que califiquen, con el objetivo de promover la formalizacion.\n\n"
            "REGIMEN LABORAL DE MICROEMPRESA:\n"
            "- Remuneracion minima: RMV vigente (S/ 1,025 en 2024).\n"
            "- Vacaciones: 15 dias calendario por ano (no 30).\n"
            "- CTS: No aplica.\n"
            "- Gratificaciones: No aplica.\n"
            "- Indemnizacion por despido arbitrario: 10 remuneraciones diarias por ano, "
            "  maximo 90 remuneraciones diarias.\n"
            "- Seguro de salud: ESSALUD (9% a cargo del empleador) o SIS subsidiado para el trabajador.\n\n"
            "REGIMEN LABORAL DE PEQUENA EMPRESA:\n"
            "- Vacaciones: 15 dias (puede negociarse hasta 30).\n"
            "- CTS: 15 dias por ano.\n"
            "- Gratificaciones: media remuneracion en julio y diciembre.\n"
            "- Indemnizacion por despido: 20 remuneraciones diarias por ano, maximo 120.\n"
            "- Seguro de vida: aplica desde el 4to ano de trabajo.\n"
            "- ESSALUD: 9%.\n\n"
            "Las MYPE tambien acceden al Regimen Tributario MYPE (tasa de IR 10% a 29.5%) "
            "y a programas de garantias estatales (Fondo CRECER, Reactiva Peru, etc.)."
        ),
    },
    {
        "article": "COD-COMERCIO",
        "section_path": "Codigo de Comercio > Normas vigentes > Comerciante y obligaciones mercantiles",
        "content": (
            "Codigo de Comercio del Peru (promulgado en 1902, aun parcialmente vigente).\n\n"
            "Aunque gran parte del Codigo de Comercio ha sido derogada o reemplazada por leyes "
            "especiales (LGS, Ley General del Sistema Financiero, LPAG, etc.), mantiene vigencia "
            "en algunos aspectos.\n\n"
            "COMERCIANTE (Art. 1): Son comerciantes para los efectos de este Codigo:\n"
            "1. Los que, teniendo capacidad legal para ejercer el comercio, se dedican a el "
            "habitualmente.\n"
            "2. Las companas mercantiles o industriales que se constituyeren con arreglo a "
            "este Codigo.\n\n"
            "ACTOS DE COMERCIO (Art. 2): La compraventa mercantil, los contratos de seguros, "
            "el transporte de personas o cosas, los contratos de comision, mandato y deposito "
            "cuando se realicen por comerciantes, entre otros.\n\n"
            "LIBROS DE CONTABILIDAD (Art. 33): Los comerciantes estan obligados a llevar la "
            "contabilidad de sus operaciones con arreglo a las prescripciones del Codigo.\n\n"
            "CONTRATOS MERCANTILES VIGENTES en el Codigo de Comercio:\n"
            "- Contrato de comision (representacion mercantil)\n"
            "- Contrato de transporte terrestre\n"
            "- Contrato de seguro (complementado por Ley 29946)\n"
            "- Letras de cambio, pagares y cheques (complementado por Ley 16587 y Ley 27287)"
        ),
    },
    {
        "article": "CORP-GOBIERNO",
        "section_path": "Derecho Corporativo > Gobierno Corporativo > Principios SMV",
        "content": (
            "Gobierno Corporativo en el Peru — Principios y Marco Normativo.\n\n"
            "El buen gobierno corporativo es el conjunto de practicas, formalizadas en reglas, "
            "con las que se dirige y controla una empresa. En Peru se rige principalmente por:\n\n"
            "CODIGO DE BUEN GOBIERNO CORPORATIVO para Sociedades Peruanas (2013, SMV - "
            "Superintendencia del Mercado de Valores). Aunque es un documento de adopcion "
            "voluntaria para empresas no listadas, es obligatorio reportar su cumplimiento "
            "para empresas inscritas en la Bolsa de Valores de Lima (BVL).\n\n"
            "PILARES DEL CODIGO:\n"
            "1. Derechos de los accionistas\n"
            "2. Junta general de accionistas\n"
            "3. El directorio y la alta gerencia\n"
            "4. Riesgo y cumplimiento\n"
            "5. Transparencia de la informacion\n\n"
            "DEBERES FIDUCIARIOS DEL DIRECTORIO (Ley 26887):\n"
            "- Deber de diligencia: actuar con la diligencia de un ordenado hombre de negocios.\n"
            "- Deber de lealtad: actuar en el interes de la sociedad y no en beneficio propio.\n"
            "- Obligacion de no competencia: no pueden desarrollar actividades competidoras.\n"
            "- Prohibicion de conflicto de intereses: deben abstenerse de votar en asuntos "
            "  en que tengan interes personal."
        ),
    },
    {
        "article": "CORP-HOLDING",
        "section_path": "Ley 26887 > LGS > Titulo IX > Grupos de empresas y holding",
        "content": (
            "Grupos de Empresas y Holding en Peru.\n\n"
            "La LGS no regula expresamente los grupos de empresas, pero la practica y la "
            "jurisprudencia reconocen su existencia. Un grupo de empresas existe cuando "
            "varias sociedades, siendo juridicamente independientes, estan bajo una "
            "direccion economica unificada (control).\n\n"
            "HOLDING: Empresa (sociedad madre o matriz) que posee acciones o participaciones "
            "de otras empresas (subsidiarias o filiales) con el objetivo de controlarlas.\n\n"
            "EFECTOS LEGALES:\n"
            "1. Cada empresa del grupo es una persona juridica independiente (principio de "
            "   separacion de personalidades).\n"
            "2. Los creditos de la empresa madre no se pueden ejecutar sobre bienes de la "
            "   subsidiaria (y viceversa), salvo levantamiento del velo societario.\n"
            "3. Las transacciones entre empresas del grupo deben ser a valores de mercado "
            "   (precios de transferencia).\n\n"
            "LEVANTAMIENTO DEL VELO SOCIETARIO:\n"
            "En casos de fraude, cuando se usa la personalidad juridica para evadir "
            "obligaciones, el Poder Judicial puede levantar el velo y responsabilizar a los "
            "socios o empresa controlante. Aplica cuando hay:\n"
            "- Confusion de patrimonio.\n"
            "- Utilizacion de la forma societaria para fines ilicitos.\n"
            "- Infracapitalizacion fraudulenta."
        ),
    },
    {
        "article": "CORP-ASAMBLEAS",
        "section_path": "Ley 26887 > LGS > SA > JGA > Acuerdos e impugnacion",
        "content": (
            "Impugnacion de Acuerdos de la JGA (Arts. 139-150 LGS).\n\n"
            "Art. 139: Pueden ser impugnados judicialmente los acuerdos de la junta general "
            "cuyo contenido sea contrario a la ley, se oponga al estatuto o al pacto social "
            "o lesione, en beneficio directo o indirecto de uno o varios accionistas, los "
            "intereses de la sociedad.\n\n"
            "PLAZOS PARA IMPUGNAR (Art. 142):\n"
            "- Acuerdos violatorios de la ley o del estatuto: 2 meses desde el acuerdo si "
            "  el demandante concurrio a la junta; 3 meses si no concurrio o si el acuerdo "
            "  no fue inscrito en el Registro; 1 ano si el acuerdo es inscribible y fue inscrito.\n"
            "- Acuerdos nulos de pleno derecho (contrarios al orden publico): no prescriben.\n\n"
            "LEGITIMADOS PARA IMPUGNAR:\n"
            "- Accionistas que en la junta hubieran hecho constar su oposicion al acuerdo.\n"
            "- Accionistas ausentes.\n"
            "- Accionistas que hayan sido privados del derecho a votar.\n\n"
            "SUSPENSION DEL ACUERDO IMPUGNADO:\n"
            "El demandante puede solicitar medida cautelar de suspension del acuerdo "
            "impugnado. El juez puede exigir contracautela si el acuerdo suspendido "
            "puede causar dano a la sociedad."
        ),
    },
    {
        "article": "CORP-VALORACION",
        "section_path": "Ley 26887 > LGS > Acciones > Valoracion > Separacion de socios",
        "content": (
            "Derecho de Separacion y Valoracion de Acciones en la LGS.\n\n"
            "DERECHO DE SEPARACION (Art. 200 LGS):\n"
            "Cuando la junta general acuerde:\n"
            "a) El cambio del objeto social.\n"
            "b) El traslado del domicilio social al extranjero.\n"
            "c) La creacion de limitaciones a la transferibilidad de las acciones o la "
            "   modificacion de las existentes.\n"
            "Los accionistas que voten en contra tienen el derecho de separarse de la "
            "sociedad y que se les reembolse el valor de sus acciones.\n\n"
            "PROCEDIMIENTO DE SEPARACION:\n"
            "1. El accionista comunica su separacion dentro de los 10 dias de la inscripcion "
            "   del acuerdo en el Registro.\n"
            "2. La sociedad determina el valor de las acciones de comun acuerdo o por peritos.\n"
            "3. Si hay desacuerdo en el valor, se nombra un perito por cada parte y un tercero "
            "   por el Poder Judicial.\n\n"
            "EXCLUSION DE SOCIOS en SRL (Art. 293 LGS):\n"
            "Un socio puede ser excluido por acuerdo de la junta de socios cuando realiza "
            "actos contrarios a los estatutos, usa el patrimonio social en beneficio propio, "
            "obstaculiza la gestion de la sociedad, o comete actos desleales."
        ),
    },
    {
        "article": "CORP-CONTRATACIONES",
        "section_path": "Ley 26887 > LGS > Actos ultravires y responsabilidad organica",
        "content": (
            "Responsabilidad Organica y Contratos de la Sociedad.\n\n"
            "REPRESENTACION ORGANICA (Art. 12 LGS):\n"
            "La sociedad esta obligada hacia aquellos con quienes haya contratado y, en "
            "general, hacia los terceros con quienes sus representantes, en ejercicio de "
            "sus atribuciones, hayan celebrado negocios juridicos.\n\n"
            "ACTOS ULTRAVIRES: Los actos del representante que excedan sus facultades "
            "(fuera del objeto social o del poder otorgado) no obligan a la sociedad, "
            "salvo que los ratifique o que el tercero haya actuado de buena fe.\n\n"
            "CONTRATOS CON DIRECTORES Y GERENTES (Art. 163 LGS):\n"
            "Las operaciones entre la sociedad y sus directores o gerentes que no se realicen "
            "en condiciones de mercado o que impliquen conflicto de interes requieren:\n"
            "- Aprobacion del directorio (cuando involucra a gerentes).\n"
            "- Aprobacion de la junta general (cuando involucra a directores).\n"
            "- Abstension del director o gerente conflictuado en la votacion.\n\n"
            "CONFLICTO DE INTERES (Art. 167 LGS): El director que tenga conflicto de "
            "interes debe ponerlo de conocimiento del directorio y abstenerse de participar "
            "en la deliberacion y votacion del asunto. El incumplimiento genera responsabilidad "
            "personal frente a la sociedad y terceros."
        ),
    },
    {
        "article": "CORP-BOND-DEUDA",
        "section_path": "Ley 26887 > LGS > Obligaciones > Emision de bonos y deuda corporativa",
        "content": (
            "Emision de Obligaciones (Bonos Corporativos) y Deuda Corporativa (Arts. 304-325 LGS).\n\n"
            "Art. 304: Las sociedades anonimas pueden emitir series numeradas de obligaciones "
            "que reconocen o crean una deuda a favor de sus titulares. "
            "Las obligaciones pueden ser:\n"
            "- Obligaciones en moneda nacional o extranjera.\n"
            "- Obligaciones con garantia especifica (hipotecaria, prendaria) o sin garantia.\n"
            "- Obligaciones convertibles en acciones.\n\n"
            "EMISION PUBLICA vs PRIVADA:\n"
            "- Emision publica (oferta publica): regulada por la Ley del Mercado de Valores "
            "  (DL 861) y supervisada por la SMV. Requiere inscripcion en el Registro Publico "
            "  del Mercado de Valores (RPMV) y prospectos informativos.\n"
            "- Emision privada (oferta privada): dirigida a inversores institucionales. "
            "  No requiere inscripcion en la SMV pero si cumplir la LGS.\n\n"
            "ASAMBLEA DE OBLIGACIONISTAS (Art. 325 LGS): Los tenedores de obligaciones "
            "de cada serie pueden constituir asamblea para defender sus intereses. "
            "El representante de los obligacionistas puede verificar el cumplimiento de las "
            "condiciones de la emision.\n\n"
            "El mercado de capitales peruano (BVL) permite a las empresas financiarse mediante "
            "la emision de bonos corporativos, bonos subordinados y papeles comerciales."
        ),
    },
    {
        "article": "CORP-SAA",
        "section_path": "Ley 26887 > LGS > SAA > Sociedad Anonima Abierta > Requisitos y SMV",
        "content": (
            "Sociedad Anonima Abierta (SAA) — Seccion Quinta LGS (Arts. 249-264).\n\n"
            "Art. 249: La sociedad anonima es abierta cuando se cumpla una o mas de las "
            "siguientes condiciones:\n"
            "a) Ha hecho oferta publica primaria de acciones o de obligaciones convertibles.\n"
            "b) Tiene mas de setecientos cincuenta (750) accionistas.\n"
            "c) Mas del treinta y cinco por ciento (35%) de su capital pertenece a ciento "
            "   setenta y cinco (175) o mas accionistas.\n"
            "d) Se constituye como tal.\n"
            "e) Todos sus socios son personas juridicas o fondos de inversion.\n\n"
            "Las SAA estan bajo la supervision de la Superintendencia del Mercado de Valores "
            "(SMV). Deben cumplir obligaciones adicionales:\n"
            "- Divulgacion de informacion financiera periodica (estados financieros trimestrales "
            "  y anuales auditados) ante la SMV.\n"
            "- Informacion de hechos de importancia (hecho relevante o material).\n"
            "- Directores independientes (minimo 1/3 del directorio).\n"
            "- Comite de auditoria.\n\n"
            "RESTRICCIONES A LA LIBRE TRANSFERIBILIDAD: Las SAA no pueden establecer "
            "limitaciones a la libre transmisibilidad de sus acciones (Art. 253)."
        ),
    },
]
