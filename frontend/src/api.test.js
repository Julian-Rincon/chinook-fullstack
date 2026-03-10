import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { getCustomer, getHealth, purchaseTrack, searchTracks } from "./api";

function mockJsonResponse(data, ok = true, status = 200) {
  return {
    ok,
    status,
    headers: {
      get: () => "application/json",
    },
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
    expect(fetch).toHaveBeenCalledWith("/api/health");
    expect(data).toEqual({ ok: true, db: 1 });
  });

  it("busca tracks con q y limit", async () => {
    fetch.mockResolvedValueOnce(mockJsonResponse([{ track_id: 1, track: "Song" }]));
    await searchTracks("rock", 20);
    expect(fetch).toHaveBeenCalledWith("/api/search?q=rock&limit=20");
  });

  it("consulta cliente", async () => {
    fetch.mockResolvedValueOnce(mockJsonResponse({ customer_id: 1, name: "Luis" }));
    const data = await getCustomer(1);
    expect(fetch).toHaveBeenCalledWith("/api/customer/1");
    expect(data.customer_id).toBe(1);
  });

  it("envía compra por POST", async () => {
    fetch.mockResolvedValueOnce(mockJsonResponse({ ok: true, invoice_id: 10 }));
    await purchaseTrack({ customerId: 1, trackId: 2, quantity: 3 });

    expect(fetch).toHaveBeenCalledWith(
      "/api/purchase",
      expect.objectContaining({
        method: "POST",
        headers: { "Content-Type": "application/json" },
      })
    );
  });
});
