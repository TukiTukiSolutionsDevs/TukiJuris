"""
Specialized legal domain agents for Peruvian law.

Each agent has deep knowledge of its legal area and filters RAG
retrieval to only relevant normative sources.
"""

from app.agents.base_agent import BaseLegalAgent


class CivilLawAgent(BaseLegalAgent):
    """Agent specializing in Peruvian Civil Law."""

    def get_agent_name(self) -> str:
        return "Agente de Derecho Civil"

    def get_legal_area(self) -> str:
        return "civil"

    def get_domain_prompt(self) -> str:
        return """ESPECIALIZACIÓN: DERECHO CIVIL PERUANO

Tu dominio incluye:
- Código Civil de 1984 (Decreto Legislativo 295) — Libros I al X
- Código Procesal Civil (Resolución Ministerial 010-93-JUS)
- Derecho de Personas, Acto Jurídico, Familia, Sucesiones
- Derechos Reales, Obligaciones, Contratos
- Responsabilidad Civil (contractual y extracontractual)
- Registros Públicos en materia civil
- Prescripción y Caducidad

NORMATIVA CLAVE:
- CC Art. 1-2132: Todo el Código Civil
- CPC: Procesos civiles (conocimiento, abreviado, sumarísimo, ejecutivo)
- Ley 26662: Competencia notarial en asuntos no contenciosos
- Ley 27287: Ley de Títulos Valores
- Código de Niños y Adolescentes (Ley 27337)

Al responder consultas civiles, siempre identifica:
1. La institución jurídica aplicable
2. Los artículos específicos del CC o norma aplicable
3. Plazos relevantes (prescripción, caducidad)
4. La vía procesal correspondiente"""

    def get_rag_filter(self) -> dict:
        return {"legal_area": {"$in": ["civil", "procesal_civil", "familia", "sucesiones"]}}


class CriminalLawAgent(BaseLegalAgent):
    """Agent specializing in Peruvian Criminal Law."""

    def get_agent_name(self) -> str:
        return "Agente de Derecho Penal"

    def get_legal_area(self) -> str:
        return "penal"

    def get_domain_prompt(self) -> str:
        return """ESPECIALIZACIÓN: DERECHO PENAL PERUANO

Tu dominio incluye:
- Código Penal de 1991 (Decreto Legislativo 635) — Parte General y Especial
- Nuevo Código Procesal Penal (Decreto Legislativo 957)
- Código de Ejecución Penal (Decreto Legislativo 654)
- Leyes penales especiales

NORMATIVA CLAVE:
- CP Art. 1-466: Tipificación de delitos y penas
- NCPP: Proceso penal común, terminación anticipada, proceso inmediato
- Ley 30077: Crimen organizado
- DL 1106: Lavado de activos
- Ley 30364: Violencia contra la mujer

Al responder consultas penales, siempre identifica:
1. El tipo penal específico (artículo del CP)
2. Los elementos del tipo (objetivo y subjetivo)
3. La pena abstracta (rango de años)
4. La vía procesal aplicable
5. Circunstancias agravantes o atenuantes relevantes"""

    def get_rag_filter(self) -> dict:
        return {"legal_area": {"$in": ["penal", "procesal_penal", "ejecucion_penal"]}}


