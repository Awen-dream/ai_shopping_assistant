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
