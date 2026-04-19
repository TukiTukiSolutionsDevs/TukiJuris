/**
 * JWT payload decoder — client-side only (NO signature verification).
 * Signature verification is the backend's responsibility.
 * This module only parses the payload to read claims like sub, is_admin, exp.
 */

export interface AccessClaims {
  /** User UUID — maps to User.id on the backend */
  sub: string;
  email?: string;
  is_admin?: boolean;
  type: "access";
  exp: number;
  iat: number;
}

/**
 * Decode the payload of a JWT access token without verifying the signature.
 * Returns null if the token is malformed or cannot be parsed.
 */
export function decodeAccessClaims(token: string): AccessClaims | null {
  try {
    const parts = token.split(".");
    if (parts.length !== 3) return null;

    const payload = parts[1];
    // Base64url → Base64 → JSON
    const b64 = payload.replace(/-/g, "+").replace(/_/g, "/");
    const pad = b64.length % 4 === 0 ? "" : "=".repeat(4 - (b64.length % 4));
    const json = atob(b64 + pad);
    return JSON.parse(json) as AccessClaims;
  } catch {
    return null;
  }
}

/**
 * Returns true if the decoded claims are expired (with no clock-skew tolerance).
 * Use this only for optimistic UI decisions — the backend is authoritative.
 */
export function isTokenExpired(claims: AccessClaims): boolean {
  return Date.now() / 1000 > claims.exp;
}
