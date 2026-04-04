# AGENTE DERECHO — Plan Maestro de Desarrollo
## Plataforma Jurídica Inteligente para el Derecho Peruano

> **Versión**: 1.0  
> **Fecha**: 2 de Abril, 2026  
> **Duración estimada**: 24 sprints (~12 meses)  
> **Sprints de 2 semanas**

---

## 1. VISIÓN DEL PRODUCTO

### 1.1 Qué es Agente Derecho

Un **ecosistema jurídico inteligente** especializado exclusivamente en el derecho peruano. No es un chatbot legal genérico — es una plataforma con agentes especializados por rama del derecho, coordinados por un orquestador central, capaz de:

- **Consultar** normativa peruana organizada y actualizada
- **Interpretar** normas en contexto legal específico
- **Guiar** al usuario hacia la rama del derecho correcta
- **Cruzar** criterios cuando un caso involucra múltiples áreas
- **Citar** fuentes oficiales con referencias verificables

### 1.2 Qué NO es

- No es asesoría legal (disclaimer obligatorio)
- No es un buscador de documentos más
- No depende de un único proveedor de IA
- No reemplaza al abogado — lo potencia

### 1.3 Usuarios Objetivo

| Segmento | Necesidad Principal |
|----------|-------------------|
| Abogados independientes | Consulta rápida de normativa, jurisprudencia y criterios |
| Estudios de abogados | Investigación legal profunda, análisis de casos multi-rama |
| Departamentos legales corporativos | Compliance, normativa sectorial, contrataciones del Estado |
| Estudiantes de derecho | Aprendizaje, consulta de códigos y principios |
| Empresarios/emprendedores | Orientación legal básica para decisiones de negocio |

---

## 2. ARQUITECTURA TÉCNICA

### 2.1 Stack Tecnológico

```
┌─────────────────────────────────────────────────┐
│                   FRONTEND                       │
│           Next.js 15+ / TypeScript              │
│     Tailwind CSS + shadcn/ui + Vercel AI SDK    │
└──────────────────────┬──────────────────────────┘
                       │ HTTPS/WebSocket
┌──────────────────────▼──────────────────────────┐
│                 API GATEWAY                       │
│              Python FastAPI (async)              │
│          Auth + Rate Limiting + Logging          │
└──────────┬───────────┬──────────────────────────┘
           │           │
    ┌──────▼───┐  ┌────▼──────────────────────────┐
    │ Auth     │  │     AI ORCHESTRATION LAYER     │
    │ Supabase │  │         LangGraph              │
    │ Auth     │  │  (State Machine / Graph-based) │
    │          │  └────┬───┬───┬───┬───┬───┬──────┘
    └──────────┘       │   │   │   │   │   │
              ┌────────▼───▼───▼───▼───▼───▼──────┐
              │      DOMAIN AGENTS (Specialized)    │
              │  Civil│Penal│Laboral│Tributario│... │
              └────────┬───────────────────────────┘
                       │
    ┌──────────────────▼──────────────────────────┐
    │              RAG PIPELINE                     │
    │  Query → Embed → Retrieve → Rerank → Answer │
    └──────┬───────────┬──────────────────────────┘
           │           │
    ┌──────▼───┐  ┌────▼──────────────────────────┐
    │ Vector   │  │       LLM ADAPTER LAYER       │
    │ Database │  │         (LiteLLM)              │
    │ pgvector │  │  OpenAI│Anthropic│Google│Local │
    └──────────┘  └───────────────────────────────┘
           │
    ┌──────▼──────────────────────────────────────┐
    │           POSTGRESQL (Supabase)              │
    │  Users│Docs│Conversations│Analytics│Billing  │
    └─────────────────────────────────────────────┘
```

### 2.2 Decisiones Técnicas y Justificación

| Decisión | Elección | Alternativas Descartadas | Razón |
|----------|----------|-------------------------|-------|
| **Backend** | Python FastAPI | Spring Boot, Django, Express | Ecosistema AI nativo, async-first, LangChain/LangGraph nativos, rendimiento superior para AI workloads |
| **Frontend** | Next.js 15+ TypeScript | React SPA, Angular, Vue | SSR, streaming nativo para chat, Vercel AI SDK, ecosistema más grande |
| **Orquestación AI** | LangGraph | CrewAI, AutoGen | Graph-based con estado persistente, ideal para routing legal complejo, ciclos de refinamiento, model-agnostic |
| **Vector DB** | pgvector (inicio) → Qdrant (escala) | Pinecone, Weaviate, Chroma | pgvector simplifica infraestructura (mismo PostgreSQL), migración a Qdrant cuando se necesite escala |
| **LLM Adapter** | LiteLLM | Directo a cada API | Abstracción model-agnostic, fallback automático, logging unificado, 100+ modelos soportados |
| **Base de datos** | PostgreSQL (Supabase) | MySQL, MongoDB | RLS nativo, auth integrado, pgvector incluido, realtime, storage para PDFs |
| **Búsqueda** | Híbrida (BM25 + Vector) | Solo vector, solo keyword | Significativamente más preciso para documentos legales con terminología específica |
| **Auth** | Supabase Auth | Keycloak, Auth0, NextAuth | Integrado con la DB, RLS, social login, SSO enterprise en plan pro |
| **Deployment** | Docker + Railway/Render → AWS | Vercel solo, Heroku | Necesitamos GPU eventual para modelos locales, control de infra |
| **Cache** | Redis (Upstash) | Memcached | Pub/sub para streaming, rate limiting, session cache |

