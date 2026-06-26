/**
 * Trial API client tests.
 *
 * Locks the wire contract for `addCardToTrial` so the next regression
 * (wrong URL, missing field, etc.) fails here instead of at runtime in
 * production. Backend contract lives in apps/api/app/api/routes/trials.py
 * and apps/api/app/schemas/trials.py.
 */

import { describe, expect, it } from "vitest";
import { http, HttpResponse } from "msw";
import { server } from "@/test/msw/server";
import { addCardToTrial, type AddCardBody } from "../trial";

const authFetch = (input: string, init?: RequestInit) => fetch(input, init);

const TRIAL_RESPONSE = {
  id: "11111111-1111-1111-1111-111111111111",
  user_id: "22222222-2222-2222-2222-222222222222",
  plan_code: "pro",
  status: "active",
  started_at: "2026-06-01T00:00:00Z",
  ends_at: "2026-06-15T00:00:00Z",
  days_remaining: 14,
  card_added_at: "2026-06-02T00:00:00Z",
  provider: "culqi",
  charged_at: null,
  charge_failed_at: null,
  charge_failure_reason: null,
  retry_count: 0,
  canceled_at: null,
  canceled_by_user: false,
  downgraded_at: null,
  subscription_id: null,
};

const VALID_BODY: AddCardBody = {
  provider: "culqi",
  token_id: "tkn_test_123",
  customer_info: {
    email: "test@tukijuris.pe",
    first_name: "Juan",
    last_name: "Pérez",
  },
};

describe("addCardToTrial", () => {
  it("POSTs to /api/trials/add-card with the exact body shape required by AddCardRequest", async () => {
    let capturedMethod = "";
    let capturedPath = "";
    let capturedContentType: string | null = "";
    let capturedBody: unknown = null;

    server.use(
      http.post("/api/trials/add-card", async ({ request }) => {
        capturedMethod = request.method;
        capturedPath = new URL(request.url).pathname;
        capturedContentType = request.headers.get("content-type");
        capturedBody = await request.json();
        return HttpResponse.json(TRIAL_RESPONSE);
      }),
    );

    const result = await addCardToTrial(authFetch, VALID_BODY);

    expect(capturedMethod).toBe("POST");
    expect(capturedPath).toBe("/api/trials/add-card");
    expect(capturedContentType).toContain("application/json");
    expect(capturedBody).toEqual(VALID_BODY);
    expect(result.id).toBe(TRIAL_RESPONSE.id);
    expect(result.provider).toBe("culqi");
  });

  it("forwards optional phone_number when provided", async () => {
    let capturedBody: unknown = null;
    server.use(
      http.post("/api/trials/add-card", async ({ request }) => {
        capturedBody = await request.json();
        return HttpResponse.json(TRIAL_RESPONSE);
      }),
    );

    await addCardToTrial(authFetch, {
      ...VALID_BODY,
      customer_info: { ...VALID_BODY.customer_info, phone_number: "+51999999999" },
    });

    expect(capturedBody).toMatchObject({
      customer_info: { phone_number: "+51999999999" },
    });
  });

  it("throws with the HTTP status attached when backend returns 4xx", async () => {
    server.use(
      http.post("/api/trials/add-card", () =>
        HttpResponse.json({ detail: "Validation error" }, { status: 422 }),
      ),
    );

    try {
      await addCardToTrial(authFetch, VALID_BODY);
      throw new Error("expected addCardToTrial to throw");
    } catch (err) {
      expect(err).toBeInstanceOf(Error);
      expect((err as Error).message).toMatch(/addCardToTrial failed: 422/);
      expect((err as Error & { status: number }).status).toBe(422);
    }
  });

  it("throws on 404 (no active trial for current user)", async () => {
    server.use(
      http.post("/api/trials/add-card", () =>
        HttpResponse.json({ detail: "No active trial found" }, { status: 404 }),
      ),
    );

    await expect(addCardToTrial(authFetch, VALID_BODY)).rejects.toThrow(
      /addCardToTrial failed: 404/,
    );
  });
});