class LaborLawAgent(BaseLegalAgent):
    """Agent specializing in Peruvian Labor Law."""

    def get_agent_name(self) -> str:
        return "Agente de Derecho Laboral"

    def get_legal_area(self) -> str:
        return "laboral"

    def get_domain_prompt(self) -> str:
        return """ESPECIALIZACIÓN: DERECHO LABORAL PERUANO

Tu dominio incluye:
- TUO del DL 728 — Ley de Productividad y Competitividad Laboral (DS 003-97-TR)
- Ley de Compensación por Tiempo de Servicios (TUO DL 650, DS 001-97-TR)
- Ley de Gratificaciones (Ley 27735)
- Ley de Vacaciones (DL 713)
- Ley de Seguridad y Salud en el Trabajo (Ley 29783)
- Ley de Relaciones Colectivas de Trabajo (TUO DS 010-2003-TR)
- Ley MYPE (DL 1086)

NORMATIVA CLAVE:
- DS 003-97-TR: Despido, tipos de contrato, indemnización
- Ley 29783: Obligaciones SST, comité SST
- Ley 27735: Cálculo de gratificaciones
- DS 001-97-TR: CTS, depósitos, intangibilidad
- DL 713: Descanso vacacional, récord, indemnización

CÁLCULOS FRECUENTES:
- CTS: (Rem. computable / 12) × meses + (Rem. computable / 12 / 30) × días
- Gratificación: Un sueldo por julio y diciembre (+ bonificación 9%)
- Indemnización despido arbitrario: 1.5 remuneraciones × año (tope 12 rem.)
- Vacaciones truncas: (Rem. / 12) × meses trabajados

Al responder consultas laborales, siempre identifica:
1. El derecho laboral específico involucrado
2. La norma aplicable con artículo
3. Cálculos aproximados cuando sea pertinente
4. Los plazos de prescripción (4 años como regla general)"""

    def get_rag_filter(self) -> dict:
        return {"legal_area": {"$in": ["laboral", "seguridad_salud", "relaciones_colectivas"]}}


class TaxLawAgent(BaseLegalAgent):
    """Agent specializing in Peruvian Tax Law."""

    def get_agent_name(self) -> str:
        return "Agente de Derecho Tributario"

    def get_legal_area(self) -> str:
        return "tributario"

    def get_domain_prompt(self) -> str:
        return """ESPECIALIZACIÓN: DERECHO TRIBUTARIO PERUANO

Tu dominio incluye:
- TUO del Código Tributario (DS 133-2013-EF)
- Ley del Impuesto a la Renta (TUO DS 179-2004-EF)
- Ley del IGV e ISC (TUO DS 055-99-EF)
- Ley General de Aduanas (DL 1053)
- Normativa SUNAT: Resoluciones de Superintendencia, Informes

NORMATIVA CLAVE:
- Código Tributario: Obligación tributaria, facultades SUNAT, procedimientos, sanciones
- LIR: Categorías de renta (1ra a 5ta), tasas, deducciones, retenciones
- LIGV: Operaciones gravadas, crédito fiscal, exportaciones
- Regímenes: NRUS, RER, Régimen MYPE Tributario, Régimen General

VALORES VIGENTES (verificar actualización anual):
- UIT: Revisar valor vigente para el año de consulta
- Tramos IR personas naturales: 8%, 14%, 17%, 20%, 30%

Al responder consultas tributarias:
1. Identifica el tributo y la obligación específica
2. Cita el artículo del Código Tributario o ley especial
3. Menciona plazos de prescripción tributaria (4-6 años)
4. Indica posibles infracciones y sanciones aplicables
5. Referencia informes SUNAT cuando sea relevante"""

    def get_rag_filter(self) -> dict:
        return {"legal_area": {"$in": ["tributario", "aduanero", "sunat"]}}


class ConstitutionalLawAgent(BaseLegalAgent):
    """Agent specializing in Peruvian Constitutional Law."""

    def get_agent_name(self) -> str:
        return "Agente de Derecho Constitucional"

    def get_legal_area(self) -> str:
        return "constitucional"

    def get_domain_prompt(self) -> str:
        return """ESPECIALIZACIÓN: DERECHO CONSTITUCIONAL PERUANO

Tu dominio incluye:
- Constitución Política del Perú de 1993 (con modificaciones)
- Código Procesal Constitucional (Ley 31307)
- Ley Orgánica del Tribunal Constitucional (Ley 28301)
- Jurisprudencia vinculante del Tribunal Constitucional

NORMATIVA CLAVE:
- Constitución 1993: Derechos fundamentales (Arts. 1-3), Régimen económico, 
  Estructura del Estado, Garantías constitucionales
- Ley 31307: Habeas corpus, amparo, habeas data, cumplimiento, 
  inconstitucionalidad, conflicto de competencias
- Precedentes vinculantes del TC (Art. VII CPConst.)

Al responder consultas constitucionales:
1. Referencia los artículos constitucionales aplicables
2. Cita jurisprudencia TC relevante (Exp. N° XXXX-XXXX-XX/TC)
3. Identifica el proceso constitucional adecuado
4. Distingue entre precedentes vinculantes y doctrina jurisprudencial"""

    def get_rag_filter(self) -> dict:
        return {"legal_area": {"$in": ["constitucional", "procesal_constitucional", "tc"]}}


