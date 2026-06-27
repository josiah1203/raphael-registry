"""Registry domain tests."""

import uuid

from fastapi.testclient import TestClient

from raphael_registry.app import app

client = TestClient(app)


def test_list_empty() -> None:
    items = client.get("/v1/registry").json()["items"]
    assert isinstance(items, list)


def test_create_semver_manifest(monkeypatch) -> None:
    published: list[tuple] = []
    monkeypatch.setattr("raphael_contracts.kafka.publish_event", lambda t, d, **m: published.append((t, d)))

    res = client.post(
        "/v1/registry",
        json={
            "name": "sonoma-core",
            "version": "1.2.3",
            "manifest": {"schema": "module-v1"},
            "module_pins": [{"module_id": "mod-a", "ref": "main"}],
        },
    )
    assert res.status_code == 200
    body = res.json()
    assert body["version"] == "1.2.3"
    assert body["module_pins"][0]["module_id"] == "mod-a"
    assert any(p[0] == "raphael.registry.published" for p in published)


def test_rejects_invalid_semver() -> None:
    res = client.post("/v1/registry", json={"name": "bad", "version": "not-semver"})
    assert res.status_code == 400


def test_get_entry_not_found() -> None:
    res = client.get("/v1/registry/reg-does-not-exist")
    assert res.status_code == 404


def test_list_contains_created_entry(monkeypatch) -> None:
    monkeypatch.setattr("raphael_contracts.kafka.publish_event", lambda *a, **k: None)
    suffix = uuid.uuid4().hex[:6]
    created = client.post(
        "/v1/registry",
        json={"name": f"pkg-{suffix}", "version": "0.1.0", "manifest": {"schema": "module-v1"}},
    )
    assert created.status_code == 200
    entry_id = created.json()["id"]

    items = client.get("/v1/registry").json()["items"]
    assert any(item["id"] == entry_id for item in items)
