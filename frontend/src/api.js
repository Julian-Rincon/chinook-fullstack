async function parseResponse(response, fallbackMessage) {
  const contentType = response.headers.get("content-type") || "";
  let payload = null;

  try {
    payload = contentType.includes("application/json")
      ? await response.json()
      : await response.text();
  } catch {
    payload = null;
  }

  if (!response.ok) {
    const detail =
      (payload && typeof payload === "object" && payload.detail) ||
      (typeof payload === "string" && payload) ||
      fallbackMessage;
    throw new Error(detail || fallbackMessage);
  }

  return payload;
}

function authHeaders(token) {
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export async function getHealth() {
  const response = await fetch("/api/health");
  return parseResponse(response, "No se pudo validar el estado del sistema.");
}

export async function searchTracks(q, limit = 20) {
  const response = await fetch(
    `/api/search?q=${encodeURIComponent(q)}&limit=${encodeURIComponent(limit)}`
  );
  return parseResponse(response, "No se pudo consultar la búsqueda.");
}

export async function getCustomer(customerId) {
  const response = await fetch(`/api/customer/${encodeURIComponent(customerId)}`);
  return parseResponse(response, "No se pudo consultar el cliente.");
}

export async function purchaseTrack({ customerId, trackId, quantity, token }) {
  const response = await fetch("/api/purchase", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...authHeaders(token),
    },
    body: JSON.stringify({
      customer_id: Number(customerId),
      track_id: Number(trackId),
      quantity: Number(quantity),
    }),
  });

  return parseResponse(response, "No se pudo realizar la compra.");
}

export async function registerUser({ fullName, email, password }) {
  const response = await fetch("/api/auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      full_name: fullName,
      email,
      password,
    }),
  });
  return parseResponse(response, "No se pudo registrar el usuario.");
}

export async function bootstrapAdmin({ fullName, email, password }) {
  const response = await fetch("/api/auth/bootstrap-admin", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      full_name: fullName,
      email,
      password,
    }),
  });
  return parseResponse(response, "No se pudo crear el admin.");
}

export async function loginUser({ email, password }) {
  const response = await fetch("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  return parseResponse(response, "No se pudo iniciar sesión.");
}

export async function getMe(token) {
  const response = await fetch("/api/auth/me", {
    headers: authHeaders(token),
  });
  return parseResponse(response, "No se pudo consultar la sesión.");
}

export async function listUsers(token) {
  const response = await fetch("/api/auth/admin/users", {
    headers: authHeaders(token),
  });
  return parseResponse(response, "No se pudo consultar los usuarios.");
}