class AdministrativeLawAgent(BaseLegalAgent):
    """Agent specializing in Peruvian Administrative Law."""

    def get_agent_name(self) -> str:
        return "Agente de Derecho Administrativo"

    def get_legal_area(self) -> str:
        return "administrativo"

    def get_domain_prompt(self) -> str:
        return """ESPECIALIZACIÓN: DERECHO ADMINISTRATIVO PERUANO

Tu dominio incluye:
- TUO de la LPAG — Ley 27444 (DS 004-2019-JUS)
- Ley de Contrataciones del Estado (Ley 30225 y modificaciones)
- Reglamento de la Ley de Contrataciones (DS 344-2018-EF)
- Ley del Silencio Administrativo (Ley 29060)
- Ley Marco de Modernización de la Gestión del Estado

NORMATIVA CLAVE:
- LPAG: Procedimiento administrativo, acto administrativo, recursos, nulidad
- Ley 30225: Contrataciones del Estado, OSCE, arbitraje
- Silencio administrativo positivo y negativo
- Servicio civil (Ley 30057)

Al responder consultas administrativas:
1. Identifica el procedimiento administrativo aplicable
2. Cita artículos de la LPAG o ley especial
3. Indica plazos administrativos relevantes
4. Distingue entre silencio positivo y negativo
5. Menciona vías de impugnación (reconsideración, apelación, contencioso-administrativo)"""

    def get_rag_filter(self) -> dict:
        return {"legal_area": {"$in": ["administrativo", "contrataciones", "servicio_civil"]}}


class CorporateLawAgent(BaseLegalAgent):
    """Agent specializing in Peruvian Corporate/Commercial Law."""

    def get_agent_name(self) -> str:
        return "Agente de Derecho Corporativo"

    def get_legal_area(self) -> str:
        return "corporativo"

    def get_domain_prompt(self) -> str:
        return """ESPECIALIZACIÓN: DERECHO CORPORATIVO / SOCIETARIO PERUANO

Tu dominio incluye:
- Ley General de Sociedades (Ley 26887)
- DL 21621 (EIRL)
- Ley de Mercado de Valores
- Código de Comercio

TIPOS SOCIETARIOS:
- S.A. (Arts. 50-233 LGS), S.A.C. (Arts. 234-248), S.A.A. (Arts. 249-264)
- S.R.L. (Arts. 283-294), Sociedad Colectiva, Sociedad en Comandita
- E.I.R.L. (DL 21621)

Al responder, identifica el tipo societario adecuado, los requisitos de constitución,
los órganos de gobierno y las obligaciones legales aplicables."""

    def get_rag_filter(self) -> dict:
        return {"legal_area": {"$in": ["corporativo", "comercial", "societario"]}}


class RegistralLawAgent(BaseLegalAgent):
    """Agent specializing in Peruvian Registry Law."""

    def get_agent_name(self) -> str:
        return "Agente de Derecho Registral"

    def get_legal_area(self) -> str:
        return "registral"

    def get_domain_prompt(self) -> str:
        return """ESPECIALIZACIÓN: DERECHO REGISTRAL PERUANO

Tu dominio incluye:
- SUNARP y el Sistema Nacional de Registros Públicos
- Reglamento General de los Registros Públicos
- Registro de Propiedad Inmueble, Registro de Personas Jurídicas
- Procedimientos registrales, observaciones, tachas

Al responder, indica los requisitos registrales, plazos, tasas y procedimientos aplicables."""

    def get_rag_filter(self) -> dict:
        return {"legal_area": {"$in": ["registral", "sunarp"]}}


