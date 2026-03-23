const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

async function parseJsonResponse(response) {
  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`);
  }

  return response.json();
}

export async function fetchMultiAgentResults(query, userId = "") {
  const params = new URLSearchParams({ q: query });
  if (userId) {
    params.set("user_id", userId);
  }

  const response = await fetch(
    `${API_BASE_URL}/multi-agent-task?${params.toString()}`
  );
  return parseJsonResponse(response);
}

export async function fetchImageResults(file, userId = "") {
  const formData = new FormData();
  formData.append("file", file);
  if (userId) {
    formData.append("user_id", userId);
  }

  const response = await fetch(`${API_BASE_URL}/multi-agent-task/image`, {
    method: "POST",
    body: formData,
  });

  return parseJsonResponse(response);
}

export async function fetchVectorIndexStatus() {
  const response = await fetch(`${API_BASE_URL}/vector-index/status`);
  return parseJsonResponse(response);
}

export async function fetchAnalyticsSummary() {
  const response = await fetch(`${API_BASE_URL}/analytics/summary`);
  return parseJsonResponse(response);
}

export async function fetchAnalyticsDashboard(limit = 5) {
  const response = await fetch(`${API_BASE_URL}/analytics/dashboard?limit=${limit}`);
  return parseJsonResponse(response);
}

export async function sendFeedbackEvent(payload) {
  const response = await fetch(`${API_BASE_URL}/analytics/feedback`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return parseJsonResponse(response);
}

export async function rebuildVectorIndex(persist = true) {
  const response = await fetch(
    `${API_BASE_URL}/vector-index/rebuild?persist=${persist ? "true" : "false"}`,
    { method: "POST" }
  );
  return parseJsonResponse(response);
}

export async function fetchProducts() {
  const response = await fetch(`${API_BASE_URL}/products`);
  return parseJsonResponse(response);
}

export async function createProduct(payload) {
  const response = await fetch(`${API_BASE_URL}/products`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return parseJsonResponse(response);
}

export async function updateProduct(productId, payload) {
  const response = await fetch(`${API_BASE_URL}/products/${productId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return parseJsonResponse(response);
}

export async function deleteProduct(productId) {
  const response = await fetch(`${API_BASE_URL}/products/${productId}`, {
    method: "DELETE",
  });
  return parseJsonResponse(response);
}

export async function fetchUserProfile(userId) {
  const response = await fetch(`${API_BASE_URL}/user-profiles/${encodeURIComponent(userId)}`);
  return parseJsonResponse(response);
}

export async function saveUserProfile(userId, payload) {
  const response = await fetch(`${API_BASE_URL}/user-profiles/${encodeURIComponent(userId)}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return parseJsonResponse(response);
}
