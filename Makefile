# Agente Derecho — Development Commands
.PHONY: up down restart logs api web db seed test test-cov build lint lint-fix format format-check ci \
        prod-up prod-down prod-logs prod-build prod-migrate prod-status \
        deploy backup restore monitor setup-server setup-cron \
        migrate migrate-new migrate-history migrate-downgrade migrate-current

# === Quick Start ===
up:                     ## Start all services
	docker compose up -d

down:                   ## Stop all services
	docker compose down

restart:                ## Restart API (picks up code changes)
	docker compose up api -d --force-recreate --no-build

logs:                   ## Show API logs
	docker compose logs api -f --tail 50

# === Individual Services ===
api:                    ## Start API only
	docker compose up api -d --force-recreate --no-build

web:                    ## Start frontend only
	docker compose up web -d --force-recreate --no-build

db:                     ## Start database + redis only
	docker compose up db redis -d

# === Build ===
build:                  ## Build all Docker images
	docker compose build

build-api:              ## Build API image
	docker compose build api

build-web:              ## Build frontend image
	docker compose build web

# === Migrations ===
migrate:                ## Run pending migrations
	cd apps/api && alembic upgrade head

migrate-new:            ## Create new migration (usage: make migrate-new MSG="add feature X")
	cd apps/api && alembic revision --autogenerate -m "$(MSG)"

migrate-history:        ## Show migration history
	cd apps/api && alembic history --verbose

migrate-downgrade:      ## Rollback last migration
	cd apps/api && alembic downgrade -1

migrate-current:        ## Show current migration version
	cd apps/api && alembic current

# === Database ===
db-shell:               ## Open psql shell
	docker exec -it agente-derecho-db-1 psql -U postgres -d agente_derecho

db-stats:               ## Show knowledge base stats
	@curl -s http://localhost:8000/api/health/knowledge | python3 -m json.tool

