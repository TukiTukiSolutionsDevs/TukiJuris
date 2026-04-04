"""
Seed: Compliance — Extension de conocimiento en derecho de cumplimiento normativo peruano.

Normas cubiertas:
- Ley 29733 — Ley de Proteccion de Datos Personales y DS 003-2013-JUS (Reglamento)
- Ley 27693 — Ley que crea la UIF-Peru (prevencion lavado de activos)
- DL 1106 — Lucha eficaz contra el lavado de activos y financiamiento del terrorismo
- Ley 30424 — Responsabilidad administrativa de personas juridicas
- ISO 37001 principios aplicados al Peru
- Codigo de Buen Gobierno Corporativo para Sociedades Peruanas (SMV)
"""

COMPLIANCE_EXT_ARTICLES = [
    # =========================================================
    # PROTECCION DE DATOS PERSONALES — LEY 29733
    # =========================================================
    {
        "article": "PDP-PRINCIP",
        "section_path": "Ley 29733 > Titulo II > Principios rectores del tratamiento de datos",
        "content": (
            "Ley 29733 — Ley de Proteccion de Datos Personales. Principios rectores del tratamiento "
            "(Arts. 4-15 y DS 003-2013-JUS, Reglamento).\n\n"
            "1. Principio de legalidad (Art. 4): El tratamiento de datos personales se enmarca en "
            "lo establecido por la ley. Se prohibe la recopilacion de datos por medios fraudulentos, "
            "desleales o ilicitos.\n\n"
            "2. Principio de consentimiento (Art. 5): Para el tratamiento de datos es necesario el "
            "consentimiento de su titular. El consentimiento debe ser libre, previo, expreso, "
            "informado e inequivoco. Excepciones: relacion contractual, obligacion legal del "
            "responsable, datos publicamente accesibles, datos anonimizados.\n\n"
            "3. Principio de finalidad (Art. 6): Los datos deben ser recopilados para una finalidad "
            "determinada, explicita y licita. No pueden ser usados para finalidades incompatibles "
            "con la que motivo su recopilacion.\n\n"
            "4. Principio de proporcionalidad (Art. 7): Solo pueden ser objeto de tratamiento los "
            "datos personales que sean adecuados, relevantes y no excesivos en relacion a la "
            "finalidad para los que se hubieran obtenido.\n\n"
            "5. Principio de calidad (Art. 8): Los datos deben ser veraces, exactos y, en la medida "
            "de lo posible, actualizados, necesarios, pertinentes y adecuados respecto de la "
            "finalidad para la que fueron recopilados.\n\n"
            "6. Principio de seguridad (Art. 9): El titular del banco de datos o quien resulte "
            "responsable debe adoptar las medidas tecnicas, organizativas y legales necesarias para "
            "garantizar la seguridad de los datos personales. El incumplimiento puede configurar "
            "infraccion grave o muy grave segun el DS 003-2013-JUS."
        ),
    },
    {
        "article": "PDP-ARCO",
        "section_path": "Ley 29733 > Titulo III > Derechos del titular > Derechos ARCO",
        "content": (
            "Ley 29733 — Derechos ARCO del titular de datos personales (Arts. 19-28).\n\n"
            "ACCESO (Art. 19-20): El titular tiene derecho a obtener informacion sobre sus propios "
            "datos personales objeto de tratamiento, el origen de los mismos, las cesiones realizadas "
            "o previstas, y la finalidad del tratamiento. La respuesta debe brindarse dentro de los "
            "20 dias habiles de presentada la solicitud. El ejercicio del derecho es gratuito la "
            "primera vez en cada periodo de doce meses.\n\n"
            "RECTIFICACION (Art. 21): El titular puede solicitar la rectificacion de sus datos "
            "personales que resulten ser parciales, inexactos, incompletos, equivocos o desactualizados. "
            "Plazo de atencion: 20 dias habiles.\n\n"
            "CANCELACION (Art. 22-23): El titular puede solicitar la supresion o cancelacion de datos "
            "cuando hayan dejado de ser necesarios para la finalidad que motivo su recopilacion, cuando "
            "expire el plazo de tratamiento, cuando se revoque el consentimiento, o cuando el "
            "tratamiento sea ilicito. El responsable debe bloquear los datos y luego suprimirlos. "
            "Plazo: 20 dias habiles.\n\n"
            "OPOSICION (Art. 24-25): El titular puede oponerse al tratamiento de sus datos cuando no "
            "hubiera prestado consentimiento o cuando el responsable pretenda tratarlos para una "
            "finalidad de publicidad o prospection comercial, o cuando exista causa legitima y "
            "fundada.\n\n"
            "Procedimiento de reclamo: Si el responsable no atiende la solicitud ARCO, el titular "
            "puede interponer reclamo ante la ANPDP dentro de los 15 dias habiles siguientes al "
            "vencimiento del plazo o de la negativa."
        ),
    },
    {
        "article": "PDP-SENSIBLES",
        "section_path": "Ley 29733 > Titulo II > Art. 13 > Tratamiento de datos sensibles",
        "content": (
            "Ley 29733 — Tratamiento de datos sensibles (Art. 13) y DS 003-2013-JUS (Art. 9-10).\n\n"
            "Son datos sensibles aquellos que afectan la intimidad de su titular o cuyo uso indebido "
            "puede generar discriminacion. Se consideran datos sensibles:\n"
            "- Datos de origen racial o etnico.\n"
            "- Ingresos economicos.\n"
            "- Opiniones o convicciones politicas, religiosas, filosoficas o morales.\n"
            "- Afiliacion sindical.\n"
            "- Informacion relacionada con la salud o la vida sexual.\n"
            "- Datos biometricos.\n\n"
            "Regla general: Los datos sensibles solo pueden ser objeto de tratamiento con el "
            "consentimiento expreso y escrito del titular o cuando una ley lo autorice.\n\n"
            "Excepciones al consentimiento para datos de salud:\n"
            "a) Tratamiento necesario para la prevencion o para el diagnostico medico.\n"
            "b) Prestacion de asistencia sanitaria o tratamiento medico.\n"
            "c) Gestion de servicios sanitarios, siempre que sean tratados por un profesional "
            "sanitario sujeto al secreto profesional.\n\n"
            "Prohibicion: Queda prohibido crear bancos de datos que contengan datos sensibles, "
            "salvo que sea necesario para la consecucion de los fines legitimos, concretos y "
            "acorde con las actividades y objeto del responsable.\n\n"
            "Infraccion muy grave: Tratar datos sensibles sin autorizacion o en contravention de "
            "las disposiciones de la ley supone infraccion muy grave sancionable con hasta 100 UIT."
        ),
    },
    {
        "article": "PDP-FLUJO",
        "section_path": "Ley 29733 > Titulo VI > Flujo transfronterizo de datos personales",
        "content": (
            "Ley 29733 — Flujo transfronterizo de datos personales (Arts. 36-39) y "
            "DS 003-2013-JUS (Arts. 75-82).\n\n"
            "El flujo transfronterizo de datos personales esta condicionado a que el pais "
            "destinatario cuente con un nivel de proteccion adecuado. Se entiende que existe nivel "
            "adecuado cuando el pais receptor cuente con legislacion que garantice los mismos "
            "derechos reconocidos por la Ley 29733.\n\n"
            "Excepciones al requisito de nivel adecuado (Art. 37):\n"
            "a) Cuando el titular de los datos haya prestado su consentimiento expreso e inequivoco.\n"
            "b) Cuando sea necesario para la ejecucion de un contrato entre el titular y el responsable.\n"
            "c) Cuando sea necesario para la ejecucion de un contrato celebrado en interes del titular.\n"
            "d) Cuando sea necesario o legalmente exigido por razones de interes publico importante.\n"
            "e) Cuando sea necesario para el establecimiento, ejercicio o defensa de una reclamacion "
            "judicial o administrativa.\n"
            "f) Cuando sea necesario para la proteccion de un interes vital del titular.\n\n"
            "Clausulas contractuales tipo: Como mecanismo alternativo al nivel de proteccion adecuado, "
            "el responsable puede celebrar contratos con el destinatario extranjero que garanticen "
            "un nivel de proteccion equivalente al de la ley peruana.\n\n"
            "La ANPDP puede suspender el flujo transfronterizo si verifica que el nivel de proteccion "
            "del pais receptor es insuficiente o que se han producido violaciones a los derechos de "
            "los titulares peruanos."
        ),
    },
    {
        "article": "PDP-ANPDP-SANCIONES",
        "section_path": "Ley 29733 > Titulo VIII > ANPDP > Infracciones y sanciones",
        "content": (
            "Ley 29733 — ANPDP e infracciones y sanciones (Arts. 40-47) y DS 003-2013-JUS "
            "(Arts. 96-116).\n\n"
            "AUTORIDAD NACIONAL DE PROTECCION DE DATOS PERSONALES (ANPDP): Es la autoridad "
            "competente del Ministerio de Justicia y Derechos Humanos (MINJUSDH) encargada de "
            "velar por el cumplimiento de la Ley 29733. Sus funciones incluyen:\n"
            "- Tramitar reclamaciones y denuncias de los titulares.\n"
            "- Fiscalizar el cumplimiento de la ley.\n"
            "- Imponer sanciones administrativas.\n"
            "- Llevar el Registro Nacional de Proteccion de Datos Personales.\n\n"
            "CLASIFICACION DE INFRACCIONES:\n\n"
            "Infracciones leves (multa: 0.5 a 5 UIT):\n"
            "- No cumplir con el deber de informacion al titular.\n"
            "- No atender las solicitudes ARCO en el plazo legal.\n"
            "- No inscribir el banco de datos ante la ANPDP.\n\n"
            "Infracciones graves (multa: 5 a 50 UIT):\n"
            "- Tratar datos sin consentimiento del titular (salvo excepciones legales).\n"
            "- Tratar datos para finalidad distinta a la declarada.\n"
            "- No adoptar medidas de seguridad adecuadas.\n"
            "- Obstaculizar el ejercicio de los derechos ARCO.\n\n"
            "Infracciones muy graves (multa: 50 a 100 UIT):\n"
            "- Tratar datos sensibles sin autorizacion.\n"
            "- Realizar flujo transfronterizo sin nivel de proteccion adecuado.\n"
            "- Reincidencia en infraccion grave.\n"
            "- Violar secreto o confidencialidad de los datos.\n\n"
            "El DS 016-2024-JUS actualiza las multas y refuerza la competencia fiscalizadora de la ANPDP."
        ),
    },
    {
        "article": "PDP-REGLAMENTO",
        "section_path": "DS 003-2013-JUS > Reglamento Ley 29733 > Obligaciones responsable banco de datos",
        "content": (
            "DS 003-2013-JUS — Reglamento de la Ley 29733. Obligaciones del titular del banco de "
            "datos personales (Arts. 36-55).\n\n"
            "1. INSCRIPCION ANTE LA ANPDP: Todo banco de datos debe inscribirse en el Registro "
            "Nacional de Proteccion de Datos Personales antes de iniciar el tratamiento. "
            "La inscripcion es anual y debe actualizarse cuando cambie el tipo de datos o la finalidad.\n\n"
            "2. POLITICA DE PRIVACIDAD: El responsable debe contar con una politica de tratamiento "
            "de datos personales accesible a los titulares, que incluya: identidad del responsable, "
            "finalidad, derechos del titular, transferencias previstas y medidas de seguridad.\n\n"
            "3. MEDIDAS DE SEGURIDAD (Art. 39): El nivel de seguridad minimo exigido varia segun la "
            "sensibilidad de los datos:\n"
            "   - Nivel basico: datos generales de identificacion.\n"
            "   - Nivel intermedio: datos economicos, financieros, credito.\n"
            "   - Nivel alto: datos sensibles (salud, biometricos, etc.).\n\n"
            "4. CONTRATOS CON ENCARGADOS DEL TRATAMIENTO: Cuando el tratamiento se encargue a un "
            "tercero (outsourcing), debe celebrarse un contrato que obligue al encargado a aplicar "
            "las medidas de seguridad y a no usar los datos para finalidad distinta.\n\n"
            "5. REGISTRO DE INCIDENTES: El responsable debe llevar un registro interno de violaciones "
            "de seguridad que afecten datos personales. Si la brecha implica riesgo para los titulares, "
            "debe notificarse a la ANPDP en el plazo establecido por la norma."
        ),
    },
    # =========================================================
    # PREVENCION DE LAVADO DE ACTIVOS — LEY 27693 Y DL 1106
    # =========================================================
    {
        "article": "LAF-UIF-CREACION",
        "section_path": "Ley 27693 > Creacion UIF-Peru > Objeto y funciones",
        "content": (
            "Ley 27693 — Ley que crea la Unidad de Inteligencia Financiera del Peru (UIF-Peru), "
            "modificada por Ley 28009 y Ley 29038.\n\n"
            "La UIF-Peru es la Unidad de Inteligencia Financiera del Peru, organismo con autonomia "
            "funcional, tecnica y administrativa, adscrita a la Superintendencia de Banca, Seguros "
            "y AFP (SBS). Fue creada mediante Ley 27693 de abril de 2002.\n\n"
            "OBJETO: Recibir, analizar y transmitir informacion para detectar el lavado de activos "
            "y el financiamiento del terrorismo (LAFT).\n\n"
            "FUNCIONES PRINCIPALES (Art. 3):\n"
            "- Recibir y analizar los Reportes de Operaciones Sospechosas (ROS) de los sujetos obligados.\n"
            "- Recibir los registros de operaciones en efectivo y otras operaciones reguladas.\n"
            "- Solicitar y obtener de los sujetos obligados informacion adicional sobre operaciones reportadas.\n"
            "- Comunicar al Ministerio Publico los indicios de lavado de activos o financiamiento del terrorismo.\n"
            "- Intercambiar informacion con unidades de inteligencia financiera de otros paises.\n"
            "- Emitir las normas de su competencia e imponer sanciones administrativas.\n\n"
            "BASE LEGAL COMPLEMENTARIA:\n"
            "- DL 1106 (2012): Lucha eficaz contra el lavado de activos.\n"
            "- DL 1249 (2016): Medidas para fortalecer la prevencion y deteccion del LAFT.\n"
            "- DS 020-2017-JUS: Reglamento de la Ley 27693."
        ),
    },
    {
        "article": "LAF-SUJETOS-OBLIGADOS",
        "section_path": "Ley 27693 > Titulo II > Sujetos obligados > Registro y reporte",
        "content": (
            "Ley 27693 y Reglamento DS 020-2017-JUS — Sujetos obligados a informar a la UIF-Peru.\n\n"
            "Son sujetos obligados las personas naturales y juridicas que por la naturaleza de su "
            "actividad pueden ser utilizadas como vehiculo para el lavado de activos. Se clasifican en:\n\n"
            "SECTOR FINANCIERO REGULADO POR SBS:\n"
            "- Empresas del sistema financiero (bancos, financieras, cajas municipales, cajas rurales).\n"
            "- Empresas del sistema de seguros y AFP.\n"
            "- Cooperativas de ahorro y credito.\n"
            "- Empresas de transferencia de fondos y cambio de moneda.\n\n"
            "SECTOR NO FINANCIERO:\n"
            "- Notarios publicos.\n"
            "- Agentes inmobiliarios y constructoras de inmuebles.\n"
            "- Comerciantes de joyas, metales preciosos, piedras preciosas y obras de arte.\n"
            "- Casinos, salas de juego, hipodromos y similares.\n"
            "- Empresas de servicios de custodia, traslado y administracion de efectivo.\n"
            "- Administradores de fondos colectivos.\n"
            "- Personas naturales o juridicas que presten servicios de contabilidad o auditoria.\n"
            "- Abogados que intervengan en determinadas operaciones (compra-venta inmuebles, "
            "constitucion de sociedades, administracion de fondos).\n\n"
            "OBLIGACIONES GENERALES DE LOS SUJETOS OBLIGADOS:\n"
            "1. Registrar las operaciones en efectivo iguales o superiores a US$ 10,000 o equivalente.\n"
            "2. Reportar Operaciones Sospechosas (ROS) a la UIF-Peru dentro de los 30 dias de detectadas.\n"
            "3. Implementar un Sistema de Prevencion LAFT con Manual aprobado.\n"
            "4. Designar un Oficial de Cumplimiento.\n"
            "5. Conservar los registros y documentos por 10 anos."
        ),
    },
    {
        "article": "LAF-OFICIAL-CUMPLIMIENTO",
        "section_path": "Ley 27693 > Titulo II > Oficial de Cumplimiento > Funciones y requisitos",
        "content": (
            "Ley 27693 y DS 020-2017-JUS — Oficial de Cumplimiento.\n\n"
            "El Oficial de Cumplimiento es la persona responsable de velar por la implementacion "
            "y funcionamiento del Sistema de Prevencion LAFT dentro de la organizacion.\n\n"
            "REQUISITOS PARA SER OFICIAL DE CUMPLIMIENTO:\n"
            "- Ser funcionario o directivo de la empresa (cargo gerencial o directivo).\n"
            "- Conocimientos en prevencion de LAFT (certificaciones como CAMS son valoradas).\n"
            "- En el sector financiero: acreditarse ante la SBS dentro de los 30 dias de designacion.\n"
            "- En sujetos obligados no financieros: inscribirse en el Registro de Oficiales de "
            "Cumplimiento de la UIF-Peru.\n\n"
            "FUNCIONES PRINCIPALES (Art. 10 DS 020-2017-JUS):\n"
            "1. Verificar la adecuada aplicacion del Manual LAFT y las politicas internas.\n"
            "2. Revisar las operaciones registradas para detectar senales de alerta.\n"
            "3. Formular el ROS y remitirlo a la UIF-Peru cuando corresponda.\n"
            "4. Coordinar con la UIF-Peru y con las autoridades en investigaciones.\n"
            "5. Capacitar al personal en la prevencion de LAFT.\n"
            "6. Presentar informes periodicos al directorio u organo equivalente.\n"
            "7. Aplicar el programa de conocimiento del cliente (KYC) y due diligence.\n\n"
            "RESPONSABILIDAD: El Oficial de Cumplimiento puede incurrir en responsabilidad "
            "administrativa si omite reportar operaciones sospechosas detectadas o si las reporta "
            "de manera deficiente. Las sanciones administrativas de la SBS o UIF-Peru pueden "
            "incluir amonestacion, multa e inhabilitacion."
        ),
    },
    {
        "article": "LAF-DL1106-TIPOS-PENALES",
        "section_path": "DL 1106 > Titulo I > Articulos 1-6 > Tipos penales de lavado de activos",
        "content": (
            "DL 1106 — Decreto Legislativo de Lucha Eficaz contra el Lavado de Activos y otros "
            "delitos relacionados a la mineria ilegal y crimen organizado (2012).\n\n"
            "TIPOS PENALES PRINCIPALES:\n\n"
            "Art. 1 — Actos de conversion y transferencia: El que convierte o transfiere dinero, "
            "bienes, efectos o ganancias cuyo origen ilicito conoce o debia presumir, con la "
            "finalidad de evitar la identificacion de su origen, incautacion o decomiso, sera "
            "reprimido con pena privativa de libertad no menor de 8 ni mayor de 15 anos y con "
            "120 a 350 dias-multa.\n\n"
            "Art. 2 — Actos de ocultamiento y tenencia: El que adquiere, utiliza, guarda, "
            "administra, custodia, recibe, oculta o mantiene en su poder dinero, bienes, efectos "
            "o ganancias de origen ilicito, sera reprimido con igual pena.\n\n"
            "Art. 3 — Transporte, traslado, ingreso o salida de dinero: El que transporta o "
            "traslada dentro del territorio nacional, o hace ingresar o salir del pais, dinero "
            "en efectivo o instrumentos de pago al portador de origen ilicito, "
            "sera sancionado con pena no menor de 8 ni mayor de 15 anos.\n\n"
            "CIRCUNSTANCIAS AGRAVANTES (Art. 4): La pena se incrementa hasta 25 anos cuando:\n"
            "- El agente utiliza su condicion de funcionario publico.\n"
            "- El agente es miembro de una organizacion criminal.\n"
            "- El valor del dinero o bienes supera las 500 UIT.\n\n"
            "AUTONOMIA DEL DELITO (Art. 10): El lavado de activos es un delito autonomo. No se "
            "requiere que los delitos precedentes hayan sido investigados, procesados, denunciados "
            "ni condenados. Basta que el agente conozca o deba presumir el origen ilicito del bien.\n\n"
            "CARGA DE LA PRUEBA: Corresponde al agente del delito demostrar el origen licito del "
            "dinero, bienes, efectos o ganancias objeto del delito."
        ),
    },
    {
        "article": "LAF-KYC",
        "section_path": "DS 020-2017-JUS > Capitulo III > Debida diligencia > KYC",
        "content": (
            "DS 020-2017-JUS — Debida diligencia en el conocimiento del cliente (KYC).\n\n"
            "DEBIDA DILIGENCIA NORMAL: Los sujetos obligados deben aplicar medidas de debida "
            "diligencia para identificar y verificar la identidad de sus clientes antes de "
            "establecer la relacion comercial o ejecutar operaciones ocasionales a partir de "
            "montos determinados por la SBS o UIF-Peru segun el sector.\n\n"
            "Medidas de debida diligencia normal incluyen:\n"
            "- Identificacion del cliente: nombre, documento de identidad, actividad economica, "
            "domicilio, telefono.\n"
            "- Identificacion del beneficiario final (UBO — Ultimate Beneficial Owner): persona "
            "natural que en ultima instancia posee o controla al cliente (participacion igual o "
            "superior al 25%).\n"
            "- Comprension del proposito y la naturaleza de la relacion comercial.\n\n"
            "DEBIDA DILIGENCIA REFORZADA: Se aplica a clientes de alto riesgo:\n"
            "- Personas Expuestas Politicamente (PEP): funcionarios, ex funcionarios publicos y "
            "sus familiares hasta segundo grado.\n"
            "- Clientes de paises de alto riesgo o jurisdicciones no cooperantes (lista GAFI).\n"
            "- Personas juridicas en regimenes de baja o nula imposicion tributaria.\n"
            "- Operaciones complejas o inusualmente grandes sin justificacion economica aparente.\n\n"
            "DEBIDA DILIGENCIA SIMPLIFICADA: Puede aplicarse a clientes de bajo riesgo "
            "(entidades publicas peruanas, empresas listadas en bolsas reguladas).\n\n"
            "Actualizacion periodica: Los expedientes KYC deben actualizarse al menos cada tres "
            "anos para clientes de riesgo alto, y cada cinco anos para los demas."
        ),
    },
    # =========================================================
    # ANTICORRUPCION Y COMPLIANCE CORPORATIVO — LEY 30424
    # =========================================================
    {
        "article": "C30424-RESPONSABILIDAD",
        "section_path": "Ley 30424 > Titulo I > Articulos 1-3 > Responsabilidad de personas juridicas",
        "content": (
            "Ley 30424 — Ley que regula la responsabilidad administrativa de las personas juridicas "
            "por el delito de cohecho activo transnacional (2016), modificada por DL 1352 (2017) "
            "y Ley 31740 (2023).\n\n"
            "AMBITO DE APLICACION: Las personas juridicas de derecho privado, incluyendo las "
            "empresas del Estado, pueden ser declaradas responsables administrativamente cuando "
            "alguna de las siguientes personas cometa un delito en su beneficio o por su cuenta:\n"
            "a) Sus socios, directores, administradores, representantes legales o apoderados.\n"
            "b) Personas que actuan bajo la autoridad y control de las anteriores.\n\n"
            "DELITOS COMPRENDIDOS (ampliados por DL 1352 y Ley 31740):\n"
            "- Cohecho activo transnacional (Art. 397-A CP).\n"
            "- Cohecho activo generico (Art. 397 CP).\n"
            "- Cohecho activo especifico (Art. 398 CP).\n"
            "- Lavado de activos (DL 1106).\n"
            "- Financiamiento del terrorismo (Art. 4-A LCT).\n"
            "- Colusión (Art. 384 CP).\n"
            "- Trafico de influencias (Art. 400 CP).\n"
            "- Enriquecimiento ilicito (Art. 401 CP).\n"
            "- Defraudacion tributaria (Ley 27038, modificada).\n\n"
            "RESPONSABILIDAD AUTONOMA: La responsabilidad de la persona juridica es autonoma e "
            "independiente de la responsabilidad penal de las personas naturales. Puede declararse "
            "su responsabilidad aunque el autor del delito haya fallecido o se haya sustraido a "
            "la accion de la justicia."
        ),
    },
    {
        "article": "C30424-MODELO-PREVENCION",
        "section_path": "Ley 30424 > Titulo II > Articulos 17-24 > Modelo de prevencion",
        "content": (
            "Ley 30424 — Modelo de prevencion (Compliance Program) como eximente y atenuante "
            "de responsabilidad (Arts. 17-24).\n\n"
            "EXENCION DE RESPONSABILIDAD: La persona juridica queda exenta de responsabilidad "
            "administrativa si, antes de la comision del delito, habia adoptado e implementado "
            "un modelo de prevencion con los siguientes elementos minimos:\n\n"
            "1. PERSONA U ORGANO A CARGO DE LA PREVENCION: Designacion de un encargado de "
            "prevencion o un organo colegiado (comite de compliance), con autonomia funcional "
            "y recursos suficientes. Rinde cuentas directamente al directorio.\n\n"
            "2. IDENTIFICACION, EVALUACION Y MITIGACION DE RIESGOS: Mapeo de los riesgos de "
            "comision de los delitos comprendidos en la ley, considerando sector, tamano, "
            "actividades y paises donde opera la empresa.\n\n"
            "3. PROCEDIMIENTOS DE SUPERVISION, MONITOREO Y AUDITORIA: Mecanismos que permitan "
            "verificar la efectividad del modelo de prevencion, con auditorias periodicas "
            "internas y/o externas.\n\n"
            "4. CANAL DE DENUNCIAS: Mecanismo interno para que empleados y terceros puedan "
            "denunciar, de manera confidencial y sin represalia, los actos presuntamente "
            "delictivos o las vulneraciones al modelo.\n\n"
            "5. DIFUSION Y CAPACITACION: Programa de difusion y capacitacion del modelo entre "
            "todos los integrantes de la organizacion.\n\n"
            "6. EVALUACION Y MONITOREO CONTINUO: El modelo debe ser evaluado, monitoreado y "
            "actualizado periodicamente para adaptarse a los cambios en los riesgos.\n\n"
            "ATENUANTE: Si el modelo existia pero fue insuficiente o no totalmente implementado, "
            "opera como circunstancia atenuante de responsabilidad, reduciendo la sancion.\n\n"
            "CERTIFICACION SMV: La Superintendencia del Mercado de Valores (SMV) certifica la "
            "idoneidad del modelo de prevencion a solicitud de las personas juridicas."
        ),
    },
    {
        "article": "C30424-SANCIONES",
        "section_path": "Ley 30424 > Titulo III > Articulos 5-11 > Sanciones a personas juridicas",
        "content": (
            "Ley 30424 — Sanciones administrativas aplicables a personas juridicas (Arts. 5-11).\n\n"
            "TIPOS DE SANCIONES:\n\n"
            "1. MULTA: De 2 UIT a 10,000 UIT. El juez penal determina el monto considerando:\n"
            "   - La gravedad de la conducta ilicita.\n"
            "   - Las consecuencias de la conducta para la sociedad y el mercado.\n"
            "   - El beneficio obtenido o esperado por la persona juridica.\n"
            "   - La capacidad economica de la persona juridica.\n"
            "   - La existencia de un modelo de prevencion (atenuante o eximente).\n\n"
            "2. INHABILITACION: Desde 6 meses hasta 5 anos para:\n"
            "   - Contratar con el Estado.\n"
            "   - Recibir subsidios, subvenciones, donaciones del Estado.\n"
            "   - Gozar de beneficios o incentivos tributarios.\n"
            "   - Participar en concesiones mineras, de hidrocarburos u otras.\n\n"
            "3. SUSPENSION DE ACTIVIDADES SOCIALES: Hasta 2 anos.\n\n"
            "4. DISOLUCION: Cuando la persona juridica fue constituida o se hubiera convertido "
            "en un instrumento para la comision del delito. Es la sancion maxima.\n\n"
            "5. CLAUSURA DE LOCALES O ESTABLECIMIENTOS: Hasta 5 anos.\n\n"
            "CIRCUNSTANCIAS ATENUANTES (Art. 12):\n"
            "- Colaboracion activa con las autoridades.\n"
            "- Haber indemnizado a los perjudicados.\n"
            "- Contar con un modelo de prevencion (aunque insuficiente).\n\n"
            "PROCEDIMIENTO: Las sanciones se imponen en el proceso penal que se tramita contra "
            "la persona natural. El Ministerio Publico incluye a la persona juridica como "
            "sujeto procesal."
        ),
    },
    {
        "article": "C-ISO37001",
        "section_path": "ISO 37001 > Principios > Sistema de gestion antisoborno",
        "content": (
            "ISO 37001 — Sistema de Gestion Antisoborno: aplicacion en el Peru.\n\n"
            "La norma ISO 37001 (publicada en 2016, adoptada en Peru como NTP-ISO 37001:2017) "
            "especifica los requisitos para un sistema de gestion antisoborno. Es la principal "
            "referencia tecnica para implementar el modelo de prevencion exigido por la Ley 30424.\n\n"
            "PRINCIPIOS CLAVE:\n\n"
            "1. LIDERAZGO Y COMPROMISO: El directorio y la alta gerencia deben demostrar liderazgo "
            "y compromiso con el sistema antisoborno, aprobando politicas, asignando recursos y "
            "supervisando resultados.\n\n"
            "2. EVALUACION DE RIESGOS: La organizacion debe evaluar periodicamente los riesgos de "
            "soborno asociados a sus actividades, paises de operacion, socios comerciales y "
            "funcionarios publicos con quienes interactua.\n\n"
            "3. CONTROLES FINANCIEROS Y NO FINANCIEROS: Implementar controles sobre pagos de "
            "facilitacion, regalos y hospitalidad, donaciones, patrocinios, y uso de agentes o "
            "intermediarios.\n\n"
            "4. DEBIDA DILIGENCIA DE SOCIOS DE NEGOCIO: Evaluar a proveedores, distribuidores, "
            "consultores y otros terceros para verificar que no representan riesgo de soborno.\n\n"
            "5. CANAL DE DENUNCIAS E INVESTIGACION: Mecanismo para recibir, proteger y gestionar "
            "denuncias de posibles actos de soborno, con investigacion adecuada.\n\n"
            "DIFERENCIA CON LA LEY 30424: ISO 37001 es mas especifica en lo tecnico (controles "
            "operativos, auditorias, indicadores), mientras que la Ley 30424 establece el marco "
            "legal de responsabilidad. La certificacion ISO 37001 es una prueba de la robustez "
            "del modelo de prevencion ante el Poder Judicial y la Fiscalia."
        ),
    },
    {
        "article": "C-PROGRAMA-COMPLIANCE",
        "section_path": "Compliance Corporativo > Programa integral > Elementos esenciales",
        "content": (
            "Programa de compliance integral en el Peru: elementos esenciales para personas juridicas "
            "bajo el regimen de la Ley 30424 e ISO 37001.\n\n"
            "1. CODIGO DE ETICA Y CONDUCTA: Documento que define los valores, principios y "
            "comportamientos esperados de todos los integrantes de la organizacion. Debe incluir "
            "politicas sobre: conflicto de intereses, regalos y hospitalidad, relacion con "
            "funcionarios publicos, confidencialidad, uso de activos corporativos.\n\n"
            "2. CANAL DE DENUNCIAS (WHISTLEBLOWING): Sistema que permite reportar, de forma "
            "confidencial y anonima si se desea, posibles violaciones al codigo de etica, actos "
            "de corrupcion, fraude o incumplimientos normativos. Debe garantizarse proteccion "
            "contra represalias al denunciante (no retaliation policy).\n\n"
            "3. DUE DILIGENCE DE TERCEROS: Proceso de evaluacion previa a contratar con "
            "proveedores, consultores, agentes y socios estrategicos, para verificar que no "
            "tienen antecedentes de corrupcion, lavado de activos, sanciones OFAC u otras.\n\n"
            "4. POLITICA DE REGALOS Y HOSPITALIDAD: Listas de control de regalos y gastos de "
            "representacion con topes monetarios, prohibicion de regalos a funcionarios publicos "
            "en periodos de licitacion o proceso de contratacion.\n\n"
            "5. CAPACITACION Y COMUNICACION: Programa anual de capacitacion obligatoria para toda "
            "la organizacion, con capacitacion reforzada para areas de riesgo (ventas, compras, "
            "relaciones publicas, financiero).\n\n"
            "6. MONITOREO Y REVISION: Indicadores de eficacia del programa (KPIs de compliance), "
            "auditoria interna periodica, y revision anual por parte del directorio. El encargado "
            "de prevencion debe presentar informes semestrales o anuales al directorio."
        ),
    },
    # =========================================================
    # GOBIERNO CORPORATIVO — CODIGO SMV
    # =========================================================
    {
        "article": "GC-SMV-PRINCIPIOS",
        "section_path": "Codigo Buen Gobierno Corporativo > SMV > Principios generales",
        "content": (
            "Codigo de Buen Gobierno Corporativo para las Sociedades Peruanas (CBGCSP) — "
            "aprobado por Resolucion SMV N° 012-2013-SMV/01 y actualizado por Resolucion SMV "
            "N° 033-2021-SMV/02.\n\n"
            "El CBGCSP es el marco de referencia para el gobierno corporativo de las empresas "
            "peruanas. Se estructura en cinco pilares:\n\n"
            "PILAR I — DERECHOS DE LOS ACCIONISTAS: Garantizar el ejercicio de los derechos "
            "politicos y economicos de todos los accionistas, incluyendo los minoritarios. "
            "Mecanismos de voto, convocatoria a junta con anticipacion suficiente (25 dias), "
            "acceso a informacion previa a la junta.\n\n"
            "PILAR II — JUNTA GENERAL DE ACCIONISTAS: Funciones y competencias exclusivas de "
            "la JGA, quorum calificado para decisiones criticas, proteccion de accionistas "
            "contra acuerdos abusivos.\n\n"
            "PILAR III — EL DIRECTORIO Y LA ALTA GERENCIA: Rol del directorio en la supervision "
            "estrategica, independencia de directores, comites del directorio (auditoria, "
            "riesgos, nombramientos y remuneraciones), separacion del cargo de presidente del "
            "directorio y gerente general.\n\n"
            "PILAR IV — RIESGO Y CUMPLIMIENTO: Marco integral de gestion de riesgos, funcion "
            "de auditoria interna, relacion con el auditor externo, sistema de control interno.\n\n"
            "PILAR V — TRANSPARENCIA E INFORMACION: Politica de informacion, hechos de "
            "importancia, reporte anual de gobierno corporativo, reporte de sostenibilidad.\n\n"
            "CUMPLIMIENTO: Las empresas inscritas en el Registro Publico del Mercado de Valores "
            "deben reportar anualmente mediante el Reporte de Cumplimiento del Codigo de Buen "
            "Gobierno Corporativo (Resolucion SMV N° 033-2021-SMV/02), bajo el principio "
            "cumple o explica (comply or explain)."
        ),
    },
    {
        "article": "GC-DIRECTORIO",
        "section_path": "Codigo Buen Gobierno Corporativo > Pilar III > Directorio > Independencia y comites",
        "content": (
            "CBGCSP — Pilar III: El Directorio y la Alta Gerencia.\n\n"
            "COMPOSICION DEL DIRECTORIO:\n"
            "- Se recomienda que el directorio tenga un numero razonable de directores "
            "independientes (al menos un tercio).\n"
            "- Director independiente: aquel que no tiene relacion alguna con la empresa, "
            "sus accionistas principales o su gestion que pudiera interferir con su juicio. "
            "No puede ser empleado ni exgerente de la empresa (en los ultimos 5 anos), ni "
            "accionista con participacion mayor al 5%.\n\n"
            "COMITE DE AUDITORIA:\n"
            "- Conformado por al menos 3 directores, la mayoria independientes.\n"
            "- Supervisa la integridad de los estados financieros.\n"
            "- Evalua la independencia y competencia del auditor externo.\n"
            "- Supervisa el sistema de control interno y el area de auditoria interna.\n"
            "- Revisa el cumplimiento de las politicas de riesgos.\n\n"
            "COMITE DE RIESGOS:\n"
            "- Apoya al directorio en la supervision del marco de gestion de riesgos.\n"
            "- Revisa el perfil de riesgo de la empresa y los limites de tolerancia.\n\n"
            "COMITE DE NOMBRAMIENTOS Y REMUNERACIONES:\n"
            "- Propone la politica de remuneraciones de directores y alta gerencia.\n"
            "- Evalua la idoneidad de los candidatos a directores.\n\n"
            "AUTOEVALUACION DEL DIRECTORIO: El directorio debe realizar una evaluacion anual "
            "de su desempeno colectivo e individual, que puede ser facilitada por un tercero "
            "externo independiente. Los resultados deben reportarse en el reporte de gobierno "
            "corporativo anual."
        ),
    },
    {
        "article": "GC-TRANSPARENCIA",
        "section_path": "Codigo Buen Gobierno Corporativo > Pilar V > Transparencia > Reporte sostenibilidad",
        "content": (
            "CBGCSP — Pilar V: Transparencia de la informacion y reporte de sostenibilidad.\n\n"
            "POLITICA DE INFORMACION: Las empresas deben contar con una politica de informacion "
            "aprobada por el directorio que regule:\n"
            "- Canales de comunicacion con accionistas, inversores, analistas y publico en general.\n"
            "- Periodos de silencio previos a la divulgacion de resultados financieros.\n"
            "- Procedimiento para la comunicacion de hechos de importancia a la SMV.\n\n"
            "HECHOS DE IMPORTANCIA (SMV): Las empresas inscritas en el Registro Publico del "
            "Mercado de Valores deben comunicar inmediatamente a la SMV cualquier hecho que sea "
            "capaz de influir en las decisiones de inversion: resultados extraordinarios, cambios "
            "en la plana gerencial, fusiones, adquisiciones, litigios significativos, cambios en "
            "la estructura accionaria.\n\n"
            "REPORTE DE SOSTENIBILIDAD (ESG): El CBGCSP recomienda que las empresas publiquen "
            "anualmente un reporte de sostenibilidad siguiendo estandares internacionales como "
            "GRI (Global Reporting Initiative) o SASB. El reporte debe incluir:\n"
            "- Dimension ambiental: huella de carbono, uso de energia y agua, gestion de residuos.\n"
            "- Dimension social: practicas laborales, salud y seguridad, comunidades, derechos humanos.\n"
            "- Dimension de gobernanza: estructura de gobierno corporativo, etica empresarial, "
            "anticorrupcion.\n\n"
            "MEMORIA ANUAL: La memoria anual debe incluir informacion sobre el perfil de riesgos "
            "de la empresa, la estructura de gobierno corporativo y el reporte de cumplimiento del CBGCSP."
        ),
    },
    {
        "article": "GC-CONTROL-INTERNO",
        "section_path": "Codigo Buen Gobierno Corporativo > Pilar IV > Riesgo y Cumplimiento > Control interno",
        "content": (
            "CBGCSP — Pilar IV: Marco integral de riesgos y control interno.\n\n"
            "SISTEMA DE CONTROL INTERNO: El directorio es responsable de establecer un sistema "
            "de control interno efectivo. El modelo de referencia mas utilizado en Peru es el "
            "marco COSO (Committee of Sponsoring Organizations of the Treadway Commission), "
            "que tiene cinco componentes:\n\n"
            "1. AMBIENTE DE CONTROL: Integridad, valores eticos, competencia del personal, "
            "estructura organizacional, asignacion de autoridad y responsabilidad.\n\n"
            "2. EVALUACION DE RIESGOS: Identificacion y analisis de los riesgos relevantes para "
            "el logro de los objetivos, incluyendo riesgos de fraude y corrupcion.\n\n"
            "3. ACTIVIDADES DE CONTROL: Politicas y procedimientos que aseguran que las "
            "instrucciones de la gerencia se llevan a cabo (segregacion de funciones, autorizaciones, "
            "conciliaciones, revisiones de desempeno).\n\n"
            "4. INFORMACION Y COMUNICACION: Los sistemas de informacion permiten capturar y "
            "comunicar los datos necesarios para controlar las operaciones.\n\n"
            "5. ACTIVIDADES DE MONITOREO: Evaluacion continua y periodica de la calidad del "
            "control interno. La auditoria interna es el principal mecanismo de monitoreo.\n\n"
            "AUDITORIA INTERNA: Debe ser independiente de las areas operativas, reportando "
            "directamente al comite de auditoria. Sus funciones incluyen evaluar la eficacia del "
            "control interno, la gestion de riesgos y el gobierno corporativo, en conformidad "
            "con las Normas Internacionales para el Ejercicio Profesional de la Auditoria Interna "
            "(NIEPAI) del IIA (Institute of Internal Auditors)."
        ),
    },
]