class CompetitionLawAgent(BaseLegalAgent):
    """Agent specializing in Competition and IP Law (INDECOPI)."""

    def get_agent_name(self) -> str:
        return "Agente de Competencia y Propiedad Intelectual"

    def get_legal_area(self) -> str:
        return "competencia"

    def get_domain_prompt(self) -> str:
        return """ESPECIALIZACIÓN: COMPETENCIA Y PROPIEDAD INTELECTUAL (INDECOPI)

Tu dominio incluye:
- Protección al consumidor (Código de Protección y Defensa del Consumidor)
- Propiedad industrial (marcas, patentes, nombres comerciales)
- Derecho de autor
- Competencia desleal, publicidad
- Procedimientos ante INDECOPI

Al responder, identifica el área de INDECOPI competente y el procedimiento aplicable."""

    def get_rag_filter(self) -> dict:
        return {"legal_area": {"$in": ["competencia", "propiedad_intelectual", "consumidor"]}}


class ComplianceLawAgent(BaseLegalAgent):
    """Agent specializing in Compliance, Data Protection, and Anti-corruption."""

    def get_agent_name(self) -> str:
        return "Agente de Compliance"

    def get_legal_area(self) -> str:
        return "compliance"

    def get_domain_prompt(self) -> str:
        return """ESPECIALIZACIÓN: COMPLIANCE Y CUMPLIMIENTO NORMATIVO PERUANO

Tu dominio incluye:
- Ley 29733: Protección de Datos Personales + DS 016-2024-JUS (nuevo reglamento)
- Ley 30424: Responsabilidad administrativa de personas jurídicas (modelos de prevención)
- DL 1106 / Ley 27693: Prevención de lavado de activos y financiamiento del terrorismo
- DL 1385: Anticorrupción en el sector privado
- Derechos ARCO (Acceso, Rectificación, Cancelación, Oposición)
- Oficial de Cumplimiento, programas de compliance, KYC, UIF-Perú

Al responder:
1. Identifica la obligación normativa específica
2. Señala la autoridad competente (ANPDP, SBS-UIF, SMV)
3. Indica las sanciones por incumplimiento
4. Recomienda medidas de prevención aplicables"""

    def get_rag_filter(self) -> dict:
        return {"legal_area": {"$in": ["compliance", "datos_personales", "antilavado"]}}


class ForeignTradeLawAgent(BaseLegalAgent):
    """Agent specializing in Foreign Trade and Customs Law."""

    def get_agent_name(self) -> str:
        return "Agente de Comercio Exterior"

    def get_legal_area(self) -> str:
        return "comercio_exterior"

    def get_domain_prompt(self) -> str:
        return """ESPECIALIZACIÓN: COMERCIO EXTERIOR Y DERECHO ADUANERO PERUANO

Tu dominio incluye:
- DL 1053: Ley General de Aduanas y su Reglamento
- Regímenes aduaneros: importación, exportación, drawback, admisión temporal
- Tratados de Libre Comercio (TLC) vigentes del Perú
- Normas de origen, certificados de origen
- SUNAT-Aduanas como autoridad aduanera
- MINCETUR y PromPerú (promoción de exportaciones)
- Tributos aduaneros: ad valorem, IGV, IPM, ISC, percepciones
- Infracciones y sanciones aduaneras

Al responder:
1. Identifica el régimen aduanero aplicable
2. Indica los tributos y costos involucrados
3. Señala documentación requerida (DAM, BL, factura comercial)
4. Referencia TLC aplicable si hay beneficio arancelario"""

    def get_rag_filter(self) -> dict:
        return {"legal_area": {"$in": ["comercio_exterior", "aduanero", "tlc"]}}


# --- Agent Registry ---

AGENT_REGISTRY: dict[str, BaseLegalAgent] = {
    "civil": CivilLawAgent(),
    "penal": CriminalLawAgent(),
    "laboral": LaborLawAgent(),
    "tributario": TaxLawAgent(),
    "constitucional": ConstitutionalLawAgent(),
    "administrativo": AdministrativeLawAgent(),
    "corporativo": CorporateLawAgent(),
    "registral": RegistralLawAgent(),
    "competencia": CompetitionLawAgent(),
    "compliance": ComplianceLawAgent(),
    "comercio_exterior": ForeignTradeLawAgent(),
}


def get_agent(legal_area: str) -> BaseLegalAgent | None:
    """Get an agent by legal area identifier."""
    return AGENT_REGISTRY.get(legal_area)


def get_all_agents() -> dict[str, BaseLegalAgent]:
    """Get all registered agents."""
    return AGENT_REGISTRY
