/**
 * Culqi.js v3/v4 loader + tokenization helper.
 *
 * The Culqi SDK is loaded **on demand** by client components that need to
 * tokenize a card (e.g. AddCardModal in /billing). This keeps the script
 * out of the global bundle and out of pages that don't need it.
 *
 * Production usage:
 *   1. Set NEXT_PUBLIC_CULQI_PUBLIC_KEY in .env.production (pk_test_xxx or pk_live_xxx).
 *   2. Call `await loadCulqi()` from a React effect or event handler.
 *   3. Call `tokenizeCard({...})` with the card data. NEVER send PAN/CVV to /api/*.
 *      The backend only ever receives the resulting tkn_xxx identifier.
 *
 * Reference: https://docs.culqi.com/
 *
 * NOTE: this file ships ready to use but the actual UI flow (PCI-safe form)
 * is deferred until Culqi habilita las credenciales (F2-PAY-02). The helper
 * is exported so that the AddCardModal swap is a 5-line change once we have
 * the public key.
 */

const CULQI_SCRIPT_SRC = "https://js.culqi.com/checkout-js";

declare global {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  interface Window {
    Culqi?: any;
  }
}

let loadPromise: Promise<void> | null = null;

export function loadCulqi(): Promise<void> {
  if (typeof window === "undefined") {
    return Promise.reject(new Error("loadCulqi must be called in the browser"));
  }
  if (window.Culqi) {
    return Promise.resolve();
  }
  if (loadPromise) return loadPromise;

  loadPromise = new Promise<void>((resolve, reject) => {
    const existing = document.querySelector<HTMLScriptElement>(
      `script[src="${CULQI_SCRIPT_SRC}"]`,
    );
    if (existing) {
      existing.addEventListener("load", () => resolve(), { once: true });
      existing.addEventListener("error", () => reject(new Error("Culqi script failed to load")), {
        once: true,
      });
      return;
    }

    const script = document.createElement("script");
    script.src = CULQI_SCRIPT_SRC;
    script.async = true;
    script.onload = () => {
      const key = process.env.NEXT_PUBLIC_CULQI_PUBLIC_KEY || "";
      if (window.Culqi && key) {
        window.Culqi.publicKey = key;
      }
      resolve();
    };
    script.onerror = () => reject(new Error("Culqi script failed to load"));
    document.head.appendChild(script);
  });

  return loadPromise;
}

export interface CardData {
  card_number: string;
  cvv: string;
  expiration_month: string; // "01".."12"
  expiration_year: string;  // "2030"
  email: string;
}

export interface CulqiToken {
  id: string;          // "tkn_xxx"
  card_brand: string;
  last_four: string;
  bin: string;
}

/**
 * Tokenize a card using Culqi.js. Resolves with the token id (tkn_xxx) or
 * rejects with a user-friendly error message.
 *
 * Implementation note: Culqi exposes both a Checkout (full hosted UI) and a
 * lower-level token endpoint. For the AddCardModal we'll use the token
 * endpoint via window.Culqi.createToken(). Until Culqi habilita en
 * producción, this function will throw "Culqi not configured" so callers
 * can show a friendly stub.
 */
export async function tokenizeCard(card: CardData): Promise<CulqiToken> {
  await loadCulqi();
  const publicKey = process.env.NEXT_PUBLIC_CULQI_PUBLIC_KEY;
  if (!publicKey) {
    throw new Error(
      "Pagos no disponibles aún. Culqi se habilita 15 días después del despliegue.",
    );
  }
  if (!window.Culqi) {
    throw new Error("No se pudo cargar Culqi.js");
  }

  // The real implementation uses Culqi.createToken via callbacks; wrap in a Promise.
  return new Promise((resolve, reject) => {
    try {
      window.Culqi.publicKey = publicKey;
      window.Culqi.settings({ title: "TukiJuris", currency: "PEN" });
      window.Culqi.createToken(card, (response: { object: string; id?: string; card_brand?: string; last_four?: string; bin?: string; user_message?: string; merchant_message?: string }) => {
        if (response?.object === "token" && response.id) {
          resolve({
            id: response.id,
            card_brand: response.card_brand || "",
            last_four: response.last_four || "",
            bin: response.bin || "",
          });
        } else {
          reject(new Error(response?.user_message || response?.merchant_message || "Token rechazado"));
        }
      });
    } catch (err) {
      reject(err instanceof Error ? err : new Error("Error tokenizando la tarjeta"));
    }
  });
}
