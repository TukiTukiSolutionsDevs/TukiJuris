"""
Load testing suite for TukiJuris (Agente Derecho).

Usage:
    # Install: pip install locust
    # Run against local:  locust -f tests/load/locustfile.py --host=http://localhost:8000
    # Run against prod:   locust -f tests/load/locustfile.py --host=https://tukijuris.net.pe
    # Headless mode:      locust -f tests/load/locustfile.py --host=http://localhost:8000 --headless -u 50 -r 5 --run-time 2m
"""
from locust import HttpUser, task, between, events
import random

# ---------------------------------------------------------------------------
# Test data
# ---------------------------------------------------------------------------

LEGAL_QUERIES = [
    "Cuales son los requisitos para un despido justificado en Peru?",
    "Como se calcula la CTS?",
    "Que dice el Art. 1351 del Codigo Civil sobre contratos?",
    "Plazos de prescripcion en derecho penal peruano",
    "Requisitos para constituir una SAC en Peru",
    "Que establece la Ley 29783 sobre seguridad en el trabajo?",
    "Principios del procedimiento administrativo segun la LPAG",
    "Que es el silencio administrativo positivo?",
    "Regimen tributario MYPE en Peru",
    "Derechos del consumidor segun INDECOPI",
    "Requisitos para inscripcion en SUNARP",
    "Que es el habeas data?",
    "Obligaciones del oficial de cumplimiento en lavado de activos",
    "Requisitos de importacion definitiva en aduanas",
    "Como funciona la negociacion colectiva de trabajo?",
]

SEARCH_QUERIES = [
    "despido arbitrario",
    "contrato de trabajo",
    "constitucion articulo 2",
    "impuesto a la renta",
    "proteccion al consumidor",
    "codigo penal",
    "procedimiento administrativo",
    "sociedad anonima",
    "habeas corpus",
    "datos personales",
    "regalias mineras",
    "teletrabajo",
]

LEGAL_AREAS = [
    "civil",
    "penal",
    "laboral",
    "tributario",
    "administrativo",
    "corporativo",
    "constitucional",
    "registral",
    "competencia",
    "compliance",
    "comercio_exterior",
]

# Pool of None values so ~30% of queries use auto-detect area
_AREA_POOL = LEGAL_AREAS + [None, None, None, None, None]


# ---------------------------------------------------------------------------
# User classes
# ---------------------------------------------------------------------------

class AnonymousUser(HttpUser):
    """Anonymous user — no auth, limited access. Represents ~30% of traffic."""

    weight = 3
    wait_time = between(2, 5)

    @task(5)
    def health_check(self):
        self.client.get("/api/health")

    @task(3)
    def health_ready(self):
        self.client.get("/api/health/ready")

    @task(2)
    def health_knowledge(self):
        self.client.get("/api/health/knowledge")

    @task(1)
    def root(self):
        self.client.get("/")


class AuthenticatedUser(HttpUser):
    """Authenticated user — registers then exercises all main flows. ~70% of traffic."""

    weight = 7
    wait_time = between(1, 3)

    token = None
    user_email = None

    def on_start(self):
        """Register a unique test user; fall back to login if the email already exists."""
        self.user_email = f"loadtest-{random.randint(10000, 99999)}@test.com"

        res = self.client.post(
            "/api/auth/register",
            json={
                "email": self.user_email,
                "password": "LoadTest123!",
                "full_name": "Load Test User",
            },
        )

        if res.status_code in (200, 201):
            self.token = res.json().get("access_token")

        elif res.status_code == 409:
            # Email collision — log in instead
            res = self.client.post(
                "/api/auth/login",
                json={
                    "email": self.user_email,
                    "password": "LoadTest123!",
                },
            )
            if res.status_code == 200:
                self.token = res.json().get("access_token")

    @property
    def auth_headers(self):
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        return {}

    @task(10)
    def legal_query(self):
        """Main product flow — legal query via chat endpoint."""
        query = random.choice(LEGAL_QUERIES)
        area = random.choice(_AREA_POOL)
        self.client.post(
            "/api/chat/query",
            json={"message": query, "legal_area": area},
            headers=self.auth_headers,
            name="/api/chat/query",
        )

    @task(5)
    def search_documents(self):
        """Search the knowledge base."""
        q = random.choice(SEARCH_QUERIES)
        self.client.get(
            f"/api/documents/search?q={q}&limit=5",
            headers=self.auth_headers,
            name="/api/documents/search",
        )

    @task(3)
    def list_areas(self):
        """Browse available legal areas."""
        self.client.get("/api/v1/areas", headers=self.auth_headers)

    @task(2)
    def v1_query(self):
        """Public v1 API — natural language query."""
        query = random.choice(LEGAL_QUERIES)
        self.client.post(
            "/api/v1/query",
            json={"query": query},
            headers=self.auth_headers,
            name="/api/v1/query",
        )

    @task(2)
    def v1_search(self):
        """Public v1 API — document search."""
        q = random.choice(SEARCH_QUERIES)
        self.client.post(
            "/api/v1/search",
            json={"query": q, "limit": 5},
            headers=self.auth_headers,
            name="/api/v1/search",
        )

    @task(1)
    def feedback_stats(self):
        self.client.get("/api/feedback/stats", headers=self.auth_headers)

    @task(1)
    def billing_plans(self):
        self.client.get("/api/billing/plans", headers=self.auth_headers)


# ---------------------------------------------------------------------------
# Event hooks
# ---------------------------------------------------------------------------

SLOW_REQUEST_THRESHOLD_MS = 5000


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """Log requests that exceed the slow-request threshold."""
    if response_time > SLOW_REQUEST_THRESHOLD_MS:
        print(
            f"[SLOW] {request_type} {name}: {response_time:.0f}ms"
            + (f" — exception: {exception}" if exception else "")
        )