### 2.3 Arquitectura de Agentes

```
                    ┌─────────────┐
                    │ ORQUESTADOR │
                    │  (LangGraph) │
                    │             │
                    │ • Clasifica │
                    │ • Enruta    │
                    │ • Integra   │
                    │ • Valida    │
                    └──────┬──────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
   ┌────▼────┐       ┌────▼────┐       ┌────▼────┐
   │ Agente  │       │ Agente  │       │ Agente  │
   │ Civil   │       │ Penal   │       │ Laboral │
   │         │       │         │       │         │
   │ CC, CPC │       │ CP, CPP │       │ LPCL,   │
   │ Familia │       │ Ejec.   │       │ LRCT,   │
   │ Sucesión│       │ Penal   │       │ Seguridad│
   └─────────┘       └─────────┘       └─────────┘
        │                  │                  │
   ┌────▼────┐       ┌────▼────┐       ┌────▼────┐
   │ Agente  │       │ Agente  │       │ Agente  │
   │Tributar.│       │ Admin.  │       │Corporat.│
   │         │       │         │       │         │
   │ CT,     │       │ LPAG,   │       │ LGS,    │
   │ LIR,    │       │ Contra- │       │ LMV,    │
   │ IGV,    │       │ taciones│       │ Ley     │
   │ SUNAT   │       │ TUO     │       │ MYPE    │
   └─────────┘       └─────────┘       └─────────┘
        │                  │                  │
   ┌────▼────┐       ┌────▼────┐       ┌────▼────┐
   │ Agente  │       │ Agente  │       │ Agente  │
   │Constit. │       │Registral│       │ Comercio│
   │         │       │         │       │ Exterior│
   │ Const.  │       │ Ley Reg.│       │         │
   │ 1993,   │       │ SUNARP  │       │ Aduanas │
   │ TC      │       │         │       │ MINCETUR│
   └─────────┘       └─────────┘       └─────────┘
        │                  │
   ┌────▼────┐       ┌────▼────┐
   │ Agente  │       │ Agente  │
   │Compet./ │       │Complian.│
   │  PI     │       │         │
   │         │       │ Dat.Per.│
   │INDECOPI │       │ Anticorr│
   │         │       │ Lavado  │
   └─────────┘       └─────────┘
```

#### Flujo del Orquestador:

```
Usuario: "Mi empleador no me pagó la liquidación después del despido"

1. CLASIFICACIÓN → Orquestador identifica: LABORAL (primario), TRIBUTARIO (secundario)
2. ENRUTAMIENTO → Activa Agente Laboral como principal
3. CONSULTA RAG → Agente busca en LPCL, DS 003-97-TR, jurisprudencia
4. ENRIQUECIMIENTO → Orquestador activa Agente Tributario para implicaciones fiscales
5. INTEGRACIÓN → Combina respuestas en formato coherente
6. VALIDACIÓN → Verifica citaciones, coherencia legal
7. RESPUESTA → Entrega al usuario con fuentes citadas
```

---

## 3. FUENTES DE DATOS DEL DERECHO PERUANO

### 3.1 Fuentes Primarias (Normativa)

| Fuente | URL | Tipo | Acceso | Prioridad |
|--------|-----|------|--------|-----------|
| **SPIJ** | spijweb.minjus.gob.pe | Legislación sistematizada | Parcial libre / Suscripción completa | CRÍTICA |
| **El Peruano** | diariooficial.elperuano.pe | Diario oficial, normas legales | Público | CRÍTICA |
| **Congreso** | leyes.congreso.gob.pe | Proyectos y leyes aprobadas | Público | ALTA |
| **Constitución 1993** | tc.gob.pe | Texto constitucional | Público | CRÍTICA |

### 3.2 Fuentes de Jurisprudencia

| Fuente | URL | Tipo | Prioridad |
|--------|-----|------|-----------|
| **Tribunal Constitucional** | tc.gob.pe/jurisprudencia | Sentencias TC | CRÍTICA |
| **Corte Suprema** | jurisprudencia.pj.gob.pe | Casaciones, precedentes | CRÍTICA |
| **INDECOPI** | servicio.indecopi.gob.pe/buscadorResoluciones | Resoluciones competencia/PI | ALTA |
| **SUNAT** | sunat.gob.pe | Resoluciones tributarias, informes | ALTA |
| **SUNARP** | sunarp.gob.pe | Resoluciones registrales | MEDIA |
| **OSCE** | osce.gob.pe | Pronunciamientos contrataciones | MEDIA |
| **SBS** | sbs.gob.pe | Resoluciones financieras | MEDIA |

### 3.3 Fuentes Doctrinarias y Complementarias

| Fuente | Tipo | Uso |
|--------|------|-----|
| **LP Derecho** (lpderecho.pe) | Portal legal, códigos actualizados | Referencia, actualización |
| **Gaceta Jurídica** | Doctrina, comentarios | Enriquecimiento contextual |
| **Revistas PJ** (revistas.pj.gob.pe) | Artículos académicos | Análisis profundo |
| **PUCP/USMP/UPC Journals** | Investigación jurídica | Base doctrinal |

### 3.4 Códigos y Normas Principales por Agente

