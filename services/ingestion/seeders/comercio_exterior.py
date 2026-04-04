"""
Seed: Comercio Exterior — Aduanas, TLC, MINCETUR.
Última área para completar 11/11.
"""

COMERCIO_EXT_ARTICLES = [
    {
        "article": "ADUANA-1",
        "section_path": "DL 1053 > Ley General de Aduanas > Disposiciones generales",
        "content": (
            "Decreto Legislativo 1053 — Ley General de Aduanas.\n"
            "Artículo 1.- Los servicios aduaneros son esenciales y están destinados a facilitar el comercio "
            "exterior, contribuyendo al desarrollo nacional y cautelando los intereses fiscales y el comercio "
            "internacional de acuerdo con los tratados y convenios vigentes.\n\n"
            "La SUNAT es la autoridad aduanera en el Perú, a través de la Superintendencia Nacional Adjunta "
            "de Aduanas.\n\n"
            "Regímenes aduaneros principales:\n"
            "1. Importación para el consumo: ingreso legal de mercancías al país.\n"
            "2. Exportación definitiva: salida legal de mercancías del país.\n"
            "3. Admisión temporal para reexportación en el mismo estado.\n"
            "4. Admisión temporal para perfeccionamiento activo.\n"
            "5. Depósito aduanero.\n"
            "6. Tránsito aduanero.\n"
            "7. Drawback: restitución de derechos arancelarios."
        ),
    },
    {
        "article": "ADUANA-DRAWBACK",
        "section_path": "DS 104-95-EF > Drawback > Restitución arancelaria",
        "content": (
            "Régimen de Drawback — Restitución Simplificada de Derechos Arancelarios (DS 104-95-EF y modificatorias).\n"
            "Permite a las empresas productoras-exportadoras obtener la restitución total o parcial de los "
            "derechos arancelarios que hayan gravado la importación de materias primas, insumos, productos "
            "intermedios o partes y piezas incorporados en la producción de bienes exportados.\n\n"
            "Tasa de restitución: 3% del valor FOB de exportación, con un tope por subpartida arancelaria.\n"
            "Requisitos principales:\n"
            "1. Ser empresa productora-exportadora.\n"
            "2. Los insumos importados deben incorporarse en el producto exportado.\n"
            "3. El valor CIF de los insumos no debe superar el 50% del valor FOB del producto exportado.\n"
            "4. La solicitud se presenta dentro de los 180 días útiles desde la fecha de embarque."
        ),
    },
    {
        "article": "TLC-GENERAL",
        "section_path": "MINCETUR > TLC vigentes del Perú",
        "content": (
            "Tratados de Libre Comercio (TLC) vigentes del Perú:\n"
            "1. TLC Perú - Estados Unidos (vigente desde febrero 2009)\n"
            "2. TLC Perú - China (vigente desde marzo 2010)\n"
            "3. TLC Perú - Unión Europea (vigente desde marzo 2013)\n"
            "4. TLC Perú - Japón (vigente desde marzo 2012)\n"
            "5. TLC Perú - Corea del Sur (vigente desde agosto 2011)\n"
            "6. TLC Perú - Chile (vigente desde marzo 2009)\n"
            "7. TLC Perú - Canadá (vigente desde agosto 2009)\n"
            "8. TLC Perú - Singapur (vigente desde agosto 2009)\n"
            "9. TLC Perú - EFTA (Suiza, Noruega, Islandia, Liechtenstein)\n"
            "10. TLC Perú - Australia (vigente desde febrero 2020)\n"
            "11. TLC Perú - Reino Unido (vigente desde diciembre 2020)\n"
            "12. Comunidad Andina (CAN): Bolivia, Colombia, Ecuador, Perú\n"
            "13. MERCOSUR: acuerdo de complementación económica\n"
            "14. Alianza del Pacífico: Chile, Colombia, México, Perú\n"
            "15. CPTPP (Tratado Integral y Progresista de Asociación Transpacífico)\n\n"
            "El MINCETUR es la autoridad rectora en materia de comercio exterior.\n"
            "PromPerú promueve las exportaciones peruanas."
        ),
    },
    {
        "article": "ADUANA-IMPORT",
        "section_path": "DL 1053 > Importación para el consumo > Tributos",
        "content": (
            "Importación para el consumo — Tributos aduaneros principales:\n\n"
            "1. Ad valorem (arancel): 0%, 4%, 6% o 11% sobre el valor CIF, según la subpartida arancelaria.\n"
            "2. IGV: 16% sobre el valor CIF + ad valorem.\n"
            "3. IPM (Impuesto de Promoción Municipal): 2% sobre la misma base del IGV.\n"
            "4. ISC (Impuesto Selectivo al Consumo): aplicable a ciertos productos (licores, cigarrillos, combustibles, vehículos).\n"
            "5. Derechos antidumping o compensatorios: cuando corresponda por resolución del INDECOPI.\n"
            "6. Percepción del IGV: aplicable según régimen de percepciones SUNAT.\n\n"
            "Base imponible CIF = Valor FOB + Flete + Seguro.\n"
            "El despacho aduanero requiere agente de aduana para mercancías con valor FOB superior a US$ 2,000.\n"
            "Documentos principales: DAM (Declaración Aduanera de Mercancías), factura comercial, BL o AWB, packing list."
        ),
    },
]
