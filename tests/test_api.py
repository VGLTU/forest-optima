# -*- coding: utf-8 -*-
"""
Тестирование REST API и сохранения рабочих пространств в SQLite.
"""

import pytest
from starlette.testclient import TestClient

from forest_optima.web.app import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    test_db = tmp_path / "test_forest.db"
    monkeypatch.setattr("forest_optima.web.app.DB_PATH", test_db)
    monkeypatch.setattr("forest_optima.web.app.DATA_DIR", tmp_path)

    with TestClient(app) as tc:
        yield tc


def test_health_check(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "forest-optima"


def test_serve_html_index(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Лес-Оптима" in response.text


def test_workspace_lifecycle(client):
    uid = "test-session-12345"

    # 1. Первый запрос к новому UID должен создать дефолтное пространство
    resp_get = client.get(f"/api/workspace/{uid}")
    assert resp_get.status_code == 200
    data_get = resp_get.json()
    assert data_get["uid"] == uid
    assert "districts" in data_get["data"]
    assert len(data_get["data"]["districts"]) == 6

    # 2. Обновление / сохранение
    new_data = {
        "name": "Тестовый сценарий тайги",
        "data": {
            "weights": {"stock": 0.6, "area": 0.2, "roads": 0.2},
            "districts": [
                {"id": 1, "name": "Участок 1", "stock": 1000.0, "area": 5000.0, "roads": 20.0}
            ],
            "enterprises": [
                {"id": 1, "name": "Леспромхоз", "econ": 4.5, "ecol": 4.0, "soc": 4.5}
            ]
        }
    }
    resp_post = client.post(f"/api/workspace/{uid}", json=new_data)
    assert resp_post.status_code == 200
    saved = resp_post.json()
    assert saved["name"] == "Тестовый сценарий тайги"
    assert len(saved["data"]["districts"]) == 1

    # 3. Проверка повторного чтения
    resp_get2 = client.get(f"/api/workspace/{uid}")
    assert resp_get2.status_code == 200
    assert resp_get2.json()["name"] == "Тестовый сценарий тайги"

    # 4. Проверка изоляции пользователей
    # Пользователь user1 должен видеть свой сценарий
    resp_user1 = client.get("/api/workspaces", headers={"X-User-Id": "user1"})
    # Пока сценарий был сохранен без owner_id, но с owner_id:
    client.post(f"/api/workspace/{uid}", json=new_data, headers={"X-User-Id": "user1"})
    resp_user1 = client.get("/api/workspaces", headers={"X-User-Id": "user1"})
    assert resp_user1.status_code == 200
    assert any(item["uid"] == uid for item in resp_user1.json())

    # Другой пользователь (или аноним в инкогнито) НЕ должен видеть чужие сценарии
    resp_incognito = client.get("/api/workspaces", headers={"X-User-Id": "user_incognito_anonymous"})
    assert resp_incognito.status_code == 200
    assert not any(item["uid"] == uid for item in resp_incognito.json())

    # Анонимный запрос без заголовка также возвращает пустой список
    resp_anon = client.get("/api/workspaces")
    assert resp_anon.status_code == 200
    assert resp_anon.json() == []


def test_calculate_endpoint(client):
    payload = {
        "weights": {"stock": 0.5, "area": 0.2, "roads": 0.3},
        "districts": [
            {"id": 1, "name": "Лесхоз А", "stock": 5000.0, "area": 30000.0, "roads": 70.0},
            {"id": 2, "name": "Лесхоз Б", "stock": 2000.0, "area": 10000.0, "roads": 20.0}
        ],
        "enterprises": [
            {"id": 1, "name": "Предприятие 1", "econ": 5.0, "ecol": 5.0, "soc": 5.0},
            {"id": 2, "name": "Предприятие 2", "econ": 3.0, "ecol": 2.0, "soc": 1.0}
        ]
    }
    resp = client.post("/api/calculate", json=payload)
    assert resp.status_code == 200
    res_data = resp.json()
    assert len(res_data["districts"]) == 2
    assert res_data["districts"][0]["optimal_rank"] == 1
    assert len(res_data["enterprises"]) == 2
    assert "Абсолютная гармония" in res_data["enterprises"][0]["euler_venn_zone"]


def test_export_excel_endpoint(client):
    payload = {
        "weights": {"stock": 0.5, "area": 0.2, "roads": 0.3},
        "districts": [
            {"id": 1, "name": "Лесхоз А", "stock": 5000.0, "area": 30000.0, "roads": 70.0}
        ],
        "enterprises": [
            {"id": 1, "name": "Предприятие 1", "econ": 5.0, "ecol": 5.0, "soc": 5.0}
        ]
    }
    resp = client.post("/api/export/excel", json=payload)
    assert resp.status_code == 200
    assert "spreadsheetml.sheet" in resp.headers["content-type"]
    assert len(resp.content) > 1000  # Валидный бинарный файл xlsx
