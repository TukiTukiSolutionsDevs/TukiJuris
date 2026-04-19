"""
Seed: Derecho Laboral — Expansion de conocimiento laboral peruano.

Normas cubiertas:
- Ley de Seguridad y Salud en el Trabajo (Ley 29783 y DS 005-2012-TR)
- Ley de Relaciones Colectivas de Trabajo (TUO DS 010-2003-TR)
  - Sindicatos, negociacion colectiva, huelga
- Ley de Teletrabajo (Ley 31572 y DS 002-2023-TR)
- Ley de Tercerizacion (Ley 29245 y DS 006-2008-TR)
- Contratos de trabajo: tipos y modalidades (TUO DL 728)
- Beneficios sociales adicionales: SNP, AFP, EsSalud, SCTR
"""

LABORAL_EXT_ARTICLES = [
    # === SEGURIDAD Y SALUD EN EL TRABAJO ===
    {
        "article": "SST-1",
        "section_path": "Ley 29783 > SST > Titulo Preliminar > Principios",
        "content": (
            "Ley de Seguridad y Salud en el Trabajo — Ley 29783 (2011) y su Reglamento "
            "DS 005-2012-TR, modificados por Ley 30222 (2014).\n\n"
            "Principios del Sistema Nacional de Seguridad y Salud en el Trabajo (Art. I-IX):\n\n"
            "I. Principio de Prevencion: El empleador garantiza el establecimiento de los medios "
            "y condiciones que protejan la vida, la salud y el bienestar de los trabajadores.\n\n"
            "II. Principio de Responsabilidad: El empleador asume las implicancias economicas, "
            "legales y de cualquiera otra indole a consecuencia de un accidente o enfermedad que "
            "sufra el trabajador en el desempeno de sus funciones o a consecuencia de el.\n\n"
            "III. Principio de Cooperacion: El Estado, los empleadores y los trabajadores, y sus "
            "organizaciones sindicales establecen mecanismos que garanticen una permanente "
            "colaboracion y coordinacion en SST.\n\n"
            "IV. Principio de Informacion y Capacitacion: Los trabajadores reciben información "
            "y capacitacion en materia de SST.\n\n"
            "V. Principio de Gestion Integral: El empleador promueve e integra la gestion de la "
            "SST en la gestion general de la empresa."
        ),
    },
    {
        "article": "SST-COMITE",
        "section_path": "Ley 29783 > SST > Capitulo IV > Comite y Supervisor de SST",
        "content": (
            "Comite de Seguridad y Salud en el Trabajo (Arts. 29-42 Ley 29783 y DS 005-2012-TR).\n\n"
            "OBLIGATORIEDAD:\n"
            "- Empleadores con 20 o mas trabajadores: Comite de SST.\n"
            "- Empleadores con menos de 20 trabajadores: Supervisor de SST (un trabajador elegido).\n\n"
            "COMPOSICION DEL COMITE:\n"
            "- Numero paritario de representantes del empleador y de los trabajadores.\n"
            "- Minimo 4 miembros (2 por cada parte), maximo 12.\n"
            "- Presidente: elegido por los miembros del Comite.\n"
            "- Secretario: Jefe de Seguridad (parte del empleador).\n\n"
            "FUNCIONES DEL COMITE (Art. 42):\n"
            "1. Aprobar el Reglamento Interno de SST.\n"
            "2. Aprobar el Programa Anual de SST.\n"
            "3. Verificar el cumplimiento de la legislacion de SST.\n"
            "4. Analizar las causas de accidentes e incidentes y proponer medidas correctivas.\n"
            "5. Promover una cultura de prevencion de riesgos laborales.\n\n"
            "El mandato del Comite es de 1 ano. Los miembros trabajadores son elegidos mediante "
            "votacion directa y secreta por todos los trabajadores."
        ),
    },
    {
        "article": "SST-IPERC",
        "section_path": "Ley 29783 > SST > Capitulo VI > IPERC y mapa de riesgos",
        "content": (
            "IPERC — Identificacion de Peligros, Evaluacion de Riesgos y Medidas de Control "
            "(Art. 57 Ley 29783 y Arts. 82-88 DS 005-2012-TR).\n\n"
            "El empleador debe elaborar y actualizar periodicamente la Evaluacion del riesgo, "
            "la cual debe identificar los peligros en el lugar de trabajo, evaluar los riesgos "
            "y adoptar medidas de control.\n\n"
            "METODOLOGIA IPERC:\n"
            "1. Identificacion de actividades y tareas.\n"
            "2. Identificacion de peligros asociados a cada actividad.\n"
            "3. Evaluacion del riesgo: probabilidad x consecuencia = nivel de riesgo.\n"
            "4. Determinacion de controles existentes.\n"
            "5. Propuesta de medidas de control adicionales (jerarquia: eliminacion, sustitucion, "
            "   controles de ingenieria, controles administrativos, EPP).\n\n"
            "MAPA DE RIESGOS (Art. 35): Es el plano del centro de trabajo donde se identifica "
            "la ubicacion de los peligros y riesgos. Debe estar actualizado y visible para los "
            "trabajadores.\n\n"
            "OBLIGACION DEL EMPLEADOR: El empleador actualiza el IPERC al menos una vez al ano "
            "o cuando cambien las condiciones de trabajo, ocurra un accidente o se adquiera "
            "nueva maquinaria."
        ),
    },
    {
        "article": "SST-ACCIDENTES",
        "section_path": "Ley 29783 > SST > Capitulo IX > Accidentes de trabajo > Investigacion",
        "content": (
            "Accidentes de Trabajo e Investigacion (Arts. 82-95 Ley 29783 y DS 005-2012-TR).\n\n"
            "ACCIDENTE DE TRABAJO (Art. 2 DS 005-2012-TR): Todo suceso repentino que sobrevenga "
            "por causa o con ocasion del trabajo y que produzca en el trabajador una lesion "
            "organica, una perturbacion funcional, una invalidez o la muerte.\n\n"
            "CLASIFICACION:\n"
            "- Accidente leve: descanso medico hasta 1 dia.\n"
            "- Accidente incapacitante: descanso medico mayor a 1 dia. Puede ser:\n"
            "  * Parcial temporal, parcial permanente, total temporal, total permanente.\n"
            "- Accidente mortal: produce muerte del trabajador.\n\n"
            "NOTIFICACION OBLIGATORIA (Art. 82 Ley 29783):\n"
            "- Accidentes mortales o incapacitantes: dentro de las 24 horas al MTPE via "
            "  sistema SINADEF.\n"
            "- Incidentes peligrosos: dentro de las 24 horas.\n\n"
            "INVESTIGACION (Art. 93): El empleador investiga la causa de los accidentes e "
            "incidentes para implementar medidas correctivas. La investigacion debe:\n"
            "1. Determinar las causas basicas (factor de trabajo y factor personal).\n"
            "2. Determinar las causas inmediatas (actos y condiciones subestandar).\n"
            "3. Proponer medidas correctivas.\n"
            "4. Documentar y registrar en el libro de accidentes."
        ),
    },
    # === RELACIONES COLECTIVAS DE TRABAJO ===
    {
        "article": "RLCT-SINDICATOS",
        "section_path": "TUO DS 010-2003-TR > Ley RLCT > Titulo I > Sindicatos > Constitucion",
        "content": (
            "Ley de Relaciones Colectivas de Trabajo (TUO aprobado por DS 010-2003-TR, "
            "modificado por Ley 31110 y otras normas).\n\n"
            "SINDICATOS (Art. 2): Los trabajadores tienen el derecho a constituir organizaciones "
            "sindicales, sin autorizacion previa. La ley protege este derecho de toda interferencia "
            "del empleador o de las autoridades.\n\n"
            "CONSTITUCION (Art. 16):\n"
            "- Sindicato de empresa: minimo 20 trabajadores.\n"
            "- Sindicato de actividad, gremio o de industria: minimo 50 trabajadores.\n"
            "- Federaciones: minimo 2 sindicatos.\n"
            "- Confederaciones: minimo 2 federaciones.\n\n"
            "REGISTRO SINDICAL (Art. 17): El sindicato adquiere personeria juridica con su "
            "inscripcion en el Registro Sindical del MTPE (ahora Registro de Organizaciones "
            "Sindicales - ROST). Para inscribirse se presenta: estatuto, acta de asamblea "
            "constitutiva y nomina de afiliados.\n\n"
            "FUERO SINDICAL (Arts. 30-33): Los dirigentes sindicales gozan de proteccion "
            "especial contra el despido y los actos de discriminacion antisindical. El fuero "
            "ampara durante el mandato y 90 dias adicionales. Para despedir a un dirigente "
            "sindical se requiere autorizacion judicial previa."
        ),
    },
    {
        "article": "RLCT-NEGOCIACION",
        "section_path": "TUO DS 010-2003-TR > RLCT > Titulo II > Negociacion Colectiva",
        "content": (
            "Negociacion Colectiva (Arts. 41-61 TUO RLCT DS 010-2003-TR).\n\n"
            "Art. 41: Negociacion colectiva es el que celebran una o varias organizaciones "
            "sindicales de trabajadores o, en ausencia de estas, los representantes de los "
            "trabajadores, con uno o varios empleadores o sus organizaciones.\n\n"
            "NIVELES DE NEGOCIACION:\n"
            "- Nivel de empresa (principalmente en Peru).\n"
            "- Nivel de rama de actividad o industria.\n"
            "- Nivel gremial.\n\n"
            "PROCESO DE NEGOCIACION:\n"
            "1. El sindicato presenta el pliego de reclamos al empleador entre enero y marzo.\n"
            "2. TRATO DIRECTO: Negociacion directa entre las partes (hasta 20 dias habiles).\n"
            "3. CONCILIACION: Intervencion del MTPE como conciliador (si fracaso el trato directo).\n"
            "4. ARBITRAJE: Si persiste el desacuerdo, cualquiera puede solicitar arbitraje "
            "   (potestativo) o las partes acuerdan someterse a arbitraje voluntario. "
            "   Tambien puede ser arbitraje obligatorio (en servicios publicos esenciales).\n\n"
            "CONVENIO COLECTIVO (Art. 42): Es el acuerdo destinado a regular las remuneraciones, "
            "condiciones de trabajo y productividad. Tiene fuerza vinculante y se aplica a todos "
            "los trabajadores de la empresa, incluyendo los no afiliados."
        ),
    },
    {
        "article": "RLCT-HUELGA",
        "section_path": "TUO DS 010-2003-TR > RLCT > Titulo III > Huelga",
        "content": (
            "Derecho de Huelga (Arts. 72-88 TUO RLCT DS 010-2003-TR).\n\n"
            "Art. 72: La huelga es la suspension colectiva del trabajo acordada mayoritariamente "
            "y realizada en forma voluntaria y pacifica por los trabajadores.\n\n"
            "REQUISITOS PARA DECLARAR LA HUELGA (Art. 73):\n"
            "1. Que tenga por objeto la defensa de los derechos e intereses economicos y sociales.\n"
            "2. Que sea acordada por mas de la mitad de los trabajadores a quienes comprende.\n"
            "3. Que sea comunicada al empleador y a la AAT (Autoridad Administrativa de Trabajo) "
            "   con 5 dias de anticipacion (10 dias en servicios publicos esenciales).\n"
            "4. Que los trabajadores en huelga designen representes para el mantenimiento de los "
            "   servicios minimos.\n\n"
            "DECLARACION DE IMPROCEDENCIA O ILEGALIDAD (Art. 84):\n"
            "La AAT puede declarar improcedente la huelga si no cumple los requisitos formales "
            "o ilegal si se inicia sin cumplir las formalidades, viola la prohibicion de huelga "
            "en servicios esenciales o si su ejercicio implica actividades violentas.\n\n"
            "SERVICIOS ESENCIALES: El personal necesario para el mantenimiento y operacion de los "
            "equipos y la continuidad de servicios cuya paralizacion ponga en peligro personas, "
            "instalaciones o recursos naturales."
        ),
    },
    # === TELETRABAJO ===
    {
        "article": "TELETRABAJO-1",
        "section_path": "Ley 31572 > Teletrabajo > Modalidades y derechos",
        "content": (
            "Ley de Teletrabajo — Ley 31572 (2022) y Reglamento DS 002-2023-TR.\n\n"
            "Art. 2: El teletrabajo es una modalidad especial de prestacion de servicios "
            "que se caracteriza por la utilizacion de tecnologias de la informacion y comunicacion "
            "(TIC) en las instituciones publicas y privadas. Puede ser:\n\n"
            "MODALIDADES:\n"
            "- TELETRABAJO TOTAL: El trabajador realiza su actividad exclusivamente desde el "
            "  lugar elegido fuera de los locales del empleador.\n"
            "- TELETRABAJO PARCIAL (hibrido): El trabajador alterna dias de trabajo en los "
            "  locales del empleador con dias de teletrabajo.\n\n"
            "DERECHOS DEL TELETRABAJADOR (Arts. 6-8):\n"
            "1. Los mismos derechos que los trabajadores presenciales (remuneracion, "
            "   beneficios sociales, SST).\n"
            "2. DERECHO A LA DESCONEXION DIGITAL: Al menos 12 horas continuas de desconexion "
            "   en periodo de 24 horas. El empleador no puede requerir al trabajador que atienda "
            "   comunicaciones, mensajes o llamadas durante ese periodo.\n"
            "3. Derecho a recibir equipamiento y cubrir los gastos de conectividad.\n\n"
            "OBLIGACION DEL EMPLEADOR: Proveer, mantener o compensar los equipos, herramientas "
            "tecnologicas e insumos necesarios para el teletrabajo, salvo acuerdo en contrario."
        ),
    },
    {
        "article": "TELETRABAJO-2",
        "section_path": "Ley 31572 > Teletrabajo > Reversibilidad y obligaciones",
        "content": (
            "Teletrabajo — Reversibilidad y obligaciones adicionales (Ley 31572 y DS 002-2023-TR).\n\n"
            "REVERSIBILIDAD (Art. 9):\n"
            "El teletrabajador puede solicitar la reversion al trabajo presencial en cualquier "
            "momento. Asimismo, el empleador puede revertir el teletrabajo al trabajo presencial "
            "cuando exista razon objetiva para ello, con un preaviso de 30 dias en el sector "
            "privado (salvo acuerdo en contrario).\n\n"
            "ACUERDO DE TELETRABAJO:\n"
            "Debe constar por escrito y contener:\n"
            "1. Descripcion de las actividades a realizar en modalidad de teletrabajo.\n"
            "2. Lugar o lugares donde se realizara el teletrabajo.\n"
            "3. Distribucion de la jornada de trabajo (si es hibrido).\n"
            "4. Mecanismos de supervision y control del trabajo.\n"
            "5. Responsabilidad sobre el equipamiento y los gastos.\n\n"
            "SEGURIDAD Y SALUD EN TELETRABAJO:\n"
            "El empleador debe garantizar la seguridad y salud del teletrabajador en el lugar "
            "de teletrabajo. Puede realizar inspecciones con previo aviso y consentimiento del "
            "trabajador en el caso de domicilio particular.\n\n"
            "IGUALDAD DE TRATO: Prohibida la discriminacion entre trabajadores presenciales y "
            "teletrabajadores en materia de remuneraciones, jornada, beneficios y formacion."
        ),
    },
    # === TERCERIZACIÓN ===
    {
        "article": "TERCERIZAR-1",
        "section_path": "Ley 29245 > Tercerizacion > Requisitos y efectos",
        "content": (
            "Ley de Tercerizacion — Ley 29245 (2008) y su Reglamento DS 006-2008-TR.\n\n"
            "Art. 1: Se denomina tercerizacion a la contratacion de empresas para que desarrollen "
            "actividades especializadas u obras, siempre que aquellas asuman los servicios "
            "prestados por su cuenta y riesgo; cuenten con sus propios recursos financieros, "
            "tecnicos o materiales; sean responsables por los resultados de sus actividades y "
            "sus trabajadores esten bajo su exclusiva subordinacion.\n\n"
            "ELEMENTOS QUE DETERMINAN UNA TERCERIZACION VALIDA:\n"
            "1. Empresa tercerizadora con personeria juridica propia.\n"
            "2. Servicio especializado distinto al core business de la empresa principal.\n"
            "3. La tercerizadora asume el riesgo de la actividad.\n"
            "4. La tercerizadora tiene recursos propios (activos, equipos, capital).\n"
            "5. Los trabajadores estan bajo la subordinacion exclusiva de la tercerizadora.\n\n"
            "DERECHOS DE LOS TRABAJADORES DESPLAZADOS (Art. 8):\n"
            "Los trabajadores de la empresa tercerizadora desplazados a la empresa principal "
            "tienen derecho a laborar en las instalaciones de la empresa principal con las "
            "mismas condiciones de seguridad y salud."
        ),
    },
    {
        "article": "TERCERIZAR-2",
        "section_path": "Ley 29245 > Tercerizacion > Desnaturalizacion y solidaridad",
        "content": (
            "Desnaturalizacion y Solidaridad en la Tercerizacion (Ley 29245 y DS 006-2008-TR).\n\n"
            "DESNATURALIZACION DE LA TERCERIZACION (Art. 5 DS 006-2008-TR):\n"
            "Se produce cuando en la tercerizacion se evidencia:\n"
            "1. La subordinacion del trabajador desplazado a la empresa principal.\n"
            "2. La propiedad de los bienes de produccion por parte de la empresa principal.\n"
            "3. La ausencia de equipamiento o recursos propios de la tercerizadora.\n"
            "4. El desplazamiento continuo de los trabajadores a la empresa principal.\n\n"
            "CONSECUENCIA DE LA DESNATURALIZACION: Los trabajadores desplazados pasan a ser "
            "considerados trabajadores de la empresa principal, con todos sus derechos.\n\n"
            "SOLIDARIDAD LABORAL Y PREVISIONAL (Art. 9 Ley 29245):\n"
            "La empresa principal es solidariamente responsable con la empresa tercerizadora "
            "por el pago de los derechos y beneficios laborales de los trabajadores desplazados "
            "(remuneraciones, CTS, gratificaciones, ESSALUD, AFP) durante el periodo de "
            "desplazamiento.\n\n"
            "REGISTRO DE EMPRESAS TERCERIZADORAS (Art. 12 DS 006-2008-TR):\n"
            "Las empresas tercerizadoras deben inscribirse en el Registro de Empresas y "
            "Entidades que realizan Actividades de Tercerizacion del MTPE."
        ),
    },
    # === CONTRATOS DE TRABAJO ===
    {
        "article": "CONTRATOS-MODALIDAD",
        "section_path": "TUO DL 728 > DS 003-97-TR > Contratos modales > Tipos y plazos",
        "content": (
            "Contratos de Trabajo Sujetos a Modalidad (Arts. 53-83 TUO DL 728 DS 003-97-TR).\n\n"
            "Art. 53: Los contratos de trabajo sujetos a modalidad pueden celebrarse cuando "
            "asi lo requieran las necesidades del mercado o mayor produccion, o cuando lo exija "
            "la naturaleza temporal o accidental del servicio a prestar o de la obra a ejecutar.\n\n"
            "CONTRATOS DE NATURALEZA TEMPORAL:\n"
            "1. Inicio o incremento de actividad (Art. 57): hasta 3 anos.\n"
            "2. Necesidades del mercado (Art. 58): hasta 5 anos.\n"
            "3. Reconversion empresarial (Art. 59): hasta 2 anos.\n\n"
            "CONTRATOS DE NATURALEZA ACCIDENTAL:\n"
            "4. Ocasional (Art. 60): hasta 6 meses al ano.\n"
            "5. Suplencia (Art. 61): hasta que el titular retorne.\n"
            "6. Emergencia (Art. 62): por el tiempo que dure la emergencia.\n\n"
            "CONTRATOS PARA OBRA O SERVICIO:\n"
            "7. Especifico (Art. 63): hasta que concluya la obra.\n"
            "8. Intermitente (Art. 64): sin limite de tiempo.\n"
            "9. Temporada (Art. 67): por cada temporada.\n\n"
            "REQUISITOS FORMALES: Deben constar por escrito, registrarse en el MTPE dentro de "
            "los 15 dias habiles, y no superar los plazos maximos. Si se excede el plazo o no "
            "se cumple la formalidad, el contrato se convierte en indeterminado."
        ),
    },
    {
        "article": "CONTRATOS-FORMACION",
        "section_path": "Ley 28518 > Modalidades formativas laborales",
        "content": (
            "Modalidades Formativas Laborales — Ley 28518 (2005).\n\n"
            "Las modalidades formativas no constituyen relacion laboral, pero si generan "
            "obligaciones para el beneficiador (empresa).\n\n"
            "MODALIDADES:\n"
            "1. APRENDIZAJE (SENATI/SENCICO): Para jovenes de 14 a 21 anos en formacion "
            "   tecnica. Duracion: segun plan de formacion. Subvencion: 50% RMV.\n\n"
            "2. PRACTICAS PRE-PROFESIONALES: Para estudiantes universitarios o de institutos "
            "   (de carrera tecnica o profesional). No puede superar el 20% del total de "
            "   trabajadores. Duracion: maxima 1 ano por empresa. Subvencion: RMV vigente.\n\n"
            "3. PRACTICAS PROFESIONALES: Para egresados de institutos o universidades. "
            "   Duracion: maxima 1 ano. Subvencion: RMV vigente.\n\n"
            "4. CAPACITACION LABORAL JUVENIL: Para jovenes entre 16 y 23 anos sin experiencia. "
            "   Duracion: 3 a 6 meses. Subvencion: RMV vigente.\n\n"
            "5. PASANTIA: Para estudiantes de colegios secundarios o de institutos y universidades. "
            "   Duracion: 3 meses. Subvencion: 10% RMV.\n\n"
            "DERECHOS COMUNES: Seguro contra accidentes de trabajo (SCTR o equivalente), "
            "descanso no menor de 30 dias por 12 meses de labor, proteccion de la madre "
            "gestante (incluye prohibicion de retiro)."
        ),
    },
    {
        "article": "LABORAL-SEGURIDAD-SOCIAL",
        "section_path": "Derecho Laboral > Seguridad Social > SNP, AFP, ESSALUD, SCTR",
        "content": (
            "Sistema de Seguridad Social en el Peru — Pensiones y Salud.\n\n"
            "SISTEMA PENSIONARIO:\n"
            "El trabajador debe elegir entre:\n"
            "1. SNP — Sistema Nacional de Pensiones (DL 19990, ONP): Aporte: 13% de la "
            "   remuneracion del trabajador. Pension de jubilacion: 65 anos con 20 anos de "
            "   aportes (minima S/ 500, maxima 5 UIT/mes en 2024). Administrado por ONP.\n\n"
            "2. SPP — Sistema Privado de Pensiones (DL 25897, AFP): Aporte: 10% de "
            "   remuneracion + comision AFP + prima seguro SIS. Los fondos son de propiedad "
            "   del afiliado. Tipos de fondos: 0 (preservacion), 1 (conservador), 2 (mixto), "
            "   3 (crecimiento). Administrado por AFPs (Habitat, Integra, Prima, Profuturo).\n\n"
            "ESSALUD (Ley 26790): Aporte del 9% a cargo del empleador. Cubre prestaciones "
            "de salud para el trabajador y sus derechohabientes.\n\n"
            "SCTR — Seguro Complementario de Trabajo de Riesgo (Ley 26790, DS 003-98-SA):\n"
            "Obligatorio para trabajadores en actividades de alto riesgo (mineria, construccion, "
            "industria, entre otras). Cubre invalidez y sobrevivencia (pensiones) y atencion "
            "medica. Puede contratarse con ONP/ESSALUD o con una aseguradora privada."
        ),
    },
    {
        "article": "LABORAL-JORNADA",
        "section_path": "Constitucion Art. 25 y DL 854 > Jornada de trabajo > Horas extras",
        "content": (
            "Jornada de Trabajo y Horas Extras (Constitucion Art. 25, DL 854 y DS 007-2002-TR).\n\n"
            "JORNADA ORDINARIA (Art. 25 Constitucion):\n"
            "La jornada ordinaria de trabajo es de 8 horas diarias o 48 horas semanales como "
            "maximo. En caso de jornadas acumulativas o atipicas, el promedio de horas trabajadas "
            "en el periodo correspondiente no puede superar los maximos.\n\n"
            "SOBRETIEMPO — HORAS EXTRAS (Art. 9 DL 854):\n"
            "El trabajo en sobretiempo es voluntario, tanto en su otorgamiento como en su "
            "realizacion. Su imposicion acarrea responsabilidad del empleador.\n\n"
            "CALCULO DE LA SOBRETASA:\n"
            "- Primeras 2 horas extras al dia: 25% sobre valor hora ordinaria.\n"
            "- A partir de la 3ra hora extra: 35% sobre valor hora ordinaria.\n"
            "- Si el trabajador fue al centro de trabajo y no le permiten laborar: "
            "  derecho al pago del sobretiempo establecido.\n\n"
            "JORNADA NOCTURNA (DS 007-2002-TR): Entre las 10:00 p.m. y 6:00 a.m. "
            "La remuneracion no puede ser menor a la RMV mas un 35% (nocturnidad).\n\n"
            "DESCANSO SEMANAL Y EN DIAS FERIADOS (DL 713): Minimo 24 horas consecutivas "
            "por semana. Si se trabaja en feriado o en el dia de descanso: se paga doble."
        ),
    },
    {
        "article": "LABORAL-HOSTIGAMIENTO",
        "section_path": "Ley 27942 > Hostigamiento sexual laboral > Definicion y procedimiento",
        "content": (
            "Hostigamiento Sexual en el Trabajo — Ley 27942 (2003), modificada por Ley 29430 "
            "y Ley 30314, y su Reglamento DS 014-2019-MIMP.\n\n"
            "Art. 4: Se considera hostigamiento sexual tipico o chantaje sexual a la conducta "
            "fisica o verbal reiterada de naturaleza sexual o sexista no deseada o rechazada, "
            "realizada por una o mas personas que se aprovechan de una posicion de autoridad "
            "o jerarquia.\n\n"
            "HOSTIGAMIENTO AMBIENTAL: Hostigamiento sexual que no requiere posicion de "
            "autoridad. Lo puede cometer cualquier trabajador.\n\n"
            "OBLIGACIONES DEL EMPLEADOR:\n"
            "- Incorporar en el Reglamento Interno de Trabajo el procedimiento de queja e "
            "  investigacion de casos de hostigamiento sexual.\n"
            "- Designar a un responsable de atender las quejas.\n"
            "- Investigar los casos en un plazo maximo de 30 dias habiles.\n"
            "- Aplicar medidas correctivas si se confirma el hostigamiento.\n\n"
            "CONSECUENCIAS PARA EL HOSTIGADOR:\n"
            "- Si es jefe del trabajador: puede ser despedido por falta grave (Art. 25.i TUO DL 728).\n"
            "- Si es trabajador: puede ser sancionado hasta con despido.\n"
            "- Si es el empleador persona natural o miembro del directorio: el trabajador "
            "  hostigado puede optar por el despido indirecto con indemnizacion."
        ),
    },
    {
        "article": "LABORAL-REMUNERACION",
        "section_path": "TUO DL 728 > Remuneracion > Conceptos remunerativos y no remunerativos",
        "content": (
            "Remuneracion — Conceptos Remunerativos y No Remunerativos (Arts. 6-7 TUO DL 728).\n\n"
            "Art. 6: Constituye remuneracion para todo efecto legal el integro de lo que el "
            "trabajador recibe por sus servicios, en dinero o en especie, cualesquiera sean "
            "la forma o denominacion que tenga, siempre que sean de su libre disposicion.\n\n"
            "CONCEPTOS NO REMUNERATIVOS (Art. 19 DS 001-97-TR — Ley CTS):\n"
            "No se computan para CTS, gratificaciones, indemnizaciones ni beneficios similares:\n"
            "a) Gratificaciones extraordinarias (no otorgadas con regularidad).\n"
            "b) Bonificaciones por cierre de pliego.\n"
            "c) Participacion en las utilidades.\n"
            "d) Costo o valor de las condiciones de trabajo.\n"
            "e) Canasta de Navidad o similares.\n"
            "f) Valor del transporte (siempre que sea razonable y suministrado por el empleador).\n"
            "g) Asignacion o bonificacion por educacion (siempre que sea razonable).\n"
            "h) Asignacion por fallecimiento de familiar directo.\n"
            "i) Remuneracion por horas extras (no se computan para CTS y gratificaciones).\n\n"
            "REMUNERACION MINIMA VITAL (RMV): S/ 1,025 desde mayo de 2022. "
            "Es el piso minimo que debe recibir todo trabajador a jornada completa. "
            "Su fijacion corresponde al Poder Ejecutivo previo consenso del CNTPE."
        ),
    },
    {
        "article": "LABORAL-PARTICIPACION",
        "section_path": "DL 892 > Participacion en las utilidades > Porcentajes y calculo",
        "content": (
            "Participacion en las Utilidades — DL 892 (1996) y DS 009-98-TR.\n\n"
            "Los trabajadores de empresas que generan rentas de tercera categoria con "
            "mas de 20 trabajadores en planilla tienen derecho a participar en las "
            "utilidades de la empresa. Los porcentajes segun actividad son:\n\n"
            "- Empresas pesqueras: 10%\n"
            "- Telecomunicaciones: 10%\n"
            "- Industriales: 10%\n"
            "- Mineras: 8%\n"
            "- Comercio al por mayor y menor: 8%\n"
            "- Restaurantes, hoteles y actividades de esparcimiento: 8%\n"
            "- Otras empresas: 5%\n\n"
            "CALCULO (Art. 2 DL 892):\n"
            "La base es la renta neta imponible del ejercicio (la de la declaracion jurada anual "
            "del IR). El porcentaje se distribuye:\n"
            "- 50% en funcion a los dias laborados en el ejercicio.\n"
            "- 50% en funcion a la remuneracion de cada trabajador.\n\n"
            "LIMITE: El monto maximo de participacion por trabajador es de 18 remuneraciones "
            "mensuales. El excedente va al Fondo Nacional de Capacitacion Laboral.\n\n"
            "PLAZO DE PAGO: Dentro de los 30 dias naturales siguientes al vencimiento del plazo "
            "para la presentacion de la declaracion jurada anual del IR."
        ),
    },
    {
        "article": "LABORAL-PENSION-AFP",
        "section_path": "DL 25897 > SPP > AFP > Multifondos y jubilacion",
        "content": (
            "Sistema Privado de Pensiones (SPP) — DL 25897 y Reglamento DS 004-98-EF. "
            "Modificaciones por Ley 29903 (multifondos) y Ley 31192 (retiros extraordinarios).\n\n"
            "MULTIFONDOS: Cada afiliado puede elegir el tipo de fondo:\n"
            "- Fondo 0 (Preservacion de Capital): Para mayores de 65 anos o aversion total al riesgo.\n"
            "- Fondo 1 (Conservador): Para afiliados proximos a jubilarse.\n"
            "- Fondo 2 (Mixto o Balanceado): Fondo por defecto. Equilibrio riesgo-rentabilidad.\n"
            "- Fondo 3 (Apreciacion de Capital): Para jovenes con horizonte largo.\n\n"
            "APORTES EN EL SPP:\n"
            "- 10% de la remuneracion asegurable.\n"
            "- Comision de la AFP (puede ser comision por flujo o mixta).\n"
            "- Prima de seguro de invalidez y sobrevivencia.\n\n"
            "JUBILACION:\n"
            "- Jubilacion ordinaria: a los 65 anos. El afiliado elige modalidad de pension.\n"
            "- Jubilacion anticipada (REJA): Para desempleados mayores de 55 anos.\n"
            "- Jubilacion anticipada para trabajos peligrosos.\n\n"
            "RETIROS EXTRAORDINARIOS (Ley 31591 — 2022): Permite retirar hasta S/ 4 UIT "
            "en casos de cese de actividades o jubilacion. Han habido multiples normas "
            "de retiros extraordinarios desde la pandemia (2020-2022)."
        ),
    },
    {
        "article": "LABORAL-INSPECCION",
        "section_path": "Ley 28806 > Inspeccion del Trabajo > SUNAFIL > Infracciones",
        "content": (
            "Sistema de Inspeccion del Trabajo — Ley 28806 (2006) y SUNAFIL.\n\n"
            "La Superintendencia Nacional de Fiscalizacion Laboral (SUNAFIL), creada por "
            "Ley 29981 (2013), es el organismo que supervisa el cumplimiento de las "
            "normas laborales y de SST.\n\n"
            "PROCESO DE INSPECCION (Ley 28806):\n"
            "1. Actuacion inspectiva previa (visita de inspeccion, comparecencia o comprobacion).\n"
            "2. Acta de inspeccion.\n"
            "3. Requerimiento de subsanacion con plazo (para infracciones leves).\n"
            "4. Acta de infraccion (si no subsana o si es infraccion grave/muy grave).\n"
            "5. Liquidacion de multa.\n"
            "6. El empleador puede impugnar el acta en procedimiento sancionador.\n\n"
            "CLASIFICACION DE INFRACCIONES Y MULTAS (DS 019-2006-TR):\n"
            "- LEVES: No causar dano grave. Multa: hasta 5 UIT para microempresa, 10 UIT pymes, 50 UIT grandes.\n"
            "- GRAVES: Afectan derechos fundamentales. Multa: hasta 10 UIT, 20 UIT, 100 UIT.\n"
            "- MUY GRAVES: Los que causan dano mayor. Multa: hasta 20 UIT, 35 UIT, 200 UIT.\n\n"
            "CRITERIOS DE GRADUACION: Capacidad economica, reincidencia, numero de trabajadores "
            "afectados. SUNAFIL puede reducir multas por subsanacion voluntaria."
        ),
    },
]
