"""
Seed: Derecho de Familia (Perú).

Núcleo normativo:
    - Código Civil — Libro III (Arts. 233-659)
    - Código de los Niños y Adolescentes (Ley 27337)
    - Ley 30364 — Violencia contra las mujeres y los integrantes del grupo familiar
    - Ley 26662 — Competencia notarial en asuntos no contenciosos
    - Ley 27495 — Divorcio convencional y ulterior municipal/notarial

Estilo: cita autoritativa del artículo + interpretación práctica. Resumen del
estado de la jurisprudencia cuando la sola lectura del CC es insuficiente
(ej. tenencia compartida, alimentos del concubino).
"""

FAMILIA_ARTICLES = [
    {
        "article": "234",
        "section_path": "Código Civil > Libro III > Matrimonio",
        "content": (
            "Artículo 234 CC.- Definición de matrimonio.\n"
            "El matrimonio es la unión voluntaria concertada por un varón y una mujer "
            "legalmente aptos para ella, formalizada con sujeción a las disposiciones del "
            "Código Civil, a fin de hacer vida común. El marido y la mujer tienen en el "
            "hogar autoridad, consideraciones, derechos, deberes y responsabilidades iguales.\n"
            "Régimen patrimonial supletorio: sociedad de gananciales (Art. 295 CC). Los "
            "futuros cónyuges pueden optar por separación de patrimonios mediante escritura "
            "pública otorgada antes del matrimonio."
        ),
    },
    {
        "article": "295-301",
        "section_path": "Código Civil > Libro III > Régimen patrimonial",
        "content": (
            "Artículos 295-301 CC.- Sociedad de gananciales y separación de patrimonios.\n"
            "SOCIEDAD DE GANANCIALES (Art. 301): comprende los bienes adquiridos a título "
            "oneroso durante el matrimonio (gananciales). Los bienes propios son los "
            "adquiridos antes del matrimonio o a título gratuito durante el mismo (herencias, "
            "donaciones).\n"
            "SEPARACIÓN DE PATRIMONIOS (Art. 327): cada cónyuge conserva la titularidad y "
            "administración exclusiva de sus bienes. Debe otorgarse por escritura pública "
            "antes del matrimonio o sustituir el régimen de gananciales por convenio.\n"
            "Sustitución de régimen: requiere escritura pública e inscripción registral. "
            "Antes de la inscripción no es oponible a terceros."
        ),
    },
    {
        "article": "333",
        "section_path": "Código Civil > Libro III > Causales de divorcio",
        "content": (
            "Artículo 333 CC.- Causales de separación de cuerpos / divorcio.\n"
            "1. Adulterio (caduca a los 6 meses de conocido el hecho).\n"
            "2. Violencia física o psicológica.\n"
            "3. Atentado contra la vida del cónyuge.\n"
            "4. Injuria grave que haga insoportable la vida en común.\n"
            "5. Abandono injustificado por más de 2 años continuos.\n"
            "6. Conducta deshonrosa que haga insoportable la vida en común.\n"
            "7. Uso habitual de drogas alucinógenas o sustancias que generen toxicomanía.\n"
            "8. Enfermedad grave de transmisión sexual contraída después del matrimonio.\n"
            "9. Homosexualidad sobreviniente.\n"
            "10. Condena por delito doloso con pena privativa de libertad mayor a 2 años.\n"
            "11. Imposibilidad de hacer vida común (causal acreditada judicialmente).\n"
            "12. Separación de hecho por más de 2 años (4 años si hay hijos menores).\n"
            "13. Separación convencional, después de transcurridos 2 años de la celebración."
        ),
    },
    {
        "article": "354-359",
        "section_path": "Código Civil > Libro III > Divorcio",
        "content": (
            "Artículos 354-359 CC.- Efectos del divorcio.\n"
            "El divorcio pone fin al vínculo matrimonial. La sentencia de divorcio se inscribe "
            "en la partida matrimonial del RENIEC.\n"
            "El cónyuge culpable pierde el derecho a alimentos y el derecho a heredar al "
            "inocente. El cónyuge inocente puede percibir una pensión compensatoria si la "
            "ruptura le genera un desequilibrio económico (jurisprudencia constante TC).\n"
            "DIVORCIO MUNICIPAL/NOTARIAL (Ley 27495 + Ley 26662): procede sólo en separación "
            "convencional con 2 años de matrimonio, sin hijos menores ni bienes sujetos a "
            "régimen de sociedad de gananciales por liquidar. Tramita ante alcalde provincial o "
            "notario público de la jurisdicción del último domicilio conyugal."
        ),
    },
    {
        "article": "472-487",
        "section_path": "Código Civil > Libro III > Alimentos",
        "content": (
            "Artículos 472-487 CC + CNA (Ley 27337).- Obligación alimentaria.\n"
            "Alimentos comprende: alimentación, vestido, vivienda, educación, recreación, "
            "asistencia médica, psicológica y todo aquello necesario para la subsistencia.\n"
            "PRELACIÓN del obligado a alimentos (Art. 475 CC):\n"
            "1. Cónyuge.\n"
            "2. Descendientes.\n"
            "3. Ascendientes.\n"
            "4. Hermanos.\n"
            "Cuando hay varios obligados del mismo grado, se distribuye proporcionalmente "
            "a la capacidad económica de cada uno (prorrateo).\n"
            "Monto: entre el 20% y 60% de los ingresos del obligado, según necesidad del "
            "alimentista y posibilidades del obligado.\n"
            "Vía procesal: Proceso Único (CNA) — competencia del juzgado de familia/paz "
            "letrado. Sentencia goza de ejecución inmediata."
        ),
    },
    {
        "article": "418-423",
        "section_path": "Código Civil > Libro III > Patria potestad",
        "content": (
            "Artículos 418-423 CC + CNA.- Patria potestad.\n"
            "La patria potestad es el conjunto de derechos y deberes que tienen los padres "
            "respecto de la persona y bienes de los hijos menores no emancipados.\n"
            "Ambos padres ejercen conjuntamente la patria potestad durante el matrimonio. En "
            "caso de separación o divorcio, el juez decide su ejercicio según el INTERÉS "
            "SUPERIOR DEL NIÑO.\n"
            "Pérdida o suspensión: por sentencia que imponga pena privativa de libertad, "
            "incumplimiento de obligaciones alimentarias por más de 6 meses, abandono, abuso "
            "de autoridad, mal trato. Pueden ser restituidas mediante proceso judicial."
        ),
    },
    {
        "article": "tenencia",
        "section_path": "CNA > Tenencia y régimen de visitas",
        "content": (
            "Artículos 81-87 CNA (Ley 27337).- Tenencia del niño/adolescente.\n"
            "La tenencia se determina de común acuerdo entre los padres. A falta de acuerdo, "
            "el juez resuelve atendiendo al INTERÉS SUPERIOR DEL NIÑO, oyendo al menor de "
            "acuerdo a su edad y madurez.\n"
            "TENENCIA COMPARTIDA (Ley 29269): el juez puede otorgarla cuando se acredite la "
            "vinculación afectiva con ambos progenitores y la cercanía geográfica de los "
            "domicilios permita la rotación.\n"
            "RÉGIMEN DE VISITAS: el padre que no obtiene la tenencia tiene derecho a un régimen "
            "amplio de visitas. La negativa injustificada del progenitor con tenencia configura "
            "el delito de impedimento de visitas (Art. 38 CNA + sanciones penales)."
        ),
    },
    {
        "article": "filiacion",
        "section_path": "Código Civil > Libro III > Filiación",
        "content": (
            "Artículos 361-417 CC + Ley 28457.- Filiación matrimonial y extramatrimonial.\n"
            "FILIACIÓN MATRIMONIAL: presunción pater is est — se presume hijo del marido el "
            "concebido durante el matrimonio (Art. 361 CC). El marido tiene 90 días desde la "
            "inscripción del nacimiento para impugnarla.\n"
            "FILIACIÓN EXTRAMATRIMONIAL: se establece por reconocimiento voluntario o por "
            "sentencia que la declara.\n"
            "PROCESO DE FILIACIÓN JUDICIAL DE PATERNIDAD EXTRAMATRIMONIAL (Ley 28457): "
            "el juez de paz letrado conoce el proceso. Si el demandado se niega a someterse "
            "a la prueba de ADN, dicha negativa se considera presunción legal de paternidad "
            "(Art. 4 Ley 28457).\n"
            "Impugnación de paternidad: el plazo para accionar es de 1 año desde el "
            "conocimiento del hecho (jurisprudencia constante de la Corte Suprema)."
        ),
    },
    {
        "article": "377-385",
        "section_path": "Código Civil > Libro III > Adopción",
        "content": (
            "Artículos 377-385 CC + Ley 26981 + CNA.- Adopción.\n"
            "ADOPCIÓN DE PERSONAS MAYORES DE EDAD: tramitación notarial (Ley 26662, Art. 21).\n"
            "ADOPCIÓN DE NIÑOS Y ADOLESCENTES: procedimiento administrativo ante la Dirección "
            "General de Adopciones (DGA) del MIMP. Requisitos: declaración judicial de abandono, "
            "informe psicosocial favorable, inscripción en el registro de adoptantes.\n"
            "ADOPCIÓN INTERNACIONAL: requiere convenio bilateral entre Perú y el país del "
            "adoptante. La DGA emite el informe de empatía y el juez resuelve la adopción.\n"
            "Efectos: el adoptado adquiere la condición de hijo del adoptante y se extinguen "
            "los vínculos de filiación con la familia biológica (irrevocabilidad)."
        ),
    },
    {
        "article": "326",
        "section_path": "Código Civil > Libro III > Unión de hecho",
        "content": (
            "Artículo 326 CC.- Unión de hecho (concubinato).\n"
            "La unión de hecho voluntaria realizada por un varón y una mujer libres de "
            "impedimento matrimonial, para alcanzar finalidades semejantes a las del "
            "matrimonio, origina una sociedad de bienes que se sujeta al régimen de la "
            "SOCIEDAD DE GANANCIALES, siempre que la unión haya durado por lo menos 2 años "
            "continuos.\n"
            "RECONOCIMIENTO NOTARIAL (Ley 29560 modifica Ley 26662): los convivientes pueden "
            "solicitar el reconocimiento de la unión de hecho mediante escritura pública "
            "ante notario, acreditando los 2 años de convivencia con declaración de testigos "
            "y publicación. Inscribible en SUNARP — Registro Personal.\n"
            "DERECHO HEREDITARIO: el conviviente supérstite hereda al fallecido conforme a las "
            "reglas del cónyuge (Art. 326 CC modificado y jurisprudencia TC Exp. 09708-2006-PA)."
        ),
    },
    {
        "article": "Ley-30364",
        "section_path": "Ley 30364 > Violencia familiar",
        "content": (
            "Ley 30364 (2015) — Prevención, sanción y erradicación de la violencia contra "
            "las mujeres y los integrantes del grupo familiar.\n"
            "TIPOS DE VIOLENCIA:\n"
            "1. Violencia física: daño a la integridad corporal.\n"
            "2. Violencia psicológica: alteración del normal desarrollo de la víctima.\n"
            "3. Violencia sexual: acciones que vulneren el derecho a decidir voluntariamente "
            "sobre la vida sexual y reproductiva.\n"
            "4. Violencia económica o patrimonial: limitación de recursos económicos o despojo "
            "de bienes.\n\n"
            "PROCEDIMIENTO:\n"
            "- Denuncia: PNP, fiscalía o juzgado de familia (24/7).\n"
            "- Ficha de Valoración del Riesgo (FVR): instrumento técnico para medir el nivel "
            "de riesgo.\n"
            "- Medidas de protección: emitidas por juez de familia en 72 horas. Incluyen "
            "retiro del agresor, prohibición de acercamiento, asignación temporal de "
            "alimentos, custodia de menores.\n"
            "- Etapa de sanción: el juez penal/mixto resuelve responsabilidad penal "
            "(faltas o delitos según la gravedad).\n\n"
            "Sanción al agresor: pena privativa de libertad + medidas accesorias (tratamiento "
            "obligatorio, trabajo comunitario, prohibición de acceso). Reincidencia agrava la pena."
        ),
    },
    {
        "article": "660-664",
        "section_path": "Código Civil > Libro IV > Sucesiones",
        "content": (
            "Artículos 660-664 CC.- Sucesión y patrimonio hereditario familiar.\n"
            "Desde el momento de la muerte de una persona, los bienes, derechos y obligaciones "
            "que constituyen la herencia se transmiten a sus sucesores.\n"
            "ÓRDENES SUCESORIOS (sucesión intestada):\n"
            "1° orden: hijos y demás descendientes.\n"
            "2° orden: padres y demás ascendientes.\n"
            "3° orden: cónyuge supérstite (excluye a los demás).\n"
            "4° orden: hermanos.\n"
            "5° orden: parientes colaterales hasta 4° grado.\n"
            "6° orden: Beneficencia Pública (a falta de los anteriores).\n\n"
            "El cónyuge supérstite concurre con los hijos y ascendientes — cuota legal "
            "específica (Art. 822 y siguientes CC). La cuarta de libre disposición permite "
            "al testador disponer libremente del 25% del patrimonio (Art. 723 CC)."
        ),
    },
]
