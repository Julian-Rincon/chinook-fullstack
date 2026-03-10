import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import App from "./App";
import * as api from "./api";

vi.mock("./api", () => ({
  getHealth: vi.fn(),
  searchTracks: vi.fn(),
  getCustomer: vi.fn(),
  purchaseTrack: vi.fn(),
}));

describe("App", () => {
  beforeEach(() => {
    api.getHealth.mockResolvedValue({ ok: true, db: 1 });
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
  });

  it("muestra el estado del sistema", async () => {
    render(<App />);
    expect(await screen.findByText(/Backend y BD activos/i)).toBeInTheDocument();
  });

  it("busca tracks y pinta resultados", async () => {
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

  it("consulta un cliente", async () => {
    const user = userEvent.setup();
    render(<App />);

    await user.click(screen.getByRole("button", { name: /^Consultar$/i }));

    expect(api.getCustomer).toHaveBeenCalledWith(1);
    expect(await screen.findByText("Luís Gonçalves")).toBeInTheDocument();
  });

  it("realiza una compra", async () => {
    api.searchTracks.mockResolvedValueOnce([
      {
        track_id: 2,
        track: "Fast As a Shark",
        artist: "Accept",
        genre: "Rock",
        price: 0.99,
      },
    ]);

    const user = userEvent.setup();
    render(<App />);

    await user.type(screen.getByLabelText(/Buscar canciones/i), "rock");
    await user.click(screen.getByRole("button", { name: /^Buscar$/i }));
    await user.click(await screen.findByRole("button", { name: /Seleccionar Fast As a Shark/i }));

    await user.click(screen.getByRole("button", { name: /^Consultar$/i }));
    await user.click(screen.getByRole("button", { name: /Comprar canción/i }));

    expect(api.purchaseTrack).toHaveBeenCalledWith({
      customerId: 1,
      trackId: 2,
      quantity: 1,
    });

    expect(await screen.findByText(/Compra realizada con éxito/i)).toBeInTheDocument();
  });
});
