import { useState } from "react";

export default function App() {
  const [q, setQ] = useState("");
  const [customerId, setCustomerId] = useState("1");
  const [results, setResults] = useState([]);
  const [msg, setMsg] = useState(null);

  async function doSearch() {
    setMsg(null);
    if (!q.trim()) {
      setMsg({ type: "error", text: "Escribe un texto para buscar." });
      return;
    }
    const r = await fetch(`/api/search?q=${encodeURIComponent(q)}`);
    const data = await r.json().catch(() => ({}));
    if (!r.ok) {
      setMsg({ type: "error", text: data.detail || "Error buscando" });
      return;
    }
    setResults(data);
    setMsg({ type: "ok", text: `Resultados: ${data.length}` });
  }

  async function buy(trackId) {
    setMsg(null);
    if (!customerId.trim()) {
      setMsg({ type: "error", text: "Customer ID requerido." });
      return;
    }
    const r = await fetch(`/api/purchase`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ customer_id: Number(customerId), track_id: Number(trackId), quantity: 1 }),
    });
    const data = await r.json().catch(() => ({}));
    if (!r.ok) {
      setMsg({ type: "error", text: data.detail || "Error comprando" });
      return;
    }
    setMsg({ type: "ok", text: `Compra OK. Invoice: ${data.invoice_id} Total: ${data.total}` });
  }

  return (
    <div style={{ maxWidth: 900, margin: "40px auto", fontFamily: "system-ui" }}>
      <h2>Chinook Store</h2>

      <div style={{ display: "flex", gap: 8, marginBottom: 12 }}>
        <input
          placeholder="Busca por canción, artista o género..."
          value={q}
          onChange={(e) => setQ(e.target.value)}
          style={{ flex: 1, padding: 10 }}
        />
        <button onClick={doSearch} style={{ padding: "10px 16px" }}>Buscar</button>
      </div>

      <div style={{ display: "flex", gap: 8, marginBottom: 12 }}>
        <input
          placeholder="Customer ID"
          value={customerId}
          onChange={(e) => setCustomerId(e.target.value)}
          style={{ width: 140, padding: 10 }}
        />
        <small>Tip: prueba con Customer ID = 1</small>
      </div>

      {msg && (
        <div style={{ padding: 10, marginBottom: 12, border: "1px solid #ccc" }}>
          <b>{msg.type === "ok" ? "✅" : "❌"}</b> {msg.text}
        </div>
      )}

      <table width="100%" cellPadding="8" style={{ borderCollapse: "collapse" }}>
        <thead>
          <tr>
            <th align="left">Track</th>
            <th align="left">Artist</th>
            <th align="left">Genre</th>
            <th align="right">Price</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {results.map((r) => (
            <tr key={r.trackid} style={{ borderTop: "1px solid #eee" }}>
              <td>{r.track}</td>
              <td>{r.artist}</td>
              <td>{r.genre || "-"}</td>
              <td align="right">{r.unitprice}</td>
              <td align="right">
                <button onClick={() => buy(r.trackid)}>Comprar</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
