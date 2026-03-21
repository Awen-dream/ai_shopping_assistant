const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

async function parseJsonResponse(response) {
  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`);
  }

  return response.json();
}

export async function fetchMultiAgentResults(query) {
  const response = await fetch(
    `${API_BASE_URL}/multi-agent-task?q=${encodeURIComponent(query)}`
  );
  return parseJsonResponse(response);
}

export async function fetchImageResults(file) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}/multi-agent-task/image`, {
    method: "POST",
    body: formData,
  });

  return parseJsonResponse(response);
}
