/**
 * api.js
 *
 * Thin wrapper around fetch() for talking to the Flask backend.
 * Every backend response follows { success, data|error } (see
 * backend/utils/responses.py), so this wrapper normalizes that into
 * either a resolved value or a thrown Error with a readable message.
 *
 * Auth token attachment is wired up in Phase 3 once Firebase Auth
 * gives us getIdToken().
 */

const API_BASE_URL = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1"
  ? "http://localhost:5000"
  : "https://YOUR-RENDER-BACKEND-URL.onrender.com"; // TODO (Phase 10): set real deployed URL

async function apiRequest(path, { method = "GET", body, authToken } = {}) {
  const headers = { "Content-Type": "application/json" };
  if (authToken) {
    headers["Authorization"] = `Bearer ${authToken}`;
  }

  let response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch (networkErr) {
    throw new Error("Could not reach the server. Check your connection and try again.");
  }

  let payload;
  try {
    payload = await response.json();
  } catch {
    throw new Error(`Unexpected server response (status ${response.status}).`);
  }

  if (!response.ok || payload.success === false) {
    throw new Error(payload.error || `Request failed with status ${response.status}`);
  }

  return payload.data;
}

window.api = { request: apiRequest, baseUrl: API_BASE_URL };
