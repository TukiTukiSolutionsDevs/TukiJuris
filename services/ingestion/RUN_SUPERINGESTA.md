# Super-ingesta — Run Order (2026-06-24)

Pasos para ejecutar la super-ingesta y volver a tener búsqueda híbrida con embeddings y áreas expandidas.

## 0. Pre-requisitos

- Docker Desktop corriendo (containers `tukijuris-*` healthy).
- Acceso a la BD `agente_derecho`.
- Dependencia Python `sentence-transformers` instalada en el container API (para embeddings locales). Si no está:
  ```bash
  docker exec tukijuris-api-1 pip install sentence-transformers
  ```
  Esto descarga el modelo `intfloat/multilingual-e5-large` (~2.2 GB) la primera vez que se usa. Cacheable.

## 1. Ingerir nuevas áreas (seeders estáticos)

Ya están registrados en `services/ingestion/ingest.py`. Idempotente: no duplica si el `document_number` ya existe.

```bash
docker exec tukijuris-api-1 python -m services.ingestion.ingest
```

Esto añadirá 4 nuevos documentos (Ley 29571, Ley 29733, Ambiental base, Ley 32069) con sus chunks. Resumen esperado:
- `consumidor`: ~17 chunks
- `datos_personales`: ~15 chunks
- `ambiental`: ~16 chunks
- `contrataciones_estado`: ~14 chunks

## 2. Ingerir normativa viva desde gob.pe (opcional pero recomendado)

El nuevo `gob_pe_scraper.py` recorre ~17 instituciones del Estado (SUNAT, ANPD, SBS, OSCE, MINAM, OEFA, OSINERGMIN, OSIPTEL, MTC, MINSA, SUNAFIL, SUNARP, SERVIR, INDECOPI, etc.) y guarda el listado de normas recientes con su URL oficial. Es un primer pase de "metadata + sumario", no texto consolidado.

```bash
docker exec tukijuris-api-1 python -m services.ingestion.scrapers.gob_pe_scraper
```

Tiempo aprox.: 3-6 minutos. Conservador con `max_sheets=3..5` por entidad — ajustar en el catálogo si se quiere más cobertura histórica.

## 3. Generar embeddings localmente con multilingual-e5-large

Sustituye al script viejo basado en Google/OpenAI. Local, gratis, 1024-dim — coincide con la columna `vector(1024)` ya migrada.

```bash
docker exec tukijuris-api-1 python -m services.ingestion.generate_embeddings_local
```

El script:
1. Verifica que la columna sea `vector(1024)`. Si no, la migra y dropea el índice HNSW.
2. Carga `intfloat/multilingual-e5-large` (cachea modelo).
3. Embebe en lotes de 32, prefijando "passage: " (convención e5).
4. Persiste con `normalize_embeddings=True` (cosine-friendly).
5. Re-crea el índice HNSW (`m=16`, `ef_construction=200`).
6. Aplica patch al `hybrid_search()` SQL para usar `vector(1024)`.

Tiempo aprox.: depende del tamaño del corpus. CPU local: ~1-2 chunks/s. GPU (mps en Mac M-series, cuda en Linux): 10-50 chunks/s. Para corpus de ~500 chunks: 5-10 minutos CPU.

Variable de entorno opcional:
```bash
EMBED_DEVICE=mps    # Mac M-series
EMBED_DEVICE=cuda   # GPU NVIDIA
EMBED_BATCH_SIZE=64 # default 32
```

## 4. Verificar

```bash
docker exec tukijuris-api-1 python -c "
import asyncio, asyncpg, os
async def main():
    c = await asyncpg.connect(os.getenv('DATABASE_URL', '').replace('postgresql+asyncpg://', 'postgresql://'))
    print('docs        :', await c.fetchval('SELECT COUNT(*) FROM documents'))
    print('chunks      :', await c.fetchval('SELECT COUNT(*) FROM document_chunks'))
    print('w/ embed    :', await c.fetchval('SELECT COUNT(*) FROM document_chunks WHERE embedding IS NOT NULL'))
    print('areas       :')
    for r in await c.fetch('SELECT legal_area, COUNT(*) c FROM document_chunks GROUP BY 1 ORDER BY c DESC'):
        print(f'  {r[\"legal_area\"]:30} {r[\"c\"]:>5}')
asyncio.run(main())
"
```

