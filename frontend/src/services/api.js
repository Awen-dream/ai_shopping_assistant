export async function getRecommendations(query) {
  const res = await fetch(`http://localhost:8000/recommend?query=${encodeURIComponent(query)}`);
  return res.json();
}