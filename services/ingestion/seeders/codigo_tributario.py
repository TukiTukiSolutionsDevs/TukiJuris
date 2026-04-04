"""
Seed: Derecho Tributario — Código Tributario y normas clave SUNAT/IR/IGV.
"""

TRIBUTARIO_ARTICLES = [
    {
        "article": "CT-1",
        "section_path": "Código Tributario > Título Preliminar > Norma I",
        "content": (
            "NORMA I: CONTENIDO. El presente Código establece los principios generales, instituciones, procedimientos y normas del ordenamiento jurídico-tributario."
        ),
    },
    {
        "article": "CT-II",
        "section_path": "Código Tributario > Título Preliminar > Norma II",
        "content": (
            "NORMA II: ÁMBITO DE APLICACIÓN. Este Código rige las relaciones jurídicas originadas por los tributos. Para estos efectos, el término genérico tributo comprende:\n"
            "a) Impuesto: Es el tributo cuyo cumplimiento no origina una contraprestación directa en favor del contribuyente por parte del Estado.\n"
            "b) Contribución: Es el tributo cuya obligación tiene como hecho generador beneficios derivados de la realización de obras públicas o de actividades estatales.\n"
            "c) Tasa: Es el tributo cuya obligación tiene como hecho generador la prestación efectiva por el Estado de un servicio público individualizado en el contribuyente. Las Tasas, entre otras, pueden ser: Arbitrios, Derechos y Licencias."
        ),
    },
    {
        "article": "CT-IV",
        "section_path": "Código Tributario > Título Preliminar > Norma IV > Principio de legalidad",
        "content": (
            "NORMA IV: PRINCIPIO DE LEGALIDAD - RESERVA DE LA LEY.\n"
            "Sólo por Ley o por Decreto Legislativo, en caso de delegación, se puede:\n"
            "a) Crear, modificar y suprimir tributos; señalar el hecho generador de la obligación tributaria, la base para su cálculo y la alícuota; el acreedor tributario; el deudor tributario y el agente de retención o percepción.\n"
            "b) Conceder exoneraciones y otros beneficios tributarios.\n"
            "c) Normar los procedimientos jurisdiccionales, así como los administrativos en cuanto a derechos o garantías del deudor tributario.\n"
            "d) Definir las infracciones y establecer sanciones.\n"
            "e) Establecer privilegios, preferencias y garantías para la deuda tributaria.\n"
            "f) Normar formas de extinción de la obligación tributaria distintas a las establecidas en este Código."
        ),
    },
    {
        "article": "CT-43",
        "section_path": "Código Tributario > Libro I > Título III > Prescripción",
        "content": (
            "Artículo 43.- La acción de la Administración Tributaria para determinar la obligación tributaria, así como la acción para exigir su pago y aplicar sanciones prescribe a los cuatro (4) años, y a los seis (6) años para quienes no hayan presentado la declaración respectiva.\n"
            "Dichas acciones prescriben a los diez (10) años cuando el Agente de retención o percepción no ha pagado el tributo retenido o percibido.\n"
            "La acción para solicitar o efectuar la compensación, así como para solicitar la devolución prescribe a los cuatro (4) años."
        ),
    },
    # === IMPUESTO A LA RENTA ===
    {
        "article": "IR-1",
        "section_path": "Ley IR > TUO DS 179-2004-EF > Ámbito de aplicación",
        "content": (
            "Artículo 1 (Ley del Impuesto a la Renta).- El Impuesto a la Renta grava:\n"
            "a) Las rentas que provengan del capital, del trabajo y de la aplicación conjunta de ambos factores, entendiéndose como tales aquellas que provengan de una fuente durable y susceptible de generar ingresos periódicos.\n"
            "b) Las ganancias de capital.\n"
            "c) Otros ingresos que provengan de terceros, establecidos por esta Ley.\n"
            "d) Las rentas imputadas, incluyendo las de goce o disfrute, establecidas por esta Ley."
        ),
    },
    {
        "article": "IR-22",
        "section_path": "Ley IR > Categorías de Renta",
        "content": (
            "Artículo 22 (Ley del IR).- Para los efectos del impuesto, las rentas afectas de fuente peruana se califican en las siguientes categorías:\n"
            "a) Primera Categoría: Rentas producidas por el arrendamiento, subarrendamiento y cesión de bienes.\n"
            "b) Segunda Categoría: Rentas del capital no comprendidas en la primera categoría (intereses, regalías, dividendos).\n"
            "c) Tercera Categoría: Rentas del comercio, la industria y otras expresamente consideradas por la Ley (rentas empresariales).\n"
            "d) Cuarta Categoría: Rentas del trabajo independiente.\n"
            "e) Quinta Categoría: Rentas del trabajo en relación de dependencia, y otras rentas del trabajo independiente expresamente señaladas por la ley."
        ),
    },
    {
        "article": "IR-53",
        "section_path": "Ley IR > Tasas del impuesto > Personas naturales",
        "content": (
            "Artículo 53 (Ley del IR).- El impuesto a cargo de personas naturales, sucesiones indivisas y sociedades conyugales que optaron por tributar como tales, domiciliadas en el país, se determina aplicando sobre la renta neta global anual la escala progresiva acumulativa siguiente:\n"
            "- Hasta 5 UIT: 8%\n"
            "- Más de 5 UIT hasta 20 UIT: 14%\n"
            "- Más de 20 UIT hasta 35 UIT: 17%\n"
            "- Más de 35 UIT hasta 45 UIT: 20%\n"
            "- Más de 45 UIT: 30%\n\n"
            "Para el ejercicio 2024, la UIT es S/ 5,150. Por lo tanto, los tramos son:\n"
            "- Hasta S/ 25,750: 8%\n"
            "- De S/ 25,750 a S/ 103,000: 14%\n"
            "- De S/ 103,000 a S/ 180,250: 17%\n"
            "- De S/ 180,250 a S/ 231,750: 20%\n"
            "- Más de S/ 231,750: 30%"
        ),
    },
    {
        "article": "IR-46",
        "section_path": "Ley IR > Deducciones > 7 UIT",
        "content": (
            "Artículo 46 (Ley del IR).- De las rentas de cuarta y quinta categorías podrán deducirse anualmente, un monto fijo equivalente a siete (7) Unidades Impositivas Tributarias (UIT).\n"
            "Adicionalmente, los contribuyentes que obtengan rentas de cuarta y/o quinta categoría podrán deducir como gasto los importes pagados por concepto de:\n"
            "a) Arrendamiento y/o subarrendamiento de inmuebles situados en el país que no estén destinados exclusivamente al desarrollo de actividades que generen rentas de tercera categoría.\n"
            "b) Intereses de créditos hipotecarios para primera vivienda.\n"
            "c) Honorarios profesionales de médicos y odontólogos.\n"
            "d) Servicios prestados por perceptores de rentas de cuarta categoría (con algunos límites).\n"
            "e) Las aportaciones al Seguro Social de Salud – EsSalud que se realicen por los trabajadores del hogar.\n"
            "El monto máximo de estas deducciones adicionales es de tres (3) UIT."
        ),
    },
    # === IGV ===
    {
        "article": "IGV-1",
        "section_path": "Ley IGV > TUO DS 055-99-EF > Operaciones gravadas",
        "content": (
            "Artículo 1 (Ley del IGV).- El Impuesto General a las Ventas grava las siguientes operaciones:\n"
            "a) La venta en el país de bienes muebles;\n"
            "b) La prestación o utilización de servicios en el país;\n"
            "c) Los contratos de construcción;\n"
            "d) La primera venta de inmuebles que realicen los constructores de los mismos;\n"
            "e) La importación de bienes.\n\n"
            "La tasa del IGV es del 16%, más el 2% del Impuesto de Promoción Municipal, totalizando el 18% que se aplica sobre el valor de venta."
        ),
    },
]