| Agente | Normativa Principal |
|--------|-------------------|
| **Civil** | Código Civil (1984), Código Procesal Civil, Ley 26887 (Familia), Código de Niños y Adolescentes |
| **Penal** | Código Penal (1991), Nuevo Código Procesal Penal, Código de Ejecución Penal |
| **Laboral** | TUO DL 728 (LPCL), DS 003-97-TR, Ley 29783 (SST), LRCT, Ley MYPE |
| **Tributario** | Código Tributario, Ley IR, Ley IGV, Ley Aduanas, normas SUNAT |
| **Administrativo** | TUO LPAG (Ley 27444), Ley Contrataciones del Estado, Ley Silencio Administrativo |
| **Corporativo** | LGS (Ley 26887), Ley de Mercado de Valores, Ley MYPE, Código de Comercio |
| **Constitucional** | Constitución 1993, Código Procesal Constitucional, Ley Orgánica TC |
| **Registral** | Ley 26366, Reglamento General Registros Públicos, TUO Registro de Propiedad |
| **Competencia/PI** | Ley de Competencia, Ley de Propiedad Industrial, Ley Derecho de Autor |
| **Compliance** | Ley 29733 (Datos Personales) + DS 016-2024-JUS, Ley 30424 (Responsabilidad Administrativa PJ), Normas Antilavado |
| **Comercio Exterior** | Ley General de Aduanas, TLC vigentes, normas MINCETUR |

---

## 4. PIPELINE DE DATOS (RAG)

### 4.1 Arquitectura del Pipeline

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  INGESTION   │───▶│  PROCESSING  │───▶│   INDEXING    │
│              │    │              │    │              │
│ • Scrapers   │    │ • PDF Parse  │    │ • Chunking   │
│ • API calls  │    │ • HTML Parse │    │ • Embedding  │
│ • RSS feeds  │    │ • OCR (old   │    │ • Metadata   │
│ • Manual     │    │   docs)      │    │ • pgvector   │
│   upload     │    │ • Clean text │    │   store      │
└──────────────┘    └──────────────┘    └──────────────┘
       │                    │                    │
       ▼                    ▼                    ▼
  ┌─────────┐        ┌──────────┐        ┌──────────┐
  │Scheduler│        │Unstructur│        │ Hybrid   │
  │ (daily/ │        │  ed.io + │        │ Search   │
  │ weekly) │        │ Custom   │        │ BM25 +   │
  └─────────┘        │ Parsers  │        │ Vector   │
                     └──────────┘        └──────────┘
```

### 4.2 Estrategia de Chunking Legal

Los documentos legales tienen una estructura jerárquica clara que debemos respetar:

```
Norma > Libro > Título > Capítulo > Sección > Artículo > Inciso

