import { render, screen, fireEvent } from "@testing-library/react";
import App from "./App";

test("muestra título", () => {
  render(<App />);
  expect(screen.getByText("Chinook Store")).toBeInTheDocument();
});

test("valida búsqueda vacía", async () => {
  render(<App />);
  fireEvent.click(screen.getByText("Buscar"));
  expect(await screen.findByText(/Escribe un texto/i)).toBeInTheDocument();
});
