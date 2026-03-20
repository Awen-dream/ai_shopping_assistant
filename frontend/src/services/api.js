export async function fetchMultiAgentResults(query) {
  const res = await fetch(`http://localhost:8000/multi-agent-task?q=${query}`);
  return await res.json();
}