export const PYTHON_EXAMPLE = `import httpx

API_KEY = "ak_your_key_here"
BASE_URL = "https://api.tukijuris.net.pe"

# Make a legal query
response = httpx.post(
    f"{BASE_URL}/api/v1/query",
    headers={"X-API-Key": API_KEY},
    json={"query": "Requisitos para un despido justificado en Peru"},
)
data = response.json()
print(data["answer"])

# Citations from the legal corpus
for citation in data["citations"]:
    print(f"[{citation['document']}] {citation['content'][:100]}...")`;

export const JS_EXAMPLE = `const API_KEY = "ak_your_key_here";
const BASE_URL = "https://api.tukijuris.net.pe";

// Make a legal query
const response = await fetch(\`\${BASE_URL}/api/v1/query\`, {
  method: "POST",
  headers: {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    query: "Requisitos para un despido justificado en Peru",
  }),
});

const data = await response.json();
console.log(data.answer);

// Citations from the legal corpus
data.citations.forEach((c) => {
  console.log(\`[\${c.document}]\`, c.content.slice(0, 100));
});`;

export const CURL_EXAMPLE = `# Register and get a JWT token
curl -X POST https://api.tukijuris.net.pe/api/auth/login \\
  -H "Content-Type: application/json" \\
  -d '{"email": "you@lawfirm.com", "password": "your-password"}'

# Use the JWT token to make a legal query
curl -X POST https://api.tukijuris.net.pe/api/v1/query \\
  -H "Authorization: Bearer eyJ..." \\
  -H "Content-Type: application/json" \\
  -d '{"query": "Plazos de prescripcion en derecho penal peruano"}'

# Or use an API key directly
curl -X POST https://api.tukijuris.net.pe/api/v1/query \\
  -H "X-API-Key: ak_your_key_here" \\
  -H "Content-Type: application/json" \\
  -d '{"query": "Como se calcula la CTS en Peru"}'`;

export const SEARCH_EXAMPLE = `import httpx

API_KEY = "ak_your_key_here"
BASE_URL = "https://api.tukijuris.net.pe"

# Search the legal knowledge base directly
response = httpx.post(
    f"{BASE_URL}/api/v1/search",
    headers={"X-API-Key": API_KEY},
    json={
        "query": "despido arbitrario indemnizacion",
        "area": "laboral",
        "limit": 5,
    },
)
results = response.json()["results"]
for r in results:
    print(f"[score={r['score']:.3f}] [{r['document']}] {r['content'][:120]}...")`;

export const ANALYZE_EXAMPLE = `import httpx

API_KEY = "ak_your_key_here"
BASE_URL = "https://api.tukijuris.net.pe"

case = """
Un trabajador fue despedido verbalmente despues de 3 años en la empresa.
No recibio carta de despido ni pago de beneficios sociales.
Desea saber que acciones legales puede tomar.
"""

response = httpx.post(
    f"{BASE_URL}/api/v1/analyze",
    headers={"X-API-Key": API_KEY},
    json={"case_description": case},
)
result = response.json()
print("Areas detectadas:", result["areas_detected"])
print("\\nAnalisis:")
print(result["analysis"])`;
