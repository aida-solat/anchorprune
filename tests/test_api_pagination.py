"""API pagination + response stability (v0.9)."""


def _create_run(client, domain="procurement"):
    return client.post(
        "/runs",
        json={"goal": "g", "domain": domain, "config_name": "mock"},
    ).json()


def test_api_pagination_runs(api_client):
    for _ in range(5):
        _create_run(api_client)

    page1 = api_client.get("/runs", params={"limit": 2, "offset": 0}).json()
    # Backward-compatible fields preserved.
    assert "runs" in page1 and "count" in page1
    assert page1["count"] == 2
    # New pagination metadata.
    assert page1["limit"] == 2
    assert page1["offset"] == 0
    assert page1["total"] == 5

    page2 = api_client.get("/runs", params={"limit": 2, "offset": 2}).json()
    assert page2["count"] == 2
    assert page2["offset"] == 2
    ids1 = {r["run_id"] for r in page1["runs"]}
    ids2 = {r["run_id"] for r in page2["runs"]}
    assert ids1.isdisjoint(ids2)


def test_api_pagination_default_shape_unchanged(api_client):
    _create_run(api_client)
    body = api_client.get("/runs").json()
    assert isinstance(body["runs"], list)
    assert body["count"] == 1
    assert body["total"] == 1


def test_api_pagination_audit(api_client):
    run_id = _create_run(api_client)["run_id"]
    api_client.post(f"/runs/{run_id}/payload", json={"content": "obs"})
    api_client.post(f"/runs/{run_id}/steps", json={"instruction": "proceed"})
    api_client.post(f"/runs/{run_id}/steps", json={"instruction": "continue"})

    full = api_client.get(f"/runs/{run_id}/audit").json()
    assert "events" in full
    total = full["total"]
    assert total >= 1

    page = api_client.get(
        f"/runs/{run_id}/audit", params={"limit": 1, "offset": 0}
    ).json()
    assert len(page["events"]) == 1
    assert page["limit"] == 1
    assert page["total"] == total


def test_api_pagination_metrics(api_client):
    run_id = _create_run(api_client)["run_id"]
    api_client.post(f"/runs/{run_id}/steps", json={"instruction": "a"})
    api_client.post(f"/runs/{run_id}/steps", json={"instruction": "b"})

    body = api_client.get(f"/runs/{run_id}/metrics").json()
    assert body["summary"]["total_steps"] == 2
    assert body["total"] == 2

    page = api_client.get(
        f"/runs/{run_id}/metrics", params={"limit": 1, "offset": 0}
    ).json()
    assert len(page["steps"]) == 1
    # Summary is computed over ALL steps regardless of paging.
    assert page["summary"]["total_steps"] == 2
