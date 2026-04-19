"""
Seed: Código Civil — Extensión: Familia, Sucesiones, Arrendamiento, Garantías.
"""

CIVIL_EXT_ARTICLES = [
    # === FAMILIA ===
    {
        "article": "233",
        "section_path": "CC > Libro III > Derecho de Familia > Disposiciones generales",
        "content": (
            "Artículo 233.- La regulación jurídica de la familia tiene por finalidad contribuir a su consolidación y fortalecimiento, en armonía con los principios y normas proclamados en la Constitución Política del Perú."
        ),
    },
    {
        "article": "234",
        "section_path": "CC > Libro III > Derecho de Familia > Matrimonio",
        "content": (
            "Artículo 234.- El matrimonio es la unión voluntariamente concertada por un varón y una mujer legalmente aptos para ella y formalizada con sujeción a las disposiciones de este Código, a fin de hacer vida común.\n"
            "El marido y la mujer tienen en el hogar autoridad, consideraciones, derechos, deberes y responsabilidades iguales."
        ),
    },
    {
        "article": "333",
        "section_path": "CC > Libro III > Derecho de Familia > Divorcio > Causales",
        "content": (
            "Artículo 333.- Son causas de separación de cuerpos:\n"
            "1. El adulterio.\n"
            "2. La violencia física o psicológica, que el juez apreciará según las circunstancias.\n"
            "3. El atentado contra la vida del cónyuge.\n"
            "4. La injuria grave, que haga insoportable la vida en común.\n"
            "5. El abandono injustificado de la casa conyugal por más de dos años continuos o cuando la duración sumada de los períodos de abandono exceda a este plazo.\n"
            "6. La conducta deshonrosa que haga insoportable la vida en común.\n"
            "7. El uso habitual e injustificado de drogas alucinógenas o de sustancias que puedan generar toxicomanía.\n"
            "8. La enfermedad grave de transmisión sexual contraída después de la celebración del matrimonio.\n"
            "9. La homosexualidad sobreviniente al matrimonio.\n"
            "10. La condena por delito doloso a pena privativa de la libertad mayor de dos años, impuesta después de la celebración del matrimonio.\n"
            "11. La imposibilidad de hacer vida en común, debidamente probada en proceso judicial.\n"
            "12. La separación de hecho de los cónyuges durante un período ininterrumpido de dos años. Dicho plazo será de cuatro años si los cónyuges tuviesen hijos menores de edad.\n"
            "13. La separación convencional, después de transcurridos dos años de la celebración del matrimonio."
        ),
    },
    {
        "article": "472",
        "section_path": "CC > Libro III > Derecho de Familia > Alimentos",
        "content": (
            "Artículo 472.- Se entiende por alimentos lo que es indispensable para el sustento, habitación, vestido, educación, instrucción y capacitación para el trabajo, asistencia médica y psicológica y recreación, según la situación y posibilidades de la familia. También los gastos del embarazo de la madre desde la concepción hasta la etapa de postparto."
        ),
    },
    {
        "article": "474",
        "section_path": "CC > Libro III > Derecho de Familia > Alimentos > Obligados",
        "content": (
            "Artículo 474.- Se deben alimentos recíprocamente:\n"
            "1. Los cónyuges.\n"
            "2. Los ascendientes y descendientes.\n"
            "3. Los hermanos."
        ),
    },
    {
        "article": "481",
        "section_path": "CC > Libro III > Derecho de Familia > Alimentos > Criterios para fijar alimentos",
        "content": (
            "Artículo 481.- Los alimentos se regulan por el juez en proporción a las necesidades de quien los pide y a las posibilidades del que debe darlos, atendiendo además a las circunstancias personales de ambos, especialmente a las obligaciones que se halle sujeto el deudor.\n"
            "El juez considera como un aporte económico el trabajo doméstico no remunerado realizado por alguno de los obligados para el cuidado y desarrollo del alimentista.\n"
            "No es necesario investigar rigurosamente el monto de los ingresos del que debe prestar los alimentos."
        ),
    },
    # === SUCESIONES ===
    {
        "article": "660",
        "section_path": "CC > Libro IV > Derecho de Sucesiones > Transmisión sucesoria",
        "content": (
            "Artículo 660.- Desde el momento de la muerte de una persona, los bienes, derechos y obligaciones que constituyen la herencia se transmiten a sus sucesores."
        ),
    },
    {
        "article": "724",
        "section_path": "CC > Libro IV > Derecho de Sucesiones > Legítima",
        "content": (
            "Artículo 724.- Son herederos forzosos los hijos y los demás descendientes, los padres y los demás ascendientes, el cónyuge o, en su caso, el integrante sobreviviente de la unión de hecho."
        ),
    },
    {
        "article": "725",
        "section_path": "CC > Libro IV > Derecho de Sucesiones > Legítima > Cuota",
        "content": (
            "Artículo 725.- El que tiene hijos u otros descendientes, o cónyuge, puede disponer libremente hasta del tercio de sus bienes."
        ),
    },
    {
        "article": "816",
        "section_path": "CC > Libro IV > Derecho de Sucesiones > Sucesión intestada > Órdenes sucesorios",
        "content": (
            "Artículo 816.- Son herederos del primer orden, los hijos y demás descendientes; del segundo orden, los padres y demás ascendientes; del tercer orden, el cónyuge o, en su caso, el integrante sobreviviente de la unión de hecho; del cuarto, quinto y sexto órdenes, respectivamente, los parientes colaterales del segundo, tercero y cuarto grado de consanguinidad.\n"
            "El cónyuge o, en su caso, el integrante sobreviviente de la unión de hecho también es heredero en concurrencia con los herederos de los dos primeros órdenes indicados en este artículo."
        ),
    },
    # === ARRENDAMIENTO ===
    {
        "article": "1666",
        "section_path": "CC > Libro VII > Contratos nominados > Arrendamiento",
        "content": (
            "Artículo 1666.- Por el arrendamiento el arrendador se obliga a ceder temporalmente al arrendatario el uso de un bien por cierta renta convenida."
        ),
    },
    {
        "article": "1697",
        "section_path": "CC > Libro VII > Contratos nominados > Arrendamiento > Resolución",
        "content": (
            "Artículo 1697.- El contrato de arrendamiento puede resolverse:\n"
            "1. Si el arrendatario no ha pagado la renta del mes anterior y se vence otro mes y además quince días. Si la renta se pacta por períodos mayores, basta el vencimiento de un solo período y además quince días. Si el alquiler se conviene por períodos menores a un mes, basta que venzan tres períodos.\n"
            "2. En los casos previstos en el inciso 1, si el arrendatario necesitó que hubiese contra él sentencia para pagar todo o parte de la renta, y se vence con exceso de quince días el plazo siguiente sin que haya pagado la nueva renta devengada.\n"
            "3. Si el arrendatario da al bien destino diferente de aquel para el que se le concedió.\n"
            "4. Si el arrendatario permite actos de deterioro en el bien.\n"
            "5. Si el arrendatario subarrienda el bien sin asentimiento del arrendador."
        ),
    },
    # === GARANTÍAS REALES ===
    {
        "article": "1055",
        "section_path": "CC > Libro V > Derechos Reales de Garantía > Hipoteca",
        "content": (
            "Artículo 1055.- La hipoteca se constituye por escritura pública, salvo disposición diferente de la ley.\n"
            "Artículo 1097.- Por la hipoteca se afecta un inmueble en garantía del cumplimiento de cualquier obligación, propia o de un tercero.\n"
            "La garantía no determina la desposesión y otorga al acreedor los derechos de persecución, preferencia y venta judicial del bien hipotecado."
        ),
    },
]