Ejemplo: Código Civil > Libro VII > Título IX > Capítulo I > Art. 1351
```

**Estrategia de chunking propuesta:**
- **Nivel artículo**: Cada artículo es un chunk base (con contexto de sección/capítulo)
- **Nivel sección**: Grupos de artículos relacionados como chunk amplio
- **Metadata obligatoria por chunk**:
  - `norma`: nombre completo de la norma
  - `tipo_norma`: ley, decreto_supremo, resolucion, sentencia, etc.
  - `area_derecho`: civil, penal, laboral, tributario, etc.
  - `articulo`: número de artículo
  - `fecha_publicacion`: fecha de publicación original
  - `fecha_modificacion`: última modificación
  - `vigente`: boolean
  - `fuente_url`: URL de la fuente original
  - `jerarquia`: constitucional, legal, reglamentario, etc.

### 4.3 Modelo de Embeddings

- **Producción**: `text-embedding-3-large` (OpenAI) — 3072 dimensiones
- **Alternativa local**: `bge-m3` (BAAI) — multilingüe, gratis, self-hosted
- **Reranking**: `cross-encoder/ms-marco-MiniLM-L-12-v2` o Cohere Rerank

---

## 5. PLAN POR SPRINTS

### FASE 0: FUNDACIÓN (Sprints 1-2) — Semanas 1-4

> **Objetivo**: Proyecto estructurado, CI/CD funcionando, esquemas de DB definidos

#### Sprint 1: Scaffolding y Arquitectura Base
- [ ] Inicializar monorepo con Turborepo o nx
  - `/apps/web` — Next.js 15+ frontend
  - `/apps/api` — FastAPI backend
  - `/packages/shared` — tipos compartidos
  - `/services/ingestion` — pipeline de datos
  - `/services/agents` — agentes de IA
- [ ] Configurar Docker Compose para desarrollo local
  - PostgreSQL + pgvector
  - Redis (Upstash local)
  - FastAPI (hot reload)
  - Next.js (dev server)
- [ ] Setup CI/CD con GitHub Actions
  - Linting (Ruff para Python, ESLint para TS)
  - Tests automáticos
  - Build verification
- [ ] Definir esquema base de PostgreSQL
  - `users`, `organizations`, `subscriptions`
  - `conversations`, `messages`
  - `documents`, `document_chunks`
  - `legal_areas`, `normative_sources`
- [ ] Configurar Supabase (Auth + Storage + DB)

#### Sprint 2: Autenticación y API Base
- [ ] Implementar auth flow completo (Supabase Auth)
  - Login/Register (email + password)
  - OAuth (Google, Microsoft)
  - Session management
  - Row Level Security (RLS) policies
- [ ] API base FastAPI
  - Health check
  - Auth middleware
  - CORS configuration
  - Rate limiting (Redis)
  - Error handling estándar
  - OpenAPI docs auto-generadas
- [ ] Frontend: Layout base
  - Auth pages (login/register)
  - Dashboard skeleton
  - Navigation structure
  - Theme system (light/dark)
- [ ] Testing foundation
  - pytest setup con fixtures
  - Vitest + React Testing Library
  - E2E básico con Playwright

**Entregable Sprint 2**: App funcionando con auth, API documentada, CI/CD verde.

---

### FASE 1: PIPELINE DE DATOS (Sprints 3-5) — Semanas 5-10

> **Objetivo**: Alimentar el sistema con normativa peruana real, procesada y lista para RAG

#### Sprint 3: Scrapers e Ingestion de Normativa
- [ ] Scraper para **El Peruano** (normas legales diarias)
  - Parser de PDFs del diario oficial
  - Extracción de metadata (número, tipo, fecha, materia)
  - Schedule de actualización diaria
- [ ] Scraper para **SPIJ** (legislación sistematizada)
  - Navegación de la estructura normativa
  - Extracción de textos completos con jerarquía
  - Manejo de normas con acceso libre
- [ ] Ingestion manual de Códigos principales (PDF → texto estructurado)
  - Constitución Política del Perú 1993
  - Código Civil 1984
  - Código Penal 1991
  - Código Procesal Civil
  - Nuevo Código Procesal Penal
- [ ] Storage de documentos raw en Supabase Storage
- [ ] Tabla `normative_documents` con metadata completa

#### Sprint 4: Procesamiento y Vectorización
- [ ] Pipeline de procesamiento de documentos
  - PDF parsing con Unstructured.io
  - HTML parsing para fuentes web
  - OCR para documentos escaneados (Tesseract)
  - Limpieza y normalización de texto legal
- [ ] Implementar chunking inteligente para documentos legales
  - Respeta estructura: Libro > Título > Capítulo > Artículo
  - Chunks con overlap contextual
  - Metadata enrichment automático
- [ ] Setup pgvector
  - Extension habilitada en PostgreSQL
  - Tabla `document_embeddings`
  - Índices HNSW para búsqueda rápida
- [ ] Generar embeddings iniciales
  - Embedding service (OpenAI text-embedding-3-large)
  - Batch processing para volúmenes grandes
  - Verificación de calidad de embeddings
- [ ] Implementar búsqueda híbrida base
  - BM25 (full-text search PostgreSQL nativo)
  - Vector similarity (pgvector)
  - Score fusion (RRF — Reciprocal Rank Fusion)

#### Sprint 5: Jurisprudencia y Fuentes Complementarias
- [ ] Scraper para **Tribunal Constitucional** (tc.gob.pe)
  - Sentencias, resoluciones
  - Metadata: expediente, fecha, ponente, materia
- [ ] Scraper para **Poder Judicial** — Corte Suprema
  - Casaciones, acuerdos plenarios, precedentes vinculantes
- [ ] Scraper para **INDECOPI** resoluciones
  - Competencia, propiedad intelectual, protección al consumidor
- [ ] Scraper para **SUNAT** normativa tributaria
  - Resoluciones, informes, directivas
- [ ] Pipeline completo de procesamiento para jurisprudencia
  - Extracción de ratio decidendi (fundamento clave)
  - Identificación de precedentes vinculantes
  - Clasificación por materia jurídica
- [ ] Dashboard de monitoreo del pipeline de datos
  - Documentos procesados por fuente
  - Errores de procesamiento
  - Cobertura por área del derecho

**Entregable Sprint 5**: Base de conocimiento con normativa principal peruana indexada y buscable. Mínimo: Constitución, 5 códigos principales, jurisprudencia TC + CS del último año.

---

### FASE 2: CORE AI — ORQUESTADOR Y PRIMER AGENTE (Sprints 6-8) — Semanas 11-16

> **Objetivo**: Sistema de IA funcional con orquestador y al menos 3 agentes dominio operativos

#### Sprint 6: LLM Adapter Layer y RAG Pipeline
- [ ] Implementar LiteLLM como capa de abstracción
  - Configuración para OpenAI (GPT-4o, GPT-4o-mini)
  - Configuración para Anthropic (Claude 3.5 Sonnet, Haiku)
  - Configuración para Google (Gemini 1.5 Pro)
  - Configuración para modelos locales (Ollama + Llama 3)
  - Fallback chain: si un modelo falla, usa el siguiente
  - Logging unificado de tokens, costos, latencia
- [ ] RAG Pipeline completo
  - Query preprocessing (expansión de consultas legales)
  - Retrieval (búsqueda híbrida BM25 + vector)
  - Reranking (cross-encoder)
  - Context assembly (armado de contexto con chunks relevantes)
  - Generation (prompt template legal especializado)
  - Post-processing (extracción de citas, formateo)
- [ ] Prompt templates base para consultas legales
  - System prompt del "abogado asistente peruano"
  - Template de citación de normas
  - Template de análisis jurisprudencial
  - Template de respuesta con disclaimer
- [ ] Evaluación de calidad RAG
  - Test set de 50 preguntas legales con respuestas esperadas
  - Métricas: groundedness, completeness, citation accuracy
  - Dashboard de métricas de calidad

#### Sprint 7: Orquestador Central (LangGraph)
- [ ] Diseñar el grafo del orquestador en LangGraph
  ```
  START → classify_query → route_to_agent → [agent_execution] 
    → validate_response → check_multi_domain → enrich_if_needed 
    → format_response → END
  ```
- [ ] Nodo de Clasificación Legal
  - Clasificador de área del derecho (fine-tuned o few-shot)
  - Detección de consultas multi-dominio
  - Detección de consultas fuera de scope (no-legal)
  - Confianza mínima para routing
- [ ] Nodo de Routing
  - Tabla de routing: clasificación → agente correspondiente
  - Routing paralelo para consultas multi-dominio
  - Queue management para agentes ocupados
- [ ] Nodo de Validación
  - Verificación de citas (¿existen las normas citadas?)
  - Coherencia de la respuesta
  - Detección de hallucinations
  - Disclaimer automático
- [ ] Nodo de Integración Multi-dominio
  - Combina respuestas de múltiples agentes
  - Resuelve contradicciones (principio de especialidad)
  - Formatea respuesta unificada
- [ ] State management persistente
  - Conversación state → PostgreSQL
  - Checkpoint recovery

#### Sprint 8: Primeros 3 Agentes Especializados
- [ ] **Agente de Derecho Civil**
  - Knowledge scope: CC, CPC, Familia, Sucesiones, Reales, Obligaciones, Contratos
  - Prompt especializado con terminología civil
  - RAG filtrado a documentos de derecho civil
  - Test cases: 20 consultas civiles con validación
- [ ] **Agente de Derecho Penal**
  - Knowledge scope: CP, NCPP, Código Ejecución Penal
  - Prompt con tipificación penal, penas, procesos
  - RAG filtrado a documentos penales + jurisprudencia penal
  - Test cases: 20 consultas penales
- [ ] **Agente de Derecho Laboral**
  - Knowledge scope: LPCL, DS 003-97-TR, Ley SST, LRCT
  - Prompt con cálculos laborales, derechos del trabajador
  - RAG filtrado a normativa laboral + resoluciones SUNAFIL
  - Test cases: 20 consultas laborales
- [ ] Integración completa: Orquestador → 3 Agentes → RAG → Respuesta
- [ ] Test end-to-end con 20 consultas que cruzan dominios

**Entregable Sprint 8**: Sistema funcional donde un usuario pregunta algo legal y recibe respuesta citada de fuentes peruanas, enrutada al agente correcto. DEMO interna.

---

### FASE 3: EXPANSIÓN DE AGENTES Y FRONTEND (Sprints 9-12) — Semanas 17-24

> **Objetivo**: Todos los agentes operativos + interfaz de usuario completa

#### Sprint 9: Agentes Tributario, Administrativo y Constitucional
- [ ] **Agente Tributario**
  - Código Tributario, LIR, IGV, ISC
  - Normas SUNAT, resoluciones del Tribunal Fiscal
  - Cálculos tributarios básicos (UIT, tramos IR)
- [ ] **Agente Administrativo**
  - LPAG (TUO Ley 27444), silencio administrativo
  - Ley de Contrataciones del Estado
  - Procedimientos ante entidades públicas
- [ ] **Agente Constitucional**
  - Constitución 1993 con modificaciones
  - Código Procesal Constitucional
  - Jurisprudencia TC vinculante
  - Procesos constitucionales (amparo, habeas corpus, etc.)
- [ ] Test set expandido: 50 consultas adicionales cubriendo nuevos agentes

#### Sprint 10: Agentes Corporativo, Registral y Competencia
- [ ] **Agente Corporativo / Societario**
  - LGS, Ley de Mercado de Valores, Ley MYPE
  - Código de Comercio
  - Constitución de empresas, tipos societarios
- [ ] **Agente Registral**
  - Normativa SUNARP, Reglamento General de Registros
  - Procedimientos registrales, observaciones
- [ ] **Agente Competencia / Propiedad Intelectual**
  - Normas INDECOPI
  - Marcas, patentes, derecho de autor
  - Protección al consumidor, publicidad
- [ ] Refinar orquestador con 8+ agentes activos
- [ ] Mejorar routing multi-dominio con feedback loop

#### Sprint 11: Frontend — Chat Interface
- [ ] Interfaz de chat principal
  - Input con sugerencias contextuales
  - Streaming de respuestas (Vercel AI SDK)
  - Markdown rendering para respuestas legales
  - Citation links clickeables → abren fuente
  - Historial de conversaciones (sidebar)
  - Indicador de agente activo ("Respondiendo: Agente Laboral")
- [ ] Selector de modelo de IA
  - Dropdown para elegir: GPT-4o, Claude, Gemini, Local
  - Indicador de costo estimado por consulta
  - Info de capacidades por modelo
- [ ] Panel de área legal
  - Navegador de ramas del derecho (visual)
  - Click en rama → inicia consulta contextualizada
  - Normas más consultadas por área
- [ ] Responsive design (mobile-first para abogados en campo)
- [ ] Dark mode

#### Sprint 12: Frontend — Documentos y Búsqueda
- [ ] Visor de documentos legales
  - Renderizado de normas con estructura jerárquica
  - Resaltado de artículos referenciados en chat
  - Links cruzados entre normas relacionadas
  - Historial de modificaciones de artículos
- [ ] Buscador avanzado de normativa
  - Búsqueda full-text en toda la base normativa
  - Filtros: área, tipo norma, fecha, vigencia
  - Resultados con context preview
  - Exportar resultados
- [ ] Favoritos y colecciones
  - Guardar normas/artículos favoritos
  - Crear colecciones temáticas
  - Compartir colecciones

**Entregable Sprint 12**: Plataforma completa con 8+ agentes, UI funcional, búsqueda y chat operativos. MVP USABLE.

---

### FASE 4: INTELIGENCIA AVANZADA (Sprints 13-16) — Semanas 25-32

> **Objetivo**: Features diferenciadores que van más allá de un chatbot básico

#### Sprint 13: Compliance Agent y Comercio Exterior
- [ ] **Agente de Compliance / Normativo**
  - Protección de Datos Personales (Ley 29733 + DS 016-2024-JUS)
  - Responsabilidad administrativa de PJ (Ley 30424)
  - Prevención de lavado de activos
  - Modelo de prevención (compliance program)
- [ ] **Agente de Comercio Exterior**
  - Ley General de Aduanas
  - TLC vigentes del Perú
  - Normas MINCETUR, SUNAT-Aduanas
  - Regímenes aduaneros
- [ ] 12 agentes especializados operativos
- [ ] Benchmark de calidad por agente

#### Sprint 14: Sistema de Citaciones y Referencias Cruzadas
- [ ] Motor de citaciones inteligente
  - Detección automática de referencias normativas en texto
  - Linking entre normas citadas y texto completo
  - "Art. 1351 CC" → link directo al artículo
- [ ] Mapa de referencias cruzadas
  - Norma A modifica Norma B
  - Norma C deroga Norma D
  - Sentencia TC interpreta Art. X de Norma Y
  - Visualización de grafo de relaciones
- [ ] Timeline de vigencia normativa
  - Ver evolución de un artículo en el tiempo
  - Comparar versiones (diff visual)
  - Alerta de normas próximas a entrar en vigencia
- [ ] "Normas relacionadas" en cada consulta
  - Sugerencias de normativa vinculada
  - Jurisprudencia relevante sobre el tema

#### Sprint 15: Análisis de Casos y Comparador
- [ ] Herramienta de análisis de caso
  - Usuario describe su caso
  - Sistema identifica normas aplicables
  - Sugiere posibles vías legales
  - Señala jurisprudencia relevante
  - Identifica riesgos y consideraciones
- [ ] Comparador de normas
  - Comparar dos versiones de una misma norma
  - Comparar normas de distintas áreas sobre mismo tema
  - Diff visual con highlighting
- [ ] Resúmenes ejecutivos de normas
  - "Explícame la Ley X en lenguaje simple"
  - Generación de resúmenes por sección
  - Puntos clave y obligaciones

#### Sprint 16: Mejora Continua de IA
- [ ] Sistema de feedback del usuario
  - Thumbs up/down en respuestas
  - Reportar respuesta incorrecta
  - Sugerir corrección
- [ ] RAG evaluation pipeline automatizado
  - Test suite de 500+ preguntas con ground truth
  - Automated scoring: precision, recall, groundedness
  - Regression testing ante cambios de prompts/modelos
- [ ] Prompt optimization
  - A/B testing de prompts
  - Per-agent prompt refinement basado en feedback
  - Few-shot examples curados por abogados
- [ ] Guardrails legales
  - Detección de consultas que requieren abogado presencial
  - Prohibición de dar "asesoría legal" directa
  - Disclaimer contextual automático
  - Límites éticos claros

**Entregable Sprint 16**: Plataforma con 12 agentes, análisis de casos, referencias cruzadas, timeline normativo, y feedback loop. ALPHA RELEASE.

---

### FASE 5: ENTERPRISE Y MONETIZACIÓN (Sprints 17-20) — Semanas 33-40

> **Objetivo**: Features enterprise, multi-tenant, analytics, y modelo de negocio

#### Sprint 17: Multi-tenant y Planes
- [ ] Sistema multi-tenant
  - Organizaciones con múltiples usuarios
  - Roles: admin, abogado, consultor, viewer
  - RLS por organización
  - Workspace compartido por organización
- [ ] Sistema de planes y billing
  - Free: 20 consultas/mes, modelo básico
  - Pro: 200 consultas/mes, todos los modelos, historial completo
  - Enterprise: ilimitado, API access, soporte prioritario
  - Integración con Stripe para pagos
  - Gestión de suscripciones
- [ ] Límites y quotas
  - Rate limiting por plan
  - Token counting y cost tracking
  - Alertas de uso

#### Sprint 18: API Pública y Integraciones
- [ ] API REST pública
  - Documentación OpenAPI completa
  - API keys management
  - Endpoints: `/query`, `/search`, `/documents`, `/agents`
  - Rate limiting por API key
  - Webhooks para eventos
- [ ] Integraciones
  - Plugin para Microsoft Word (consulta desde documento)
  - Extensión Chrome (consulta desde cualquier web legal)
  - Widget embeddable para sitios de estudios de abogados
- [ ] SDK básico
  - Python SDK
  - JavaScript/TypeScript SDK

#### Sprint 19: Analytics y Admin Panel
- [ ] Dashboard de analytics
  - Consultas por área del derecho (tendencias)
  - Normativa más consultada
  - Tiempos de respuesta
  - Calidad de respuestas (basada en feedback)
  - Costo por consulta (por modelo)
- [ ] Admin panel
  - Gestión de usuarios y organizaciones
  - Moderación de contenido
  - Upload manual de normativa
  - Configuración de agentes (prompts, knowledge)
- [ ] Reportes
  - Reporte de uso mensual por organización
  - Exportar historial de consultas
  - Reporte de normativa actualizada

#### Sprint 20: Seguridad y Compliance del Producto
- [ ] Auditoría de seguridad
  - Penetration testing
  - OWASP Top 10 checklist
  - Data encryption at rest y in transit
  - Backup automatizado
- [ ] Compliance de datos
  - Cumplimiento Ley 29733 (Protección Datos Personales Perú)
  - Política de privacidad
  - Términos de uso
  - Consentimiento informado
  - Derecho al olvido (eliminación de datos)
- [ ] Logging y auditoría
  - Audit trail de todas las consultas
  - Log de accesos
  - Retención configurable

**Entregable Sprint 20**: Plataforma enterprise-ready con billing, API, analytics. BETA RELEASE.

---

### FASE 6: REFINAMIENTO Y LANZAMIENTO (Sprints 21-24) — Semanas 41-48

> **Objetivo**: Pulir, optimizar, testear con usuarios reales, lanzar

#### Sprint 21: Beta Testing con Usuarios Reales
- [ ] Programa de beta testers
  - 20-50 abogados/estudios seleccionados
  - Onboarding guiado
  - Canal de feedback directo (Slack/Discord)
  - Sesiones de uso observado
- [ ] Iterar basado en feedback
  - Ajustar UX/UI
  - Mejorar calidad de respuestas
  - Agregar normativa faltante
  - Corregir errores de citación
- [ ] Documentación de usuario
  - Guía de inicio rápido
  - Tutoriales por caso de uso
  - FAQ
  - Video walkthroughs

#### Sprint 22: Performance y Optimización
- [ ] Optimización de latencia
  - Caching de consultas frecuentes (Redis)
  - Pre-computation de embeddings para búsquedas populares
  - CDN para assets estáticos
  - Database query optimization
- [ ] Optimización de costos AI
  - Routing inteligente: consultas simples → modelo barato, complejas → modelo potente
  - Cache de respuestas similares
  - Embedding batch processing
  - Análisis de costo por feature
- [ ] Escalabilidad
  - Load testing (k6 o Artillery)
  - Horizontal scaling plan
  - Database read replicas si necesario
  - Queue system (Celery + Redis) para jobs pesados

#### Sprint 23: Contenido y Cobertura Legal
- [ ] Auditoría de cobertura normativa
  - Checklist de normas principales por área
  - Gap analysis: ¿qué falta?
  - Priorizar normativa faltante
- [ ] Actualización de contenido
  - Pipeline de actualización diaria funcionando
  - Alertas de nuevas normas relevantes
  - Newsletter automático de cambios normativos
- [ ] Calidad de contenido
  - Revisión por abogados de respuestas generadas
  - Curación de prompts por especialistas
  - Ground truth dataset expandido a 1000+ Q&A

#### Sprint 24: Go-Live
- [ ] Landing page / marketing site
  - Propuesta de valor clara
  - Planes y precios
  - Demo interactiva
  - Testimonios de beta testers
- [ ] Infraestructura de producción
  - Deploy final (AWS/Railway)
  - Monitoring (Sentry, Datadog o similar)
  - Alerting
  - Runbooks para incidentes
- [ ] Launch checklist
  - [ ] Todos los agentes funcionando
  - [ ] Normativa principal indexada y actualizada
  - [ ] Auth + billing operativos
  - [ ] Performance dentro de SLA
  - [ ] Seguridad auditada
  - [ ] Términos legales aprobados
  - [ ] Soporte al cliente listo
  - [ ] Backup y recovery probados
- [ ] 🚀 **LANZAMIENTO PÚBLICO**

**Entregable Sprint 24**: Plataforma en producción, usuarios pagando, pipeline de actualización diaria, soporte activo. GO LIVE.

---

## 6. MÉTRICAS DE ÉXITO

### 6.1 Métricas Técnicas

| Métrica | Target MVP | Target v1.0 |
|---------|-----------|-------------|
| Latencia de respuesta (p95) | < 8 segundos | < 5 segundos |
| Groundedness (respuestas basadas en fuentes) | > 85% | > 95% |
| Citation accuracy (citas correctas) | > 80% | > 92% |
| Routing accuracy (agente correcto) | > 85% | > 95% |
| Uptime | 99% | 99.9% |
| Cobertura normativa (vs total estimado) | 40% | 75% |

### 6.2 Métricas de Producto

| Métrica | Target 3 meses | Target 12 meses |
|---------|---------------|-----------------|
| Usuarios registrados | 500 | 5,000 |
| Usuarios activos mensuales | 150 | 2,000 |
| Consultas diarias | 200 | 5,000 |
| NPS (Net Promoter Score) | > 30 | > 50 |
| Retención mensual | > 40% | > 65% |
| Conversión free → paid | > 5% | > 12% |

---

## 7. RIESGOS Y MITIGACIONES

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| **Hallucinations** — IA inventa normas inexistentes | Alta | Crítico | Guardrails estrictos, citation verification, groundedness checks, disclaimer prominente |
| **Acceso a datos** — SPIJ requiere suscripción | Media | Alto | Iniciar con fuentes libres, negociar acceso institucional, fallback a scraping de El Peruano |
| **Calidad de OCR** — normas antiguas escaneadas | Media | Medio | Inversión en pre-procesamiento, revisión manual de normas clave |
| **Cambios normativos frecuentes** — Perú publica muchas normas | Alta | Alto | Pipeline automatizado diario, alertas de nuevas normas, proceso de actualización rápida |
| **Responsabilidad legal** — usuario toma decisiones basado en la plataforma | Media | Crítico | Disclaimer claro "no es asesoría legal", T&C robustos, seguro de responsabilidad |
| **Costos de IA** — tokens se acumulan rápido | Alta | Alto | Routing inteligente (modelo barato para simple, caro para complejo), caching agresivo, modelos locales para tier free |
| **Competencia** — vLex, LP, Gaceta pueden lanzar AI | Media | Medio | Diferenciación por profundidad de agentes especializados y UX superior |
| **Regulación AI** — nueva regulación de IA en Perú | Baja | Medio | Monitorear proyectos de ley, diseño compliance-first |

---

## 8. EQUIPO SUGERIDO

### 8.1 Equipo Mínimo Viable (MVP)

| Rol | Cantidad | Responsabilidad |
|-----|----------|----------------|
| **Tech Lead / Fullstack** | 1 | Arquitectura, backend, integración AI |
| **Frontend Developer** | 1 | Next.js, UI/UX, chat interface |
| **AI/ML Engineer** | 1 | RAG pipeline, agentes, LangGraph, embeddings |
| **Data Engineer** | 1 | Scrapers, pipeline de datos, procesamiento legal |
| **Asesor Legal** (part-time) | 1 | Validación de contenido, ground truth, prompts |

### 8.2 Equipo Completo (Post-MVP)

Se agregan:
- DevOps / SRE (1)
- QA Engineer (1)
- Product Manager (1)
- Designer UI/UX (1)
- Abogado(s) especialista(s) adicionales (2-3)
- Customer Success (1)

---

## 9. PRESUPUESTO ESTIMADO (Mensual)

### 9.1 Infraestructura

| Servicio | Costo MVP/mes | Costo Producción/mes |
|----------|--------------|---------------------|
| Supabase (Pro) | $25 | $75 |
| Railway/Render (API) | $20 | $100 |
| Vercel (Frontend) | $0-20 | $20 |
| Redis (Upstash) | $0-10 | $25 |
| OpenAI API | $100-300 | $500-2,000 |
| Anthropic API | $50-150 | $200-1,000 |
| Storage (PDFs) | $5 | $20 |
| Monitoring (Sentry) | $0 | $26 |
| **TOTAL INFRA** | **~$250-550/mes** | **~$1,000-3,300/mes** |

### 9.2 Servicios Externos

| Servicio | Costo |
|----------|-------|
| SPIJ suscripción | ~$200-500/año |
| Dominio + SSL | ~$50/año |
| Stripe (processing) | 2.9% + $0.30/transacción |

---

## 10. TIMELINE VISUAL

```
MES  1-2  │ FASE 0: Fundación          │ ████░░░░░░░░░░░░░░░░░░░░
MES  2-4  │ FASE 1: Data Pipeline       │ ░░░░████████░░░░░░░░░░░░
MES  5-7  │ FASE 2: Core AI             │ ░░░░░░░░░░░░████████░░░░
MES  7-10 │ FASE 3: Agentes + Frontend  │ ░░░░░░░░░░░░░░░░████████
MES 10-12 │ FASE 4: Inteligencia Avanz. │ ░░░░░░░░░░░░░░░░░░░░████
─────────────────────────────────────────
MES  1    │ Sprint 1-2                  │ Scaffolding, Auth
MES  2    │ Sprint 3                    │ Scrapers, Normativa  
MES  3    │ Sprint 4-5                  │ Vectorización, Jurisprudencia
MES  4    │ Sprint 6                    │ LLM Layer, RAG Pipeline
MES  5    │ Sprint 7                    │ Orquestador LangGraph
MES  6    │ Sprint 8                    │ 3 Agentes + Demo ⭐ MVP INTERNO
MES  7    │ Sprint 9-10                 │ 8+ Agentes
MES  8    │ Sprint 11-12                │ Frontend completo ⭐ MVP USABLE
MES  9    │ Sprint 13-14                │ 12 Agentes + Citaciones
MES 10    │ Sprint 15-16                │ Análisis de casos ⭐ ALPHA
MES 11    │ Sprint 17-20                │ Enterprise + API ⭐ BETA
MES 12    │ Sprint 21-24                │ Polish + Launch 🚀 GO LIVE
```

---

## 11. PRÓXIMOS PASOS INMEDIATOS

1. **Validar stack tecnológico** — ¿FastAPI + Next.js + LangGraph es aceptable o hay preferencia por otro stack?
2. **Definir MVP scope** — ¿Arrancar con 3 agentes (Civil, Penal, Laboral) está bien?
3. **Acceso a fuentes** — Investigar viabilidad de scraping de SPIJ y otras fuentes
4. **Team building** — ¿Quién desarrolla? ¿Solo? ¿Equipo? Esto define velocidad
5. **Budget** — Definir presupuesto mensual para infraestructura AI
6. **Arrancar Sprint 1** — Scaffolding del proyecto

---

> **Nota**: Este plan es una guía viva. Se ajusta sprint a sprint según descubrimientos, feedback y realidades del proyecto. La belleza de hacerlo en sprints es que cada 2 semanas tenés un punto de decisión para pivotar, ajustar o acelerar.

---

*Documento generado como parte del proceso de planificación de Agente Derecho.*
*Última actualización: 2 de Abril, 2026*
