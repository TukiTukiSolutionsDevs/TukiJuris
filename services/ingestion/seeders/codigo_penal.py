"""
Seed: Código Penal Peruano (DL 635) — Artículos más consultados.
"""

PENAL_ARTICLES = [
    # === PARTE GENERAL ===
    {
        "article": "11",
        "section_path": "CP > Libro I > Título II > Hecho Punible > Bases de punibilidad",
        "content": (
            "Artículo 11.- Son delitos y faltas las acciones u omisiones dolosas o culposas penadas por la ley."
        ),
    },
    {
        "article": "12",
        "section_path": "CP > Libro I > Título II > Hecho Punible > Dolo y culpa",
        "content": (
            "Artículo 12.- Las penas establecidas por la ley se aplican siempre al agente de infracción dolosa.\n"
            "El agente de infracción culposa es punible en los casos expresamente establecidos por la ley."
        ),
    },
    {
        "article": "20",
        "section_path": "CP > Libro I > Título II > Hecho Punible > Causas de inimputabilidad",
        "content": (
            "Artículo 20.- Está exento de responsabilidad penal:\n"
            "1. El que por anomalía psíquica, grave alteración de la conciencia o por sufrir alteraciones en la percepción, que afectan gravemente su concepto de la realidad, no posea la facultad de comprender el carácter delictuoso de su acto o para determinarse según esta comprensión;\n"
            "2. El menor de 18 años;\n"
            "3. El que obra en defensa de bienes jurídicos propios o de terceros, siempre que concurran las circunstancias siguientes: a) Agresión ilegítima; b) Necesidad racional del medio empleado para impedirla o repelerla; c) Falta de provocación suficiente de quien hace la defensa;\n"
            "4. El que, ante un peligro actual e insuperable de otro modo, que amenace la vida, la integridad corporal, la libertad u otro bien jurídico, realiza un hecho destinado a conjurar dicho peligro de sí o de otro (estado de necesidad);\n"
            "5. El que, ante un peligro actual y no evitable de otro modo, que signifique una amenaza para la vida, la integridad corporal o la libertad, realiza un hecho antijurídico para alejar el peligro de sí mismo o de una persona con quien tiene estrecha vinculación;\n"
            "6. El que obra por una fuerza física irresistible proveniente de un tercero o de la naturaleza;\n"
            "7. El que obra compelido por miedo insuperable de un mal igual o mayor;\n"
            "8. El que obra por disposición de la ley, en cumplimiento de un deber o en el ejercicio legítimo de un derecho, oficio o cargo;\n"
            "9. El que obra por orden obligatoria de autoridad competente, expedida en ejercicio de sus funciones;\n"
            "10. El que actúa con el consentimiento válido del titular de un bien jurídico de libre disposición."
        ),
    },
    {
        "article": "29",
        "section_path": "CP > Libro I > Título III > Penas > Clases de pena",
        "content": (
            "Artículo 28.- Las penas aplicables de conformidad con este Código son:\n"
            "- Privativa de libertad;\n"
            "- Restrictivas de libertad;\n"
            "- Limitativas de derechos; y\n"
            "- Multa.\n\n"
            "Artículo 29.- La pena privativa de libertad puede ser:\n"
            "- Temporal: tiene una duración mínima de dos días y una máxima de treinta y cinco años.\n"
            "- De cadena perpetua."
        ),
    },
    # === DELITOS CONTRA LA VIDA ===
    {
        "article": "106",
        "section_path": "CP > Libro II > Título I > Delitos contra la Vida > Homicidio simple",
        "content": (
            "Artículo 106.- El que mata a otro será reprimido con pena privativa de libertad no menor de seis ni mayor de veinte años."
        ),
    },
    {
        "article": "108",
        "section_path": "CP > Libro II > Título I > Delitos contra la Vida > Homicidio calificado",
        "content": (
            "Artículo 108.- Será reprimido con pena privativa de libertad no menor de quince años el que mata a otro concurriendo cualquiera de las circunstancias siguientes:\n"
            "1. Por ferocidad, codicia, lucro o por placer;\n"
            "2. Para facilitar u ocultar otro delito;\n"
            "3. Con gran crueldad o alevosía;\n"
            "4. Por fuego, explosión o cualquier otro medio capaz de poner en peligro la vida o salud de otras personas."
        ),
    },
    {
        "article": "111",
        "section_path": "CP > Libro II > Título I > Delitos contra la Vida > Homicidio culposo",
        "content": (
            "Artículo 111.- El que, por culpa, ocasiona la muerte de una persona, será reprimido con pena privativa de libertad no mayor de dos años o con prestación de servicios comunitarios de cincuenta y dos a ciento cuatro jornadas.\n"
            "La pena privativa de la libertad será no menor de un año ni mayor de cuatro años si el delito resulta de la inobservancia de reglas de profesión, de ocupación o industria y no menor de un año ni mayor de seis años cuando sean varias las víctimas del mismo hecho.\n"
            "La pena privativa de la libertad será no menor de cuatro años ni mayor de ocho años e inhabilitación, si la muerte se comete utilizando vehículo motorizado o arma de fuego, estando el agente bajo el efecto de drogas tóxicas, estupefacientes, sustancias psicotrópicas o sintéticas, o con presencia de alcohol en la sangre en proporción mayor de 0.5 gramos-litro, o cuando el delito resulte de la inobservancia de reglas técnicas de tránsito."
        ),
    },
    # === DELITOS CONTRA EL PATRIMONIO ===
    {
        "article": "185",
        "section_path": "CP > Libro II > Título V > Delitos contra el Patrimonio > Hurto simple",
        "content": (
            "Artículo 185.- El que, para obtener provecho, se apodera ilegítimamente de un bien mueble, total o parcialmente ajeno, sustrayéndolo del lugar donde se encuentra, será reprimido con pena privativa de libertad no menor de uno ni mayor de tres años.\n"
            "Se equiparan a bien mueble la energía eléctrica, el gas, los hidrocarburos o sus productos derivados, el agua y cualquier otra energía o elemento que tenga valor económico, así como el espectro electromagnético y también los recursos pesqueros objeto de un mecanismo de asignación de Límites Máximos de Captura por Embarcación."
        ),
    },
    {
        "article": "188",
        "section_path": "CP > Libro II > Título V > Delitos contra el Patrimonio > Robo",
        "content": (
            "Artículo 188.- El que se apodera ilegítimamente de un bien mueble total o parcialmente ajeno, para aprovecharse de él, sustrayéndolo del lugar en que se encuentra, empleando violencia contra la persona o amenazándola con un peligro inminente para su vida o integridad física será reprimido con pena privativa de libertad no menor de tres ni mayor de ocho años."
        ),
    },
    {
        "article": "189",
        "section_path": "CP > Libro II > Título V > Delitos contra el Patrimonio > Robo agravado",
        "content": (
            "Artículo 189.- La pena será no menor de doce ni mayor de veinte años si el robo es cometido:\n"
            "1. En inmueble habitado.\n"
            "2. Durante la noche o en lugar desolado.\n"
            "3. A mano armada.\n"
            "4. Con el concurso de dos o más personas.\n"
            "5. En cualquier medio de locomoción de transporte público o privado de pasajeros o de carga, terminales terrestres, ferroviarios, lacustres y fluviales, puertos, aeropuertos, restaurantes y afines, establecimientos de hospedaje y lugares de alojamiento, áreas naturales protegidas, fuentes de agua minero-medicinales con fines turísticos, bienes inmuebles integrantes del patrimonio cultural de la Nación y museos.\n"
            "6. Fingiendo ser autoridad o servidor público o trabajador del sector privado o mostrando mandamiento falso de autoridad.\n"
            "7. En agravio de menores de edad, personas con discapacidad, mujeres en estado de gravidez o adulto mayor.\n"
            "8. Sobre vehículo automotor, sus autopartes o accesorios.\n\n"
            "La pena será no menor de veinte ni mayor de treinta años si el robo es cometido:\n"
            "1. Cuando se cause lesiones a la integridad física o mental de la víctima.\n"
            "2. Con abuso de la incapacidad física o mental de la víctima o mediante el empleo de drogas, insumos químicos o fármacos contra la víctima.\n"
            "3. Colocando a la víctima o a su familia en grave situación económica.\n"
            "4. Sobre bienes de valor científico o que integren el patrimonio cultural de la Nación.\n\n"
            "La pena será de cadena perpetua cuando el agente actúe en calidad de integrante de una organización criminal, o si, como consecuencia del hecho, se produce la muerte de la víctima o se le causa lesiones graves a su integridad física o mental."
        ),
    },
    {
        "article": "196",
        "section_path": "CP > Libro II > Título V > Delitos contra el Patrimonio > Estafa",
        "content": (
            "Artículo 196.- El que procura para sí o para otro un provecho ilícito en perjuicio de tercero, induciendo o manteniendo en error al agraviado mediante engaño, astucia, ardid u otra forma fraudulenta, será reprimido con pena privativa de libertad no menor de uno ni mayor de seis años."
        ),
    },
    {
        "article": "197",
        "section_path": "CP > Libro II > Título V > Delitos contra el Patrimonio > Estafa agravada",
        "content": (
            "Artículo 197.- La defraudación será reprimida con pena privativa de libertad no menor de cuatro ni mayor de ocho años y con noventa a trescientos sesenta y cinco días-multa, cuando:\n"
            "1. Se realice con simulación de juicio o empleo de otro fraude procesal.\n"
            "2. Se realice con abuso de firma en blanco, extendiendo algún documento en perjuicio del firmante o de tercero.\n"
            "3. Si el comitente de un bien mueble lo vende o grava como propio, si su transferencia no ha sido autorizada por quien le hizo la entrega.\n"
            "4. Se venda o grave, como bienes libres, los que son litigiosos o están embargados o gravados y cuando se venda, grave o arriende como propios los bienes ajenos."
        ),
    },
    # === DELITOS CONTRA LA LIBERTAD SEXUAL ===
    {
        "article": "170",
        "section_path": "CP > Libro II > Título IV > Cap IX > Violación sexual",
        "content": (
            "Artículo 170.- El que con violencia, física o psicológica, grave amenaza o aprovechándose de un entorno de coacción o de cualquier otro entorno que impida a la persona dar su libre consentimiento, obliga a esta a tener acceso carnal por vía vaginal, anal o bucal o realiza cualquier otro acto análogo con la introducción de un objeto o parte del cuerpo por alguna de las dos primeras vías, será reprimido con pena privativa de libertad no menor de seis ni mayor de ocho años.\n"
            "La pena será no menor de doce ni mayor de dieciocho años e inhabilitación conforme corresponda, si la violación se realiza a mano armada o por dos o más sujetos, o si el agente se aprovecha de su vínculo de parentesco o su posición de autoridad."
        ),
    },
]
