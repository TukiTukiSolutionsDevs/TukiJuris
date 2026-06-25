"""
Seed: Derecho Notarial (Perú).

Núcleo normativo:
    - DL 1049 — Ley del Notariado y su Reglamento DS 010-2010-JUS
    - Ley 26662 — Competencia notarial en asuntos no contenciosos
    - Ley 27157 — Regularización de edificaciones y prescripción notarial
    - Ley 29560 — Modifica Ley 26662 (unión de hecho notarial)
"""

NOTARIAL_ARTICLES = [
    {
        "article": "DL-1049-A1",
        "section_path": "DL 1049 > Función notarial",
        "content": (
            "Artículos 1-3 DL 1049 — Función notarial.\n"
            "El notario es el profesional del derecho que está autorizado para dar fe "
            "pública de los actos y contratos que ante él se celebran. Formaliza la voluntad "
            "de los otorgantes, redactando los instrumentos a los que confiere autenticidad.\n\n"
            "CARACTERES DEL NOTARIO:\n"
            "1. Profesional del derecho (abogado titulado).\n"
            "2. Investido de fe pública por el Estado.\n"
            "3. Imparcial: actúa para asesorar a TODAS las partes intervinientes.\n"
            "4. Discreto: deber de secreto profesional.\n"
            "5. Inamovible en su oficio dentro de su distrito notarial salvo causales legales.\n\n"
            "FUNCIONES PRINCIPALES:\n"
            "- Autorización de instrumentos protocolares y extra-protocolares.\n"
            "- Custodia del protocolo notarial.\n"
            "- Tramitación de asuntos no contenciosos (Ley 26662).\n"
            "- Comprobación de hechos materiales (actas)."
        ),
    },
    {
        "article": "Escritura-Publica",
        "section_path": "DL 1049 > Escritura pública",
        "content": (
            "Artículos 51-67 DL 1049 — Escritura pública.\n"
            "Es el instrumento PROTOCOLAR matriz que el notario incorpora a su protocolo, "
            "contiene los actos jurídicos manifestados por los comparecientes con la fe "
            "pública del notario.\n\n"
            "ESTRUCTURA:\n"
            "1. INTRODUCCIÓN: lugar y fecha, identificación del notario y comparecientes "
            "(documento de identidad, estado civil, ocupación, domicilio).\n"
            "2. CUERPO: minuta (acto jurídico) redactada y firmada por abogado colegiado.\n"
            "3. CONCLUSIÓN: lectura, conformidad, observaciones y firma de comparecientes + "
            "notario (firma + signo + sello).\n\n"
            "MINUTA: documento privado autorizado por abogado colegiado que se eleva a "
            "escritura pública. Exigida para actos sobre bienes inmuebles, contratos por "
            "encima de 4 UIT, constitución de sociedades, etc.\n\n"
            "TESTIMONIO: copia literal del original obrante en el protocolo, expedida por el "
            "notario con su firma, sello y fe pública. Sirve para inscripción registral y "
            "para acreditar el acto frente a terceros."
        ),
    },
    {
        "article": "Acta-Notarial",
        "section_path": "DL 1049 > Acta notarial",
        "content": (
            "Artículos 94-99 DL 1049 — Actas notariales.\n"
            "Instrumento PROTOCOLAR mediante el cual el notario, a solicitud de parte, da fe "
            "de los actos, hechos o circunstancias que presencia o le constan personalmente.\n\n"
            "TIPOS DE ACTAS:\n"
            "1. Acta de protocolización: incorpora documentos privados al protocolo notarial.\n"
            "2. Acta de presencia: el notario constata hechos materiales (estado de un bien, "
            "ocurrencia de un evento, recepción/entrega).\n"
            "3. Acta de notoriedad: declara un hecho público y notorio basado en testimonio "
            "de testigos calificados.\n"
            "4. Acta de comprobación de identidad.\n"
            "5. Acta de subasta notarial.\n\n"
            "VALOR PROBATORIO: el acta otorga PLENA PRUEBA del hecho narrado por el notario "
            "respecto de lo presenciado, salvo prueba en contrario por falsedad."
        ),
    },
    {
        "article": "Carta-Notarial",
        "section_path": "DL 1049 > Carta notarial",
        "content": (
            "Artículos 100-102 DL 1049 — Carta notarial.\n"
            "Instrumento EXTRA-PROTOCOLAR a través del cual el notario diligencia el envío "
            "de un mensaje del remitente al destinatario, dejando constancia de la fecha de "
            "entrega y de su contenido.\n\n"
            "EFECTOS LEGALES TÍPICOS:\n"
            "- Constitución en mora (Art. 1333 CC).\n"
            "- Resolución contractual por incumplimiento (Art. 1429 CC — preaviso 15 días).\n"
            "- Interrupción de la prescripción (Art. 1996 CC).\n"
            "- Comunicación de intención de no renovar contrato.\n"
            "- Comunicación de hechos para fines de responsabilidad.\n\n"
            "DILIGENCIAMIENTO:\n"
            "1. El remitente entrega la carta al notario por triplicado.\n"
            "2. El notario certifica la fecha de recepción y entrega un ejemplar.\n"
            "3. Diligencia la entrega al destinatario en su domicilio o lo notifica por "
            "publicación si se desconoce su paradero.\n"
            "4. Devuelve al remitente el cargo con la constancia de entrega o de su negativa."
        ),
    },
    {
        "article": "Ley-26662-Asuntos-No-Contenciosos",
        "section_path": "Ley 26662 > Asuntos no contenciosos",
        "content": (
            "Ley 26662 (1996) — Competencia notarial en asuntos no contenciosos.\n"
            "Otorga competencia AL NOTARIO Y AL JUEZ (a opción del solicitante) para conocer "
            "asuntos sin controversia litigiosa.\n\n"
            "ASUNTOS COMPETENCIA NOTARIAL:\n"
            "1. Rectificación de partidas registrales (nombres, fechas, errores materiales).\n"
            "2. Adopción de personas mayores de edad (Art. 21 Ley 26662).\n"
            "3. Patrimonio familiar (constitución y modificación).\n"
            "4. Inventarios.\n"
            "5. Comprobación de testamentos cerrados u ológrafos (apertura).\n"
            "6. Sucesión intestada (declaración de herederos).\n"
            "7. Separación convencional y divorcio ulterior (modificada por Ley 29227).\n"
            "8. Reconocimiento de unión de hecho (Ley 29560).\n"
            "9. Prescripción adquisitiva notarial de inmuebles (Ley 27157).\n"
            "10. Convocatoria a junta de acreedores en concursos privados.\n\n"
            "TRÁMITE: solicitud escrita firmada por abogado + recaudos exigidos. El notario "
            "publica el aviso (uno o dos veces según el asunto) y al no haber oposición declara "
            "lo solicitado mediante acta o escritura. Si hay oposición, debe remitirse al PJ."
        ),
    },
    {
        "article": "Sucesion-Intestada-Notarial",
        "section_path": "Ley 26662 > Sucesión intestada",
        "content": (
            "Artículos 38-44 Ley 26662 — Sucesión intestada notarial.\n"
            "Procede cuando el causante falleció SIN HABER OTORGADO TESTAMENTO o cuando el "
            "testamento es nulo o caducó.\n\n"
            "REQUISITOS DE LA SOLICITUD:\n"
            "1. Partida de defunción del causante.\n"
            "2. Partidas que acrediten el parentesco de los solicitantes con el causante.\n"
            "3. Documento de identidad de los herederos.\n"
            "4. Declaración de la inexistencia de testamento.\n"
            "5. Indicación de los bienes que conforman la masa hereditaria (referencial).\n\n"
            "TRÁMITE:\n"
            "1. Solicitud firmada por abogado al notario del último domicilio del causante.\n"
            "2. El notario publica avisos en El Peruano y en un diario de mayor circulación "
            "del lugar (2 publicaciones espaciadas).\n"
            "3. Si en 15 días desde la última publicación no hay oposición, el notario emite "
            "ACTA NOTARIAL declarando a los herederos.\n"
            "4. Inscripción de la sucesión en SUNARP — Registro Personal."
        ),
    },
    {
        "article": "Prescripcion-Adquisitiva-Notarial",
        "section_path": "Ley 27157 > Prescripción adquisitiva notarial",
        "content": (
            "Ley 27157 (1999) + DS 035-2006-VIVIENDA — Prescripción adquisitiva notarial.\n"
            "Procede ante notario público respecto de INMUEBLES URBANOS cuando el "
            "solicitante ha poseído el bien en forma:\n"
            "1. CONTINUA: sin interrupciones.\n"
            "2. PACÍFICA: sin violencia.\n"
            "3. PÚBLICA: a la vista de todos.\n"
            "4. COMO PROPIETARIO: con ánimo de dueño (animus domini).\n"
            "Por un plazo de 10 AÑOS (prescripción larga) o 5 AÑOS si la posesión se ha "
            "ejercido con justo título y buena fe (prescripción corta).\n\n"
            "REQUISITOS DE LA SOLICITUD:\n"
            "1. Plano perimétrico y de ubicación visados por la municipalidad.\n"
            "2. Memoria descriptiva.\n"
            "3. Certificado registral inmobiliario.\n"
            "4. Declaración jurada de los colindantes reconociendo la posesión.\n"
            "5. Declaraciones de 3 testigos sobre los años de posesión.\n\n"
            "TRÁMITE: el notario realiza inspección ocular, publica avisos (Peruano + diario "
            "local), notifica a los colindantes. Sin oposición en 25 días, declara la "
            "prescripción mediante escritura pública. Si hay oposición se remite al PJ.\n\n"
            "Solo procede para inmuebles URBANOS — los rurales se rigen por la Ley 28685 "
            "(formalización rural ante COFOPRI / municipalidades)."
        ),
    },
    {
        "article": "Divorcio-Notarial",
        "section_path": "Ley 29227 > Divorcio notarial",
        "content": (
            "Ley 29227 (2008) — Divorcio rápido municipal o notarial.\n"
            "Permite tramitar el divorcio ulterior tras separación convencional ante "
            "ALCALDE PROVINCIAL o NOTARIO PÚBLICO del último domicilio conyugal.\n\n"
            "REQUISITOS:\n"
            "1. Matrimonio civil con MÍNIMO 2 AÑOS de antigüedad.\n"
            "2. NO TENER HIJOS MENORES DE EDAD ni mayores con incapacidad.\n"
            "3. NO TENER BIENES SUJETOS A SOCIEDAD DE GANANCIALES que liquidar — o tener "
            "liquidación previa por escritura pública.\n"
            "4. Mutuo acuerdo expresado en solicitud conjunta firmada por ambos cónyuges + "
            "abogado.\n\n"
            "TRÁMITE:\n"
            "1. Presentación de la solicitud al notario o alcalde.\n"
            "2. Audiencia única de ratificación (15 días desde la solicitud).\n"
            "3. Resolución de SEPARACIÓN CONVENCIONAL inscrita en RENIEC.\n"
            "4. Transcurridos 2 MESES desde la separación, cualquiera de los cónyuges solicita "
            "la DISOLUCIÓN DEL VÍNCULO MATRIMONIAL.\n"
            "5. El notario/alcalde emite el acta de divorcio, inscribible en RENIEC."
        ),
    },
    {
        "article": "Union-Hecho-Notarial",
        "section_path": "Ley 29560 > Unión de hecho notarial",
        "content": (
            "Ley 29560 (2010) — Reconocimiento notarial de la unión de hecho.\n"
            "Modifica la Ley 26662 incorporando la unión de hecho como asunto no contencioso "
            "de competencia notarial.\n\n"
            "REQUISITOS:\n"
            "1. Convivencia continua, pública y notoria por al menos 2 AÑOS continuos.\n"
            "2. Ausencia de impedimento matrimonial entre los convivientes.\n"
            "3. Solicitud conjunta de ambos convivientes con abogado.\n\n"
            "ACREDITACIÓN:\n"
            "- Declaración jurada de los convivientes.\n"
            "- Declaración de DOS TESTIGOS sobre la convivencia.\n"
            "- Documentos que acrediten la relación: hijos comunes, contratos, partidas, "
            "fotos, recibos de servicios a nombre de ambos.\n\n"
            "TRÁMITE:\n"
            "1. El notario publica avisos en El Peruano y diario local.\n"
            "2. Transcurridos 15 días sin oposición, declara la unión de hecho mediante "
            "ESCRITURA PÚBLICA.\n"
            "3. Inscripción en SUNARP — Registro Personal.\n\n"
            "EFECTOS: la unión de hecho reconocida origina régimen de sociedad de gananciales "
            "(Art. 326 CC) y produce los efectos sucesorios del cónyuge (jurisprudencia TC)."
        ),
    },
    {
        "article": "Protocolo-Notarial",
        "section_path": "DL 1049 > Protocolo notarial",
        "content": (
            "Artículos 36-50 DL 1049 — Protocolo notarial.\n"
            "El protocolo notarial es el conjunto ordenado de los REGISTROS NOTARIALES en los "
            "que el notario incorpora los instrumentos públicos protocolares que autoriza.\n\n"
            "REGISTROS NOTARIALES:\n"
            "1. De escrituras públicas.\n"
            "2. De actas notariales (de protocolización, presencia, notoriedad, etc.).\n"
            "3. De testamentos (testamentos por escritura pública).\n"
            "4. De protestos.\n"
            "5. De otros que disponga la ley.\n\n"
            "CARACTERES:\n"
            "- Único e indivisible: pertenece al oficio notarial, no al notario titular.\n"
            "- Inalterable: los instrumentos no pueden ser modificados, salvo aclaración "
            "complementaria por escritura ulterior.\n"
            "- Custodia perpetua: el notario es responsable de su conservación. Al cesar en "
            "el cargo, el protocolo pasa a su sucesor o al Archivo Notarial del Colegio.\n\n"
            "ARCHIVO GENERAL DE LA NACIÓN: tras 30 años, los protocolos se transfieren al AGN "
            "como patrimonio histórico-jurídico."
        ),
    },
    {
        "article": "Constitucion-Sociedad-Notarial",
        "section_path": "LGS + DL 1049 > Constitución de sociedades",
        "content": (
            "Constitución de sociedades por escritura pública (LGS Ley 26887 + DL 1049).\n"
            "Las sociedades anónimas, SAC, SRL y EIRL deben constituirse por escritura "
            "pública otorgada ante notario.\n\n"
            "REQUISITOS:\n"
            "1. MINUTA firmada por los socios y autorizada por abogado, conteniendo:\n"
            "   - Identidad y declaraciones de los socios.\n"
            "   - Razón/denominación social, objeto, domicilio, duración.\n"
            "   - Capital social, aportes (en efectivo o en bienes valuados).\n"
            "   - Estatuto social completo.\n"
            "   - Nombramiento del directorio o administrador inicial.\n"
            "2. CONSTANCIA DE RESERVA DE NOMBRE de SUNARP (válida 30 días).\n"
            "3. PAGO DEL CAPITAL: depósito bancario por el aporte en efectivo (mínimo 25% al "
            "constituir, saldo en 1 año).\n"
            "4. RECIBO DE PAGO DEL DERECHO REGISTRAL.\n\n"
            "EFECTOS DE LA INSCRIPCIÓN EN SUNARP: la sociedad adquiere PERSONALIDAD JURÍDICA "
            "(Art. 6 LGS) desde su inscripción registral. Antes de ese momento, los actos se "
            "realizan bajo régimen de sociedad irregular con responsabilidad solidaria de los "
            "socios."
        ),
    },
    {
        "article": "Aranceles-Notariales",
        "section_path": "DL 1049 + Reglamento > Aranceles",
        "content": (
            "Aranceles notariales (DS 010-2010-JUS + Aranceles Notariales del Colegio de "
            "Notarios).\n"
            "Los honorarios del notario son LIBRES y se pactan con el cliente, pero el Colegio "
            "publica una tabla referencial mínima por tipo de acto.\n\n"
            "DERECHOS DEL ESTADO (independientes del honorario):\n"
            "- Impuesto a las Transacciones Financieras (ITF) en operaciones sujetas.\n"
            "- Impuesto de Alcabala (3% del valor para transferencias de inmuebles, asume "
            "comprador, paga municipio).\n"
            "- IGV 18% sobre primera venta de inmuebles del constructor (parte por encima "
            "del valor del terreno).\n"
            "- Derechos registrales SUNARP (escala según valor del acto).\n\n"
            "DESCUENTOS LEGALES:\n"
            "- Personas con discapacidad: 50% sobre aranceles notariales y registrales (Ley 29973).\n"
            "- Adultos mayores: descuentos según convenios institucionales.\n"
            "- Primera vivienda dentro de programas Mivivienda / Techo Propio: tasas reducidas."
        ),
    },
]
