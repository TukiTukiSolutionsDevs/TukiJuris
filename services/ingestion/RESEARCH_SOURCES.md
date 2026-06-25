# Peruvian Legal Sources — Scraping Feasibility Research

> Investigación rápida (~2–3 min/fuente) sobre acceso programático a fuentes oficiales peruanas para alimentar el corpus RAG de TukiJuris.
> Fecha: 2026-06-24. Verificar URLs antes de implementar scraper — pueden cambiar.

Leyenda: **Acceso** = static HTML / SPA-JS / API / RSS / sitemap / PDF-listing. **Verdict**: Easy ≤1 día scraper, Medium 2–5 días, Hard semanas / requiere navegador headless / captcha, Unknown.

---

## A. Universales (normativa nacional consolidada)

| # | Fuente | URL real listado/búsqueda | Acceso | Paginación | Formato | Endpoint programático | Verdict |
|---|---|---|---|---|---|---|---|
| 1 | SPIJ MINJUS | `https://spijweb.minjus.gob.pe/` (portal) + `https://spij.minjus.gob.pe/` (consulta directa) | SPA-JS sobre backend ASP. Consulta requiere sesión + filtros server-side; algunas vistas exigen suscripción institucional para texto consolidado completo | Form POST con paginación oculta (viewstate-style) | HTML + PDF | ❌ No hay API pública. Texto consolidado es el diferencial — los gratuitos solo dan versión histórica | **Hard** (SPA + sesión + posibles límites legales de uso) |
| 2 | El Peruano — Normas Legales | `https://diariooficial.elperuano.pe/Normas/normasactualizadas` y `https://diariooficial.elperuano.pe/normas` | Static HTML + index diario; PDFs de edición completa por fecha | Paginación por fecha (`?fecha=DD/MM/YYYY`) y por número de norma | PDF (edición) + HTML (extracto) | Index navegable; cada edición tiene PDF descargable. No hay API JSON | **Easy–Medium** (URL pattern predecible por fecha; OCR para PDFs antiguos) |
| 3 | Plataforma del Estado — gob.pe normas | `https://www.gob.pe/busquedas?contenido[]=normas` (+ `institucion[]=<slug>`) | Server-rendered HTML con filtros via query string | Query strings: `?contenido[]=normas&institucion[]=sunat&page=N` | HTML listing + PDF adjunto por norma | Buscador unificado del Estado — query params estables, sin API pero scrapeable directamente | **Easy** (query string limpio, paginación numérica, agrupa casi todas las entidades) |

---

## B. Tribunales y jurisprudencia

| # | Fuente | URL real listado/búsqueda | Acceso | Paginación | Formato | Endpoint programático | Verdict |
|---|---|---|---|---|---|---|---|
| 4 | Tribunal Constitucional | `https://jurisprudencia.sedetc.gob.pe/sistematizacion-jurisprudencial` (buscador nuevo) + `https://www.tc.gob.pe/jurisprudencia` | SPA-JS (buscador 2025 con IA semántica) | Scroll/AJAX paginado | HTML ficha + PDF sentencia | Buscador semántico oficial; no expone API documentada pero llamadas XHR son interceptables | **Medium** (SPA — usar Playwright o reverse-engineer XHR endpoint) |
| 5 | Poder Judicial (Jurisprudencia Sistematizada / casaciones) | `https://www.pj.gob.pe/wps/wcm/connect/cij-juris/s_jurisprudencia_sistematizada` + `.../as_casaciones_publicadas_peruano/casaciones_publicadas` | WCM-portal (IBM WebSphere) — HTML server-side con sesiones JSESSIONID | Form POST con `wcm_page.parameters` | HTML ficha + PDF resolución; export Excel disponible en UI | No hay API; portal exporta Excel — útil como bulk seed | **Medium** (WCM session handling + Excel export como atajo) |
| 6 | Tribunal Fiscal (MEF) | `https://www.mef.gob.pe/es/jurisprudencia/acuerdos-de-sala-plena-y-resoluciones-de-observancia-obligatoria` + `https://www.gob.pe/57981-jurisprudencia-tribunal-fiscal` | Static HTML con listados anuales + PDFs adjuntos directos | Por año + listado plano | PDF (RTFs OO desde 1980) | URL pattern por año/expediente; sin API pero descarga directa por archivo | **Easy** (PDFs servidos estáticamente, índices anuales) |
| 7 | Tribunal Registral SUNARP | `https://scr.sunarp.gob.pe/sip` (Sistema Integrado de Precedentes) | SPA-JS con filtros (Registro, materia, fecha) sobre backend SCR | AJAX/JSON interno | HTML + PDF resolución | XHR interno consultable; el SIP es la fuente oficial estructurada | **Medium** (sniff XHR del SIP, paginar por filtros) |
| 8 | Tribunal de Contrataciones del Estado (OSCE/OECE) | `https://www.gob.pe/institucion/oece/colecciones/716-resoluciones-del-tribunal-de-contrataciones-del-estado` | Static HTML (gob.pe colecciones) | `?sheet=N` paginación numérica | HTML ficha + PDF resolución | Mismo patrón gob.pe colecciones; predecible | **Easy** (colección gob.pe — patrón uniforme con otras instituciones) |
| 9 | Tribunal del Servicio Civil (SERVIR) | `https://www.gob.pe/40281-buscar-las-resoluciones-emitidas-por-el-tribunal-del-servicio-civil-tsc` + colecciones `/institucion/servir/colecciones/1680...` y `1800` | Buscador dedicado (form server-side) + colecciones gob.pe paralelas | Form filters + colecciones `?sheet=N` | HTML + PDF | Buscador con 8 filtros — accesible via GET con query string | **Easy** (doble vía: buscador formal o colecciones gob.pe) |
| 10 | Tribunal de Fiscalización Ambiental (OEFA) | `https://repositorio.oefa.gob.pe/browse/title?scope=...` (DSpace) | DSpace (estándar académico) — REST API disponible | DSpace REST API + sword endpoints | PDF resolución + metadata DC | ✅ DSpace expone `/rest/items`, `/rest/collections` — API JSON estable | **Easy** (DSpace REST API es ideal para ingestion automatizada) |

