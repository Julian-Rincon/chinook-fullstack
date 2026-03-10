import { useEffect, useMemo, useState } from "react";
import { getCustomer, getHealth, purchaseTrack, searchTracks } from "./api";

const SAMPLE_TERMS = ["rock", "jazz", "queen", "metal", "blues"];

function formatUsd(value) {
  const amount = Number(value);
  if (Number.isNaN(amount)) return "—";
  return new Intl.NumberFormat("es-CO", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
  }).format(amount);
}

export default function App() {
  const [health, setHealth] = useState({ loading: true, ok: false, db: null });

  const [query, setQuery] = useState("");
  const [tracks, setTracks] = useState([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchError, setSearchError] = useState("");
  const [searchNotice, setSearchNotice] = useState("");

  const [customerId, setCustomerId] = useState("1");
  const [customer, setCustomer] = useState(null);
  const [customerLoading, setCustomerLoading] = useState(false);
  const [customerError, setCustomerError] = useState("");

  const [selectedTrack, setSelectedTrack] = useState(null);
  const [quantity, setQuantity] = useState("1");
  const [purchaseLoading, setPurchaseLoading] = useState(false);
  const [purchaseError, setPurchaseError] = useState("");
  const [purchaseSuccess, setPurchaseSuccess] = useState("");

  useEffect(() => {
    const loadHealth = async () => {
      try {
        const data = await getHealth();
        setHealth({ loading: false, ok: !!data?.ok, db: data?.db ?? null });
      } catch {
        setHealth({ loading: false, ok: false, db: null });
      }
    };

    loadHealth();
  }, []);

  const loadCustomer = async (idOverride = customerId) => {
    const parsedId = Number(String(idOverride).trim());

    if (!parsedId || parsedId < 1) {
      setCustomer(null);
      setCustomerError("Ingresa un Customer ID válido.");
      return null;
    }

    setCustomerLoading(true);
    setCustomerError("");

    try {
      const data = await getCustomer(parsedId);
      setCustomer(data);
      return data;
    } catch (error) {
      setCustomer(null);
      setCustomerError(error.message || "No se pudo consultar el cliente.");
      return null;
    } finally {
      setCustomerLoading(false);
    }
  };

  const handleSearch = async (termOverride = query) => {
    const term = String(termOverride).trim();

    if (!term) {
      setTracks([]);
      setSearchError("Escribe un término para buscar canciones, artistas o géneros.");
      setSearchNotice("");
      return;
    }

    setSearchLoading(true);
    setSearchError("");
    setSearchNotice("");

    try {
      const results = await searchTracks(term, 20);
      setTracks(Array.isArray(results) ? results : []);
      setSearchNotice(
        Array.isArray(results) && results.length
          ? `Resultados encontrados: ${results.length}`
          : "No se encontraron coincidencias."
      );
    } catch (error) {
      setTracks([]);
      setSearchError(error.message || "No se pudo consultar la búsqueda.");
    } finally {
      setSearchLoading(false);
    }
  };

  const handleSelectTrack = (track) => {
    setSelectedTrack(track);
    setPurchaseError("");
    setPurchaseSuccess("");
  };

  const handlePurchase = async () => {
    const parsedCustomerId = Number(String(customerId).trim());
    const parsedQuantity = Number(String(quantity).trim());

    setPurchaseError("");
    setPurchaseSuccess("");

    if (!selectedTrack) {
      setPurchaseError("Selecciona una canción antes de comprar.");
      return;
    }

    if (!parsedCustomerId || parsedCustomerId < 1) {
      setPurchaseError("Ingresa un Customer ID válido.");
      return;
    }

    if (!parsedQuantity || parsedQuantity < 1) {
      setPurchaseError("La cantidad debe ser mayor o igual a 1.");
      return;
    }

    setPurchaseLoading(true);

    try {
      const result = await purchaseTrack({
        customerId: parsedCustomerId,
        trackId: selectedTrack.track_id,
        quantity: parsedQuantity,
      });

      setPurchaseSuccess(
        `Compra realizada con éxito. Factura #${result.invoice_id} por ${formatUsd(result.total)}.`
      );

      await loadCustomer(parsedCustomerId);
    } catch (error) {
      setPurchaseError(error.message || "No se pudo realizar la compra.");
    } finally {
      setPurchaseLoading(false);
    }
  };

  const customerSummary = useMemo(() => {
    if (!customer) return null;
    return {
      name: customer.name ?? "—",
      email: customer.email ?? "—",
      country: customer.country ?? "—",
      total: customer.total ?? 0,
      invoices: customer.invoices ?? 0,
    };
  }, [customer]);

  return (
    <div className="page-shell">
      <div className="page-overlay" />

      <main className="app">
        <header className="hero-card">
          <div>
            <span className="badge">Chinook Fullstack</span>
            <h1>Chinook Store</h1>
            <p className="hero-text">
              Busca canciones por texto, consulta clientes y realiza compras conectándote al backend
              FastAPI y a PostgreSQL en AWS.
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
                aria-label="Buscar canciones"
                type="text"
                placeholder="Ej: rock, queen, jazz..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSearch()}
              />
              <button onClick={() => handleSearch()} disabled={searchLoading}>
                {searchLoading ? "Buscando..." : "Buscar"}
              </button>
            </div>

            <div className="chip-row">
              {SAMPLE_TERMS.map((term) => (
                <button
                  key={term}
                  className="chip"
                  onClick={() => {
                    setQuery(term);
                    handleSearch(term);
                  }}
                >
                  {term}
                </button>
              ))}
            </div>

            {searchError && <div className="alert error">{searchError}</div>}
            {!searchError && searchNotice && <div className="alert info">{searchNotice}</div>}

            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Track</th>
                    <th>Artist</th>
                    <th>Genre</th>
                    <th>Price</th>
                    <th>Acción</th>
                  </tr>
                </thead>
                <tbody>
                  {!searchLoading && tracks.length === 0 ? (
                    <tr>
                      <td colSpan="5" className="empty-cell">
                        Aún no hay resultados. Prueba con <strong>rock</strong>, <strong>jazz</strong> o{" "}
                        <strong>queen</strong>.
                      </td>
                    </tr>
                  ) : (
                    tracks.map((item) => {
                      const isSelected = selectedTrack?.track_id === item.track_id;
                      return (
                        <tr key={item.track_id} className={isSelected ? "row-selected" : ""}>
                          <td>{item.track}</td>
                          <td>{item.artist}</td>
                          <td>{item.genre}</td>
                          <td>{formatUsd(item.price)}</td>
                          <td>
                            <button
                              className="table-btn"
                              aria-label={`Seleccionar ${item.track}`}
                              onClick={() => handleSelectTrack(item)}
                            >
                              {isSelected ? "Seleccionada" : "Seleccionar"}
                            </button>
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>
          </article>

          <article className="card">
            <div className="card-header">
              <h2>Consulta de cliente y compra</h2>
              <p>Consulta un cliente y compra una canción seleccionada.</p>
            </div>

            <div className="customer-row">
              <input
                aria-label="Customer ID"
                type="number"
                min="1"
                value={customerId}
                onChange={(e) => setCustomerId(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && loadCustomer()}
              />
              <button onClick={() => loadCustomer()} disabled={customerLoading}>
                {customerLoading ? "Consultando..." : "Consultar"}
              </button>
            </div>

            <div className="hint-box">
              <strong>Cómo usar la página</strong>
              <ol>
                <li>Busca una canción en la tabla de la izquierda.</li>
                <li>Presiona <strong>Seleccionar</strong> en la canción que quieres comprar.</li>
                <li>Consulta un cliente con <strong>Customer ID = 1</strong>.</li>
                <li>Define la cantidad y presiona <strong>Comprar canción</strong>.</li>
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
                <span>Total histórico</span>
                <strong>{customerSummary ? formatUsd(customerSummary.total) : "—"}</strong>
              </div>
              <div className="summary-card">
                <span>Facturas</span>
                <strong>{customerSummary?.invoices ?? "—"}</strong>
              </div>
            </div>

            <div className="purchase-panel">
              <div className="purchase-header">
                <h3>Compra</h3>
                {selectedTrack ? (
                  <span className="selected-tag">
                    {selectedTrack.track} · {formatUsd(selectedTrack.price)}
                  </span>
                ) : (
                  <span className="selected-tag muted">Sin canción seleccionada</span>
                )}
              </div>

              <div className="customer-row">
                <input
                  aria-label="Cantidad"
                  type="number"
                  min="1"
                  value={quantity}
                  onChange={(e) => setQuantity(e.target.value)}
                />
                <button onClick={handlePurchase} disabled={purchaseLoading}>
                  {purchaseLoading ? "Comprando..." : "Comprar canción"}
                </button>
              </div>

              {purchaseError && <div className="alert error">{purchaseError}</div>}
              {purchaseSuccess && <div className="alert success">{purchaseSuccess}</div>}
            </div>

            <details className="raw-json">
              <summary>Ver respuesta completa del cliente</summary>
              <pre>{customer ? JSON.stringify(customer, null, 2) : "Sin datos cargados."}</pre>
            </details>
          </article>
        </section>
      </main>
    </div>
  );
}
