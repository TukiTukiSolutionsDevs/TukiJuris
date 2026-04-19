import "@testing-library/jest-dom";
import { afterAll, afterEach, beforeAll } from "vitest";
import { server } from "./msw/server";

// Start MSW server before all tests
beforeAll(() => server.listen({ onUnhandledRequest: "warn" }));

// Reset handlers between tests to avoid state leak
afterEach(() => server.resetHandlers());

// Stop server after all tests
afterAll(() => server.close());
