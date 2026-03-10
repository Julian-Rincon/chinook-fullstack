import { useEffect, useMemo, useState } from "react";

const API = {
  health: "/api/health",
  search: (q) => `/api/search?q=${encodeURIComponent(q)}`, // <- ajusta esta si tu backend usa otra ruta
  customer: (id) => `/api/customer/${encodeURIComponent(id)}`, // <- ajusta esta si tu backend usa otra ruta
};

const sampleTerms = ["rock", "jazz", "queen", "metal", "blues"];

function firstValue(obj, keys, fallback = "—") {
  for (const key of keys) {
    if (obj && obj[key] !== undefined && obj[key] !== null && obj[key] !== "") {
      return obj[key];
    }
  }
  return fallback;
}

function normalizeTracks(payload) {
  if (Array.isArray(payload)) return payload;
  if (Array.isArray(payload?.items)) return payload.items;
  if (Array.isArray(payload?.results)) return payload.results;
  if (Array.isArray(payload?.tracks)) return payload.tracks;
  return [];
}

function formatPrice(value) {
  const n = Number(value);
  if (Number.isNaN(n)) return value ?? "—";
  return new Intl.NumberFormat("es-CO", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
  }).format(n);
}

export default function App() {
  const [query, setQuery] = useState("");
  const [customerId, setCustomerId] = useState("1");

  const [health, setHealth] = useState({ loading: true, ok: false, db: null });
  const [tracks, setTracks] = useState([]);
  const [customerData, setCustomerData] = useState(null);

  const [searchLoading, setSearchLoading] = useState(false);
  const [customerLoading, setCustomerLoading] = useState(false);

  const [searchError, setSearchError] = useState("");
  const [customerError, setCustomerError] = useState("");

  useEffect(() => {
    const loadHealth = async () => {
      try {
        const res = await fetch(API.health);
        const data = await res.json();
        setHealth({ loading: false, ok: !!data?.ok, db: data?.db ?? null });
      } catch {
        setHealth({ loading: false, ok: false, db: null });
      }
    };
    loadHealth();
  }, []);

  const searchTracks = async (customQuery) => {
    const term = (customQuery ?? query).trim();
    if (!term) {
      setTracks([]);
      setSearchError("Escribe un término para buscar canciones, artistas o géneros.");
      return;
    }

    setSearchLoading(true);
    setSearchError("");

    try {
      const res = await fetch(API.search(term));
      if (!res.ok) throw new Error("No se pudo consultar la búsqueda.");
      const data = await res.json();
      setTracks(normalizeTracks(data));
    } catch (err) {
      setTracks([]);
      setSearchError(err.message || "Ocurrió un error al buscar.");
    } finally {
      setSearchLoading(false);
    }
  };

  const loadCustomer = async () => {
    const id = String(customerId).trim();
    if (!id) {
      setCustomerData(null);
      setCustomerError("Ingresa un Customer ID.");
      return;
    }

    setCustomerLoading(true);
    setCustomerError("");

    try {
      const res = await fetch(API.customer(id));
      if (!res.ok) throw new Error("No se pudo consultar el cliente.");
      const data = await res.json();
      setCustomerData(data);
    } catch (err) {
      setCustomerData(null);
      setCustomerError(err.message || "Ocurrió un error al consultar el cliente.");
    } finally {
      setCustomerLoading(false);
    }
  };

  const customerSummary = useMemo(() => {
    if (!customerData || typeof customerData !== "object") return null;

    return {
      name: firstValue(customerData, ["name", "full_name", "customer_name", "CustomerName"]),
      email: firstValue(customerData, ["email", "Email"]),
      country: firstValue(customerData, ["country", "Country"]),
      total: firstValue(customerData, ["total", "Total", "total_spent", "TotalSpent"]),
      invoices: firstValue(customerData, ["invoices", "Invoices", "invoice_count", "InvoiceCount"]),
    };
  }, [customerData]);

  return (
    <div className="page-shell">
      <div className="page-overlay" />

      <main className="app">
        <header className="hero-card">
          <div>
            <span className="badge">Chinook Fullstack</span>
            <h1>Chinook Store</h1>
            <p className="hero-text">
              Busca canciones por texto y consulta información de clientes conectándote al backend FastAPI y a la base
              de datos PostgreSQL en AWS.
            </p>
          </div>

          <div className="status-box">
            <div className="status-title">Estado del sistema</div>
            <div className={`status-pill ${health.ok ? "ok" : "fail"}`}>
              {health.loading ? "Verificando..." : health.ok ? "Backend y BD activos" : "Sin conexión"}
            </div>
            <small>DB: {health.loading ? "..." : health.db ?? "—"}</small>
          </div>
        </header>

        <section className="grid two-col">
          <article className="card">
            <div className="card-header">
              <h2>Búsqueda de tracks</h2>
              <p>Busca por nombre de canción, artista o género.</p>
            </div>

            <div className="search-row">
              <input
                type="text"
                placeholder="Ej: rock, queen, jazz..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && searchTracks()}
              />
              <button onClick={() => searchTracks()} disabled={searchLoading}>
                {searchLoading ? "Buscando..." : "Buscar"}
              </button>
            </div>

            <div className="chip-row">
              {sampleTerms.map((term) => (
                <button
                  key={term}
                  className="chip"
                  onClick={() => {
                    setQuery(term);
                    searchTracks(term);
                  }}
                >
                  {term}
                </button>
              ))}
            </div>

            {searchError && <div className="alert error">{searchError}</div>}

            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Track</th>
                    <th>Artist</th>
                    <th>Genre</th>
                    <th>Price</th>
                  </tr>
                </thead>
                <tbody>
                  {!searchLoading && tracks.length === 0 ? (
                    <tr>
                      <td colSpan="4" className="empty-cell">
                        Aún no hay resultados. Prueba con <strong>rock</strong>, <strong>jazz</strong> o{" "}
                        <strong>queen</strong>.
                      </td>
                    </tr>
                  ) : (
                    tracks.map((item, index) => (
                      <tr key={index}>
                        <td>{firstValue(item, ["track", "Track", "name", "Name", "track_name", "TrackName"])}</td>
                        <td>{firstValue(item, ["artist", "Artist", "artist_name", "ArtistName"])}</td>
                        <td>{firstValue(item, ["genre", "Genre", "genre_name", "GenreName"])}</td>
                        <td>{formatPrice(firstValue(item, ["price", "Price", "unit_price", "UnitPrice"], "—"))}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </article>

          <article className="card">
            <div className="card-header">
              <h2>Consulta de cliente</h2>
              <p>Usa un Customer ID para ver datos rápidos del cliente.</p>
            </div>

            <div className="customer-row">
              <input
                type="number"
                min="1"
                value={customerId}
                onChange={(e) => setCustomerId(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && loadCustomer()}
              />
              <button onClick={loadCustomer} disabled={customerLoading}>
                {customerLoading ? "Consultando..." : "Consultar"}
              </button>
            </div>

            <div className="hint-box">
              <strong>Cómo usar la página</strong>
              <ol>
                <li>Escribe un término en la búsqueda y presiona <strong>Buscar</strong>.</li>
                <li>Para clientes, prueba con <strong>Customer ID = 1</strong>.</li>
                <li>Si no ves datos, revisa que las rutas del bloque <code>API</code> coincidan con tu backend.</li>
              </ol>
            </div>

            {customerError && <div className="alert error">{customerError}</div>}

            <div className="summary-grid">
              <div className="summary-card">
                <span>Cliente</span>
                <strong>{customerSummary?.name ?? "—"}</strong>
              </div>
              <div className="summary-card">
                <span>Email</span>
                <strong>{customerSummary?.email ?? "—"}</strong>
              </div>
              <div className="summary-card">
                <span>País</span>
                <strong>{customerSummary?.country ?? "—"}</strong>
              </div>
              <div className="summary-card">
                <span>Total</span>
                <strong>{customerSummary?.total ?? "—"}</strong>
              </div>
            </div>

            <details className="raw-json">
              <summary>Ver respuesta completa del cliente</summary>
              <pre>{customerData ? JSON.stringify(customerData, null, 2) : "Sin datos cargados."}</pre>
            </details>
          </article>
        </section>
      </main>
    </div>
  );
}
