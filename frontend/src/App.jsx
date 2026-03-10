import { useEffect, useMemo, useState } from "react";
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

const SAMPLE_TERMS = ["rock", "jazz", "queen", "metal", "blues"];
const TOKEN_KEY = "chinook_token";

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

  const [token, setToken] = useState(localStorage.getItem(TOKEN_KEY) || "");
  const [authUser, setAuthUser] = useState(null);
  const [authMode, setAuthMode] = useState("login");
  const [authForm, setAuthForm] = useState({
    fullName: "",
    email: "",
    password: "",
  });
  const [authLoading, setAuthLoading] = useState(false);
  const [authError, setAuthError] = useState("");
  const [authSuccess, setAuthSuccess] = useState("");

  const [adminUsers, setAdminUsers] = useState([]);
  const [adminLoading, setAdminLoading] = useState(false);
  const [adminError, setAdminError] = useState("");

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

  useEffect(() => {
    const loadSession = async () => {
      if (!token) {
        setAuthUser(null);
        return;
      }

      try {
        const me = await getMe(token);
        setAuthUser(me);
      } catch {
        localStorage.removeItem(TOKEN_KEY);
        setToken("");
        setAuthUser(null);
      }
    };

    loadSession();
  }, [token]);

  const persistSession = (sessionToken, user) => {
    localStorage.setItem(TOKEN_KEY, sessionToken);
    setToken(sessionToken);
    setAuthUser(user);
  };

  const clearSession = () => {
    localStorage.removeItem(TOKEN_KEY);
    setToken("");
    setAuthUser(null);
    setAdminUsers([]);
  };

  const handleAuthSubmit = async () => {
    setAuthLoading(true);
    setAuthError("");
    setAuthSuccess("");

    try {
      if (!authForm.email.trim() || !authForm.password.trim()) {
        throw new Error("Email y contraseña son obligatorios.");
      }

      if (authMode !== "login" && !authForm.fullName.trim()) {
        throw new Error("El nombre completo es obligatorio.");
      }

      if (authMode === "login") {
        const result = await loginUser({
          email: authForm.email,
          password: authForm.password,
        });
        persistSession(result.access_token, result.user);
        setAuthSuccess("Sesión iniciada correctamente.");
      }

      if (authMode === "register") {
        await registerUser({
          fullName: authForm.fullName,
          email: authForm.email,
          password: authForm.password,
        });
        setAuthSuccess("Usuario registrado. Ahora inicia sesión.");
        setAuthMode("login");
      }

      if (authMode === "bootstrap") {
        const result = await bootstrapAdmin({
          fullName: authForm.fullName,
          email: authForm.email,
          password: authForm.password,
        });
        persistSession(result.access_token, result.user);
        setAuthSuccess("Admin creado e inicio de sesión exitoso.");
      }
    } catch (error) {
      setAuthError(error.message || "No se pudo completar la autenticación.");
    } finally {
      setAuthLoading(false);
    }
  };

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

  const handlePurchase = async () => {
    const parsedCustomerId = Number(String(customerId).trim());
    const parsedQuantity = Number(String(quantity).trim());

    setPurchaseError("");
    setPurchaseSuccess("");

    if (!authUser || !token) {
      setPurchaseError("Debes iniciar sesión para comprar canciones.");
      return;
    }

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
        token,
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

  const handleLoadUsers = async () => {
    setAdminLoading(true);
    setAdminError("");
    try {
      const data = await listUsers(token);
      setAdminUsers(Array.isArray(data) ? data : []);
    } catch (error) {
      setAdminUsers([]);
      setAdminError(error.message || "No se pudo consultar usuarios.");
    } finally {
      setAdminLoading(false);
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
              Busca canciones, consulta clientes, compra canciones con autenticación y gestiona roles
              de usuario/admin sobre FastAPI + PostgreSQL en AWS.
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

        <section className="grid auth-layout">
          <article className="card">
            <div className="card-header">
              <h2>Autenticación y roles</h2>
              <p>Modo rápido para cumplir registro, login y roles admin/usuario.</p>
            </div>

            {!authUser ? (
              <>
                <div className="tab-row">
                  <button
                    className={`tab-btn ${authMode === "login" ? "active" : ""}`}
                    onClick={() => setAuthMode("login")}
                  >
                    Login
                  </button>
                  <button
                    className={`tab-btn ${authMode === "register" ? "active" : ""}`}
                    onClick={() => setAuthMode("register")}
                  >
                    Registro usuario
                  </button>
                  <button
                    className={`tab-btn ${authMode === "bootstrap" ? "active" : ""}`}
                    onClick={() => setAuthMode("bootstrap")}
                  >
                    Crear primer admin
                  </button>
                </div>

                <div className="form-stack">
                  {authMode !== "login" && (
                    <input
                      aria-label="Nombre completo"
                      type="text"
                      placeholder="Nombre completo"
                      value={authForm.fullName}
                      onChange={(e) => setAuthForm({ ...authForm, fullName: e.target.value })}
                    />
                  )}

                  <input
                    aria-label="Email auth"
                    type="email"
                    placeholder="correo@ejemplo.com"
                    value={authForm.email}
                    onChange={(e) => setAuthForm({ ...authForm, email: e.target.value })}
                  />

                  <input
                    aria-label="Password auth"
                    type="password"
                    placeholder="Contraseña"
                    value={authForm.password}
                    onChange={(e) => setAuthForm({ ...authForm, password: e.target.value })}
                  />

                  <button onClick={handleAuthSubmit} disabled={authLoading}>
                    {authLoading
                      ? "Procesando..."
                      : authMode === "login"
                        ? "Iniciar sesión"
                        : authMode === "register"
                          ? "Registrar usuario"
                          : "Crear admin"}
                  </button>
                </div>

                {authError && <div className="alert error">{authError}</div>}
                {authSuccess && <div className="alert success">{authSuccess}</div>}
              </>
            ) : (
              <>
                <div className="session-box">
                  <div>
                    <strong>Sesión activa</strong>
                    <p>{authUser.full_name}</p>
                    <small>
                      {authUser.email} · <strong>{authUser.role}</strong>
                    </small>
                  </div>
                  <button onClick={clearSession}>Cerrar sesión</button>
                </div>

                {authUser.role === "admin" && (
                  <div className="admin-panel">
                    <div className="purchase-header">
                      <h3>Panel admin</h3>
                      <button onClick={handleLoadUsers} disabled={adminLoading}>
                        {adminLoading ? "Cargando..." : "Cargar usuarios"}
                      </button>
                    </div>

                    {adminError && <div className="alert error">{adminError}</div>}

                    {adminUsers.length > 0 && (
                      <div className="table-wrap">
                        <table>
                          <thead>
                            <tr>
                              <th>ID</th>
                              <th>Nombre</th>
                              <th>Email</th>
                              <th>Rol</th>
                            </tr>
                          </thead>
                          <tbody>
                            {adminUsers.map((user) => (
                              <tr key={user.user_id}>
                                <td>{user.user_id}</td>
                                <td>{user.full_name}</td>
                                <td>{user.email}</td>
                                <td>{user.role}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </div>
                )}
              </>
            )}
          </article>
        </section>

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
                              onClick={() => setSelectedTrack(item)}
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
                <li>Inicia sesión como usuario o admin.</li>
                <li>Busca una canción en la tabla de la izquierda.</li>
                <li>Presiona <strong>Seleccionar</strong>.</li>
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