---

## C. Reguladores con resoluciones

| # | Fuente | URL real listado/búsqueda | Acceso | Paginación | Formato | Endpoint programático | Verdict |
|---|---|---|---|---|---|---|---|
| 11 | SUNAT | `https://www.sunat.gob.pe/legislacion/general/index.html` + `/legislacion/superAdjunta/rsnati/index.html` + `https://www.gob.pe/institucion/sunat/normas-legales` | Static HTML por materia (IGV, Renta, Código Tributario…) + colección gob.pe | Index por sección, sin paginación numérica clásica | HTML + PDF | Doble vía: SUNAT legacy estático + gob.pe colecciones (preferir gob.pe) | **Easy** (gob.pe institucion/sunat) |
| 12 | INDECOPI | `https://www.gob.pe/10720-buscar-resoluciones-del-indecopi` + buscador semántico `https://consumidor.gob.pe/2026/04/06/buscador-semantico-de-resoluciones` | Buscador oficial via gob.pe; nuevo buscador semántico con IA (2026) | Query string + AJAX en buscador semántico | HTML + PDF resolución | Buscador semántico IA — probable API JSON detrás (sin documentar aún) | **Medium** (sniff XHR del buscador semántico; o usar gob.pe estable) |
| 13 | ANPDP | `https://www.gob.pe/institucion/anpd/normas-legales` + búsqueda `gob.pe/busquedas?contenido[]=normas&institucion=anpd` | Static HTML colección gob.pe (institución migrada a slug `anpd`) | `?sheet=N` | HTML + PDF | Patrón uniforme gob.pe; resoluciones de procedimientos trilaterales desde 2013 | **Easy** (gob.pe colección estándar) |
| 14 | SBS | `https://www.sbs.gob.pe/app/pp/INT_CN/Paginas/Busqueda/BusquedaPortal.aspx` | ASP.NET WebForms con viewstate + filtros radgrid | `rdgUltimaVersionNormasChangePage=N_20` (RadGrid pages) | HTML ficha + PDF | ❌ Sin API; requiere manejo viewstate + eventtarget. Tiene "buscador de normas" oficial | **Medium** (WebForms — usar requests con viewstate o Playwright) |
| 15 | SMV | `https://www.smv.gob.pe/ServicioConsultaNormas/Frm_sil_actualizaciones` + `/SIMV/Frm_Resoluciones` | ASP.NET con tokens en query `?data=<hex>` (token aparentemente estático por sección) | Listado tabular único | HTML + PDF | URLs con token persistente; tabla scrapeable directa | **Easy** (HTML tabular, scraping clásico) |
| 16 | OSCE — Opiniones DTN | `https://www.gob.pe/institucion/osce/colecciones/713-opiniones` (y `oece/colecciones/713-opiniones-de-la-direccion-tecnico-normativa-osce`) | Colección gob.pe estándar | `?sheet=N` | HTML + PDF Opinión | Patrón uniforme | **Easy** |
| 17 | MINAM | `https://www.gob.pe/institucion/minam/normas-legales` (patrón gob.pe) | Static HTML colección gob.pe | `?sheet=N` | HTML + PDF | Patrón estándar | **Easy** |
| 18 | OEFA (reglamentario) | `https://www.gob.pe/institucion/oefa/normas-legales` + repositorio DSpace para resoluciones del TFA (ver #10) | Static HTML + DSpace REST | gob.pe `?sheet=N` / DSpace REST offset | HTML + PDF | DSpace REST + colección gob.pe | **Easy** |
| 19 | OSINERGMIN | `https://www.osinergmin.gob.pe/Resoluciones/Resoluciones-GRT-<YEAR>.aspx` + `https://www.gob.pe/institucion/osinergmin/colecciones/5240-resoluciones-del-consejo-directivo` | Static HTML por año (legacy) + colección gob.pe (recomendada) | Por año (legacy) / `?sheet=N` (gob.pe) | HTML + PDF resolución | gob.pe colección uniforme; legacy útil para histórico | **Easy** |
| 20 | OSIPTEL | `https://www.osiptel.gob.pe/buscador-de-normas-y-regulaciones?org=<>&cat=<>&anio=<>&input=<>` | Buscador propio con query string limpio (GET) | Query string + paginación numérica | HTML + PDF | URL pattern explícito y documentado en UI; no API pero scrapeable trivial | **Easy** (query string GET directo — ideal) |
| 21 | MTC | `https://www.gob.pe/institucion/mtc/normas-legales` | Colección gob.pe estándar | `?sheet=N` | HTML + PDF | Patrón uniforme | **Easy** |
| 22 | MINSA / DIGEMID | `https://www.gob.pe/institucion/minsa/normas-legales` + `https://www.digemid.minsa.gob.pe/webDigemid/category/normas-legales` | gob.pe estándar (MINSA) + WordPress (DIGEMID, `/category/normas-legales`) | gob.pe `?sheet=N` / WP `/page/N/` | HTML + PDF | DIGEMID es WordPress → expone `/wp-json/wp/v2/posts?categories=<id>` (probable) | **Easy** (WP REST API en DIGEMID; gob.pe en MINSA) |
| 23 | SUSALUD | `https://www.gob.pe/institucion/susalud/normas-legales` + `/normas-legales/tipos/63-resolucion-de-superintendencia` | Colección gob.pe | `?sheet=N` | HTML + PDF | Patrón uniforme | **Easy** |
| 24 | SUNAFIL | `https://www.gob.pe/institucion/sunafil/normas-legales` (+ `/tipos/63-resolucion-de-superintendencia`) y buscador resoluciones inspección | Colección gob.pe + buscador específico | `?sheet=N` | HTML + PDF | Patrón uniforme + buscador secundario para resoluciones de inspección | **Easy** |
| 25 | SUNARP (normativa general) | `https://www.sunarp.gob.pe/qsec-nxnumdoc.asp` + `https://www.gob.pe/institucion/sunarp/normas-legales` + SCR Sunarp compendios | Legacy ASP estático + gob.pe + compendios PDF anuales | `?ID=<N>` legacy / `?sheet=N` gob.pe | HTML + PDF + Compendios PDF | gob.pe + compendio PDF como bulk seed | **Easy** |

---

## Hallazgos transversales / estrategia recomendada

1. **gob.pe colecciones es el patrón dominante** (entidades 3, 8, 9, 11–13, 16–25): URL pattern `https://www.gob.pe/institucion/<slug>/normas-legales` o `/colecciones/<id>-<nombre>?sheet=N`. Un único scraper parametrizado por `(slug, sheet)` cubre ~70% de las fuentes. **Build first.**
2. **El Peruano** (fuente #2) es la fuente primaria de publicación oficial — descarga de PDF por fecha permite reconstruir corpus histórico completo con OCR.
3. **DSpace en OEFA** (fuente #10) ofrece REST API estándar — modelo a replicar si otras entidades migran.
4. **SPIJ MINJUS** (fuente #1) es el mayor desafío y el mayor valor (textos consolidados). Evaluar si licencia institucional / convenio MINJUS es viable antes de invertir en scraper. Sin texto consolidado, hay que reconstruir consolidación desde El Peruano + modificatorias (compleja, error-prone).
5. **SBS** (fuente #14) requiere manejo ASP.NET WebForms — único caso con verdadero overhead técnico fuera de SPIJ.
6. **TC nuevo buscador** (fuente #4) y **INDECOPI semántico** (fuente #12) son SPAs recientes con IA — reverse-engineer XHR ahora antes de que añadan rate limiting.
7. **Riesgos legales**: revisar términos de uso de cada portal antes de scraping masivo. SPIJ y El Peruano explícitamente prohíben reuso comercial de versiones consolidadas en algunos contextos → relevante para BYOK Empresarial.

## Orden de implementación sugerido

1. **Sprint 1 — gob.pe scraper genérico** (cubre 17 de 25 fuentes con un solo módulo).
2. **Sprint 2 — El Peruano PDF + OCR** (fuente primaria histórica).
3. **Sprint 3 — DSpace OEFA + OSIPTEL buscador GET** (alta jurisprudencia ambiental + telecom).
4. **Sprint 4 — Playwright/headless workers** para TC, INDECOPI semántico, SUNARP SIP.
5. **Sprint 5 — SBS WebForms + WCM Poder Judicial** (más complejo, dejar al final).
6. **Aparte — Decisión estratégica SPIJ**: evaluar convenio MINJUS antes de scraping.
