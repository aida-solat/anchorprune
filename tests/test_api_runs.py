"""Run lifecycle + payload endpoints."""


def _create_run(client, domain="procurement"):
    return client.post(
        "/runs",
        json={
            "goal": "Recommend the safest supplier.",
            "domain": domain,
            "config_name": "mock",
            "system_anchors": [
                {
                    "content": "A supplier cannot be recommended without verified compliance documentation.",
                    "anchor_type": "policy",
                    "priority": "critical",
                }
            ],
            "metadata": {"source": "api-test"},
        },
    )


def test_create_run(api_client):
    resp = _create_run(api_client)
    assert resp.status_code == 201
    body = resp.json()
    assert body["run_id"].startswith("run_")
    assert body["status"] == "created"
    assert body["domain"] == "procurement"


def test_get_run(api_client):
    run_id = _create_run(api_client).json()["run_id"]
    resp = api_client.get(f"/runs/{run_id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["run_id"] == run_id
    assert body["goal"] == "Recommend the safest supplier."
    assert body["metadata"]["source"] == "api-test"


def test_get_missing_run_returns_404(api_client):
    resp = api_client.get("/runs/run_does_not_exist")
    assert resp.status_code == 404
    error = resp.json()["error"]
    assert error["code"] == "RUN_NOT_FOUND"
    assert error["details"]["run_id"] == "run_does_not_exist"


def test_list_runs_and_domain_filter(api_client):
    _create_run(api_client, domain="procurement")
    _create_run(api_client, domain="coding_agent")
    all_runs = api_client.get("/runs").json()
    assert all_runs["count"] == 2
    filtered = api_client.get("/runs", params={"domain": "coding_agent"}).json()
    assert filtered["count"] == 1
    assert filtered["runs"][0]["domain"] == "coding_agent"


def test_add_payload(api_client):
    run_id = _create_run(api_client).json()["run_id"]
    resp = api_client.post(
        f"/runs/{run_id}/payload",
        json={
            "block_type": "tool_output",
            "content": "Supplier A is missing ISO9001 documentation.",
            "decision_impact": 0.8,
            "metadata": {"source": "erp_export"},
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "added"
    assert body["payload_block_id"]


def test_delete_run(api_client):
    run_id = _create_run(api_client).json()["run_id"]
    assert api_client.delete(f"/runs/{run_id}").status_code == 200
    assert api_client.get(f"/runs/{run_id}").status_code == 404
    # Deleting again is a 404.
    assert api_client.delete(f"/runs/{run_id}").status_code == 404
