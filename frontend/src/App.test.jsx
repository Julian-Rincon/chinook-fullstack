import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import App from "./App";
import * as api from "./api";

vi.mock("./api", () => ({
  bootstrapAdmin: vi.fn(),
  getCustomer: vi.fn(),
  getHealth: vi.fn(),
  getMe: vi.fn(),
  listUsers: vi.fn(),
  loginUser: vi.fn(),
  purchaseTrack: vi.fn(),
  registerUser: vi.fn(),
  searchTracks: vi.fn(),
}));

describe("App", () => {
  beforeEach(() => {
    localStorage.clear();
    api.getHealth.mockResolvedValue({ ok: true, db: 1 });
    api.getMe.mockResolvedValue({
      user_id: 1,
      full_name: "Tester",
      email: "tester@test.com",
      role: "user",
      is_active: true,
    });
    api.searchTracks.mockResolvedValue([]);
    api.getCustomer.mockResolvedValue({
      customer_id: 1,
      name: "Luís Gonçalves",
      email: "luisg@embraer.com.br",
      country: "Brazil",
      total: 39.62,
      invoices: 7,
    });
    api.purchaseTrack.mockResolvedValue({
      ok: true,
      invoice_id: 99,
      total: 0.99,
    });
    api.loginUser.mockResolvedValue({
      access_token: "token-123",
      user: {
        user_id: 1,
        full_name: "Tester",
        email: "tester@test.com",
        role: "user",
        is_active: true,
      },
    });
    api.registerUser.mockResolvedValue({
      ok: true,
      user: { role: "user" },
    });
  });

  it("renderiza la página", async () => {
    render(<App />);
    //xd
    expect(screen.getByText(/Chinook Store/i)).toBeInTheDocument();
    expect(await screen.findByText(/Backend y BD activos/i)).toBeInTheDocument();
  });

  it("permite login", async () => {
    const user = userEvent.setup();
    render(<App />);

    await user.type(screen.getByLabelText(/Email auth/i), "tester@test.com");
    await user.type(screen.getByLabelText(/Password auth/i), "secret123");
    await user.click(screen.getByRole("button", { name: /Iniciar sesión/i }));

    expect(api.loginUser).toHaveBeenCalled();
    expect(await screen.findByText(/Sesión activa/i)).toBeInTheDocument();
  });

  it("permite buscar tracks", async () => {
    api.searchTracks.mockResolvedValueOnce([
      {
        track_id: 1,
        track: "Balls to the Wall",
        artist: "Accept",
        genre: "Rock",
        price: 0.99,
      },
    ]);

    const user = userEvent.setup();
    render(<App />);

    await user.type(screen.getByLabelText(/Buscar canciones/i), "rock");
    await user.click(screen.getByRole("button", { name: /^Buscar$/i }));

    expect(api.searchTracks).toHaveBeenCalledWith("rock", 20);
    expect(await screen.findByText("Balls to the Wall")).toBeInTheDocument();
  });
});