Smoke test del retriever desde el chat:
- "¿Cuáles son los derechos del consumidor según el Código de Consumo?" → debe citar Ley 29571 art. 1
- "¿Qué es un dato sensible bajo la Ley 29733?" → debe citar art. 2 LPDP
- "¿Qué tipos de procedimiento de selección reconoce la nueva LCE Ley 32069?" → debe citar Ley 32069

## 5. (Opcional) Comparación con embedding viejo

Si se quiere comparar precisión vs el embedding anterior (Google 768-dim), se puede mantener una copia paralela:
```sql
ALTER TABLE document_chunks ADD COLUMN embedding_old vector(768);
-- copiar de un snapshot anterior
```
y construir un script de evaluación con preguntas-respuestas etiquetadas.

## Áreas hardcoded actualizadas

Sincronizadas en:
- `apps/api/app/core/validators.py` (frozenset `_VALID_LEGAL_AREAS`)
- `apps/api/app/agents/orchestrator.py` (`LEGAL_AREAS`, `KEYWORD_MAP`, classification prompt)
- `apps/web/src/app/chat/constants.ts` (`LEGAL_AREAS`)
- `apps/web/src/app/chat/components/AreaChip.tsx` (`AREA_LABELS`)
- `apps/web/src/app/docs/_data/legal-areas.ts` (`LEGAL_AREAS`)

Quedan duplicadas y NO actualizadas (low priority, fallback funciona con `area-id` literal):
- `apps/web/src/app/historial/page.tsx` (AREA_LABELS local)
- `apps/web/src/app/compartido/[id]/page.tsx` (AREA_LABELS local)
- `apps/web/src/app/buscar/page.tsx`
- `apps/web/src/app/guia/page.tsx`
- `apps/web/src/app/configuracion/page.tsx`

Refactor recomendado en próxima sesión: deduplicar a una única exportación canónica desde `chat/constants.ts`.

## Archivos creados / modificados esta sesión

### Nuevos
- `services/ingestion/scrapers/gob_pe_scraper.py` — scraper genérico gob.pe (cubre ~17 instituciones).
- `services/ingestion/generate_embeddings_local.py` — embeddings sentence-transformers, multilingual-e5-large 1024-dim.
- `services/ingestion/seeders/consumidor.py` — ~17 chunks Ley 29571.
- `services/ingestion/seeders/datos_personales.py` — ~15 chunks Ley 29733 + DS 003-2013-JUS.
- `services/ingestion/seeders/ambiental.py` — ~16 chunks Ley 28611 / SEIA / LRH / LFFS / SINEFA / GIRS / ANP / consulta previa.
- `services/ingestion/seeders/contrataciones_estado.py` — ~14 chunks Ley 32069 (LGCP vigente 22-abr-2025).
- `services/ingestion/RESEARCH_SOURCES.md` — investigación de fuentes oficiales peruanas (subagente).
- `services/ingestion/SEED_CORPUS.md` — build list ~160 documentos verificados.
- `services/ingestion/RUN_SUPERINGESTA.md` — este archivo.

### Modificados
- `apps/api/app/core/validators.py` — `_VALID_LEGAL_AREAS` de 11 → 29 áreas.
- `apps/api/app/agents/orchestrator.py` — `LEGAL_AREAS` (11→29), `KEYWORD_MAP` (+18 áreas), classification prompt.
- `apps/web/src/app/chat/constants.ts` — `LEGAL_AREAS` (11→29).
- `apps/web/src/app/chat/components/AreaChip.tsx` — `AREA_LABELS` (11→29).
- `apps/web/src/app/docs/_data/legal-areas.ts` — `LEGAL_AREAS` (11→29) con iconos lucide-react actualizados.
- `services/ingestion/ingest.py` — import + registro de 4 nuevos documentos.

## Pendiente para próximas sesiones

- Scrapers especializados: El Peruano PDF + OCR; DSpace OEFA REST; OSIPTEL buscador GET; SUNARP SIP; Playwright para TC sedetc / INDECOPI semántico; SBS WebForms; WCM Poder Judicial.
- Seeders adicionales (el resto del corpus): familia, comercial, propiedad_intelectual, mercado_valores, seguros, minero, hidrocarburos, telecom, transporte, salud, financiero, seguridad_social, notarial, procesal extendido.
- `domain_agents.py`: añadir agentes especializados nuevos en `AGENT_REGISTRY` (actualmente las 18 áreas nuevas caen al fallback "civil" del orchestrator si no clasifican bien).
- Deduplicar `LEGAL_AREAS` / `AREA_LABELS` en frontend.
- Evaluar convenio MINJUS para acceder a SPIJ con textos consolidados.
