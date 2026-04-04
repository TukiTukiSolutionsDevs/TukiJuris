/**
 * Auth utilities — token management and API calls.
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const TOKEN_KEY = "agente_derecho_token";
const USER_KEY = "agente_derecho_user";

export interface AuthUser {
  id: string;
  email: string;
  full_name: string | null;
  plan: string;
}

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function getUser(): AuthUser | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem(USER_KEY);
  return raw ? JSON.parse(raw) : null;
}

export function setUser(user: AuthUser): void {
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function logout(): void {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
  window.location.href = "/auth/login";
}

export function authHeaders(): Record<string, string> {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export async function login(
  email: string,
  password: string
): Promise<{ token: string }> {
  const res = await fetch(`${API_URL}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Error de conexion" }));
    throw new Error(err.detail || "Credenciales invalidas");
  }
  const data = await res.json();
  setToken(data.access_token);
  return { token: data.access_token };
}

export async function register(
  email: string,
  password: string,
  full_name?: string
): Promise<{ token: string }> {
  const res = await fetch(`${API_URL}/api/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password, full_name }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Error de conexion" }));
    throw new Error(err.detail || "Error al registrar");
  }
  const data = await res.json();
  setToken(data.access_token);
  return { token: data.access_token };
}
