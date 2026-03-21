from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_multi_agent_task_returns_results_wrapper():
    response = client.get("/multi-agent-task", params={"q": "耳机"})

    assert response.status_code == 200
    payload = response.json()
    assert "results" in payload
    assert payload["results"]
    assert payload["results"][0]["category"] == "耳机"


def test_multi_agent_task_rejects_empty_query():
    response = client.get("/multi-agent-task", params={"q": ""})

    assert response.status_code == 422


def test_image_route_falls_back_safely_for_invalid_image_bytes():
    response = client.post(
        "/multi-agent-task/image",
        files={"file": ("not-an-image.txt", b"not an image", "text/plain")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert "results" in payload
    assert payload["results"]
