from fastapi.testclient import TestClient

from learning_ecosystem.web.app import create_app


def test_learner_and_admin_shell() -> None:
    client = TestClient(create_app(":memory:"))
    home = client.get("/")
    assert home.status_code == 200
    assert "Continue learning" in home.text
    assert "Curriculum &amp; knowledge" in home.text or "Curriculum & knowledge" in home.text

    learn = client.get("/learn")
    assert learn.status_code == 200
    assert "poc-learner-001" in learn.text
    assert "POC-SESSION-001" in learn.text
    assert "Start a new session" in learn.text

    admin = client.get("/admin")
    assert admin.status_code == 200
    assert "Flow Bulk Execution Semantics" in admin.text
    assert "flow-collection-scope" in admin.text
    assert "OAuth architecture" in admin.text

    started = client.post("/learn/start", follow_redirects=False)
    assert started.status_code == 303
    live = client.get(started.headers["location"])
    assert live.status_code == 200
    assert "Your answer" in live.text
    assert "I'm stuck" in live.text
