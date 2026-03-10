import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  bootstrapAdmin,
  getCustomer,
  getHealth,
  getMe,
  listUsers,
  loginUser,
  purchaseTrack,
  registerUser,
  searchTracks,
} from "./api";

function mockJsonResponse(data, ok = true) {
  return {
    ok,
    headers: { get: () => "application/json" },
    json: async () => data,
    text: async () => JSON.stringify(data),
  };
}

describe("api services", () => {
  beforeEach(() => {
    global.fetch = vi.fn();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("consulta health", async () => {
    fetch.mockResolvedValueOnce(mockJsonResponse({ ok: true, db: 1 }));
    const data = await getHealth();
    expect(data.ok).toBe(true);
  });

  it("busca tracks", async () => {
    fetch.mockResolvedValueOnce(mockJsonResponse([]));
    await searchTracks("rock", 20);
    expect(fetch).toHaveBeenCalledWith("/api/search?q=rock&limit=20");
  });

  it("consulta cliente", async () => {
    fetch.mockResolvedValueOnce(mockJsonResponse({ customer_id: 1 }));
    const data = await getCustomer(1);
    expect(data.customer_id).toBe(1);
  });

  it("hace purchase con token", async () => {
    fetch.mockResolvedValueOnce(mockJsonResponse({ ok: true }));
    await purchaseTrack({ customerId: 1, trackId: 2, quantity: 1, token: "abc" });
    expect(fetch).toHaveBeenCalledWith(
      "/api/purchase",
      expect.objectContaining({
        method: "POST",
        headers: expect.objectContaining({
          Authorization: "Bearer abc",
        }),
      })
    );
  });

  it("registra usuario", async () => {
    fetch.mockResolvedValueOnce(mockJsonResponse({ ok: true }));
    await registerUser({ fullName: "User", email: "u@test.com", password: "secret123" });
    expect(fetch).toHaveBeenCalledWith("/api/auth/register", expect.any(Object));
  });

  it("crea admin", async () => {
    fetch.mockResolvedValueOnce(mockJsonResponse({ access_token: "x" }));
    const data = await bootstrapAdmin({ fullName: "Admin", email: "a@test.com", password: "secret123" });
    expect(data.access_token).toBe("x");
  });

  it("hace login", async () => {
    fetch.mockResolvedValueOnce(mockJsonResponse({ access_token: "x", user: { role: "user" } }));
    const data = await loginUser({ email: "u@test.com", password: "secret123" });
    expect(data.access_token).toBe("x");
  });

  it("consulta me y users", async () => {
    fetch
      .mockResolvedValueOnce(mockJsonResponse({ user_id: 1 }))
      .mockResolvedValueOnce(mockJsonResponse([{ user_id: 1 }]));
    const me = await getMe("abc");
    const users = await listUsers("abc");
    expect(me.user_id).toBe(1);
    expect(users[0].user_id).toBe(1);
  });
});