db-backup:              ## Backup full DB to backups/ (schema + data + embeddings, ~1.6MB)
	@mkdir -p backups
	@echo "Dumping database..."
	@docker exec agente-derecho-db-1 pg_dump -U postgres --format=custom --compress=9 agente_derecho > backups/tukijuris_$(shell date +%Y%m%d_%H%M%S).dump
	@echo "✅ Backup saved to backups/"
	@ls -lh backups/*.dump | tail -1

db-restore:             ## Restore DB from backup (usage: make db-restore FILE=backups/tukijuris_xxx.dump)
	@test -n "$(FILE)" || (echo "❌ Usage: make db-restore FILE=backups/tukijuris_xxx.dump" && exit 1)
	@test -f "$(FILE)" || (echo "❌ File not found: $(FILE)" && exit 1)
	@echo "⚠️  Restoring $(FILE) — this REPLACES all data..."
	@docker exec agente-derecho-db-1 psql -U postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='agente_derecho' AND pid <> pg_backend_pid();" > /dev/null 2>&1 || true
	@docker exec agente-derecho-db-1 dropdb -U postgres --if-exists agente_derecho
	@docker exec agente-derecho-db-1 createdb -U postgres agente_derecho
	@cat $(FILE) | docker exec -i agente-derecho-db-1 pg_restore -U postgres -d agente_derecho --no-owner --no-privileges
	@echo "✅ Restored. Restarting API to reconnect..."
	@docker compose restart api > /dev/null 2>&1
	@sleep 3
	@curl -s http://localhost:8000/api/health/knowledge | python3 -m json.tool

db-seed-full:           ## Full pipeline: ingest + embeddings + scrapers (populates empty DB)
	@echo "=== Step 1/3: Ingesting seeder documents ==="
	@docker exec agente-derecho-api-1 python -m services.ingestion.ingest
	@echo ""
	@echo "=== Step 2/3: Generating embeddings (this takes ~4 min) ==="
	@docker exec agente-derecho-api-1 python -m services.ingestion.generate_embeddings
	@echo ""
	@echo "=== Step 3/3: Running scrapers (El Peruano, TC, INDECOPI) ==="
	@docker exec agente-derecho-api-1 python -m services.ingestion.scrapers.scheduler
	@echo ""
	@echo "=== Generating embeddings for scraped data ==="
	@docker exec agente-derecho-api-1 python -m services.ingestion.generate_embeddings
	@echo ""
	@echo "✅ Full seed complete. Knowledge base status:"
	@curl -s http://localhost:8000/api/health/knowledge | python3 -m json.tool

# === Development ===
seed:                   ## Run all data seeders
	@echo "Seeding legal documents..."
	@for f in services/ingestion/seeders/*.py; do \
		docker cp "$$f" agente-derecho-api-1:/tmp/$$(basename $$f); \
	done
	@echo "Files copied. Run ingestion manually or use API."

health:                 ## Check system health
	@echo "=== API ===" && curl -s http://localhost:8000/api/health | python3 -m json.tool
	@echo "=== DB + pgvector ===" && curl -s http://localhost:8000/api/health/ready | python3 -m json.tool
	@echo "=== Knowledge Base ===" && curl -s http://localhost:8000/api/health/knowledge | python3 -m json.tool

status:                 ## Show all container status
	docker compose ps

# === Frontend ===
fe-dev:                 ## Run frontend in dev mode (local, no docker)
	cd apps/web && npm run dev

fe-build:               ## Build frontend
	cd apps/web && npm run build

# === Testing ===
test:                   ## Run test suite (requires DB + Redis running)
	docker exec tukijuris-api-1 pytest tests/ -v --tb=short

test-cov:               ## Run test suite with coverage report
	docker exec tukijuris-api-1 pytest tests/ \
	    --cov=app \
	    --cov-report=term-missing \
	    --cov-report=json:/tmp/coverage.json

query:                  ## Test a legal query (usage: make query Q="tu pregunta")
	@curl -s -X POST http://localhost:8000/api/chat/query \
		-H "Content-Type: application/json" \
		-d '{"message": "$(Q)"}' | python3 -m json.tool

search:                 ## Search normativa (usage: make search Q="despido")
	@curl -s "http://localhost:8000/api/documents/search?q=$(Q)&limit=5" | python3 -m json.tool

# === Load Testing ===
loadtest:               ## Run load test (50 users, 2 min, headless)
	locust -f tests/load/locustfile.py --host=http://localhost:8000 --headless -u 50 -r 5 --run-time 2m --html=tests/load/report.html

loadtest-ui:            ## Run load test with web UI (open http://localhost:8089)
	locust -f tests/load/locustfile.py --host=http://localhost:8000

# === Scrapers ===
scrape:                 ## Run all scrapers once
	python -m services.ingestion.scrapers.scheduler

scrape-daemon:          ## Run scraper scheduler as daemon (periodic)
	python -m services.ingestion.scrapers.scheduler --daemon

scrape-peruano:         ## Scrape El Peruano only
	python -m services.ingestion.scrapers.el_peruano

scrape-tc:              ## Scrape TC enhanced only
	python -m services.ingestion.scrapers.tc_enhanced

scrape-indecopi:        ## Scrape INDECOPI only
	python -m services.ingestion.scrapers.indecopi_scraper

# === Production ===
.PHONY: prod-up prod-down prod-logs prod-build prod-migrate

prod-up:                ## Start production stack
	docker compose -f docker-compose.prod.yml up -d

prod-down:              ## Stop production stack
	docker compose -f docker-compose.prod.yml down

prod-logs:              ## Show production logs (last 100 lines, follow)
	docker compose -f docker-compose.prod.yml logs -f --tail 100

prod-build:             ## Build production images
	docker compose -f docker-compose.prod.yml build

prod-migrate:           ## Run Alembic migrations in production
	docker compose -f docker-compose.prod.yml exec api alembic upgrade head

prod-status:            ## Show production container status
	docker compose -f docker-compose.prod.yml ps

# === CI ===
lint:                   ## Run linter (ruff)
	ruff check apps/api/

lint-fix:               ## Auto-fix lint issues
	ruff check --fix apps/api/

format:                 ## Format code (ruff)
	ruff format apps/api/

format-check:           ## Check formatting
	ruff format --check apps/api/

ci:                     ## Run full CI locally (lint + test + build)
	@echo "=== Lint ===" && ruff check apps/api/
	@echo "=== Tests ===" && cd apps/api && python -m pytest tests/ -v --tb=short
	@echo "=== Frontend Build ===" && cd apps/web && npm run build
	@echo "=== CI passed ==="

# === Operations ===
deploy:                 ## Deploy latest changes to production
	bash infrastructure/scripts/deploy.sh

backup:                 ## Run database backup
	bash infrastructure/scripts/backup.sh

restore:                ## Restore database (usage: make restore FILE=path/to/backup)
	bash infrastructure/scripts/restore.sh $(FILE)

monitor:                ## Quick system health check
	bash infrastructure/scripts/monitor.sh

setup-server:           ## Initial VPS setup (run once, as root)
	sudo bash infrastructure/scripts/setup-server.sh

setup-cron:             ## Setup cron jobs for backup + cert renewal
	@echo "Adding cron jobs..."
	(crontab -l 2>/dev/null; echo "0 2 * * * /opt/tukijuris/app/infrastructure/scripts/backup.sh") | crontab -
	(crontab -l 2>/dev/null; echo "0 3 * * * /opt/tukijuris/app/infrastructure/certbot/renew-certs.sh") | crontab -
	@echo "Cron jobs added. Verify with: crontab -l"

# === Help ===
help:                   ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'
