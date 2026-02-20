from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src import app as app_module


@pytest.fixture(autouse=True)
def restore_activities_state():
    original_activities = deepcopy(app_module.activities)
    yield
    app_module.activities.clear()
    app_module.activities.update(deepcopy(original_activities))


@pytest.fixture
def client():
    return TestClient(app_module.app)


def test_root_redirects_to_static_index(client):
    response = client.get("/", follow_redirects=False)
    assert response.status_code in (302, 307)
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_expected_payload(client):
    response = client.get("/activities")

    assert response.status_code == 200
    payload = response.json()
    assert "Basketball Team" in payload
    assert "participants" in payload["Basketball Team"]


def test_signup_successfully_registers_student(client):
    activity_name = "Basketball Team"
    email = "new.student@mergington.edu"

    response = client.post(f"/activities/{activity_name}/signup", params={"email": email})

    assert response.status_code == 200
    assert email in app_module.activities[activity_name]["participants"]


def test_signup_rejects_duplicate_student(client):
    activity_name = "Basketball Team"
    existing_email = app_module.activities[activity_name]["participants"][0]

    response = client.post(
        f"/activities/{activity_name}/signup", params={"email": existing_email}
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up"


def test_signup_rejects_unknown_activity(client):
    response = client.post(
        "/activities/Unknown Activity/signup", params={"email": "student@mergington.edu"}
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_rejects_when_activity_is_full(client):
    activity_name = "Basketball Team"
    app_module.activities[activity_name]["max_participants"] = len(
        app_module.activities[activity_name]["participants"]
    )

    response = client.post(
        f"/activities/{activity_name}/signup", params={"email": "extra@mergington.edu"}
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Activity is full"


def test_unregister_successfully_removes_student(client):
    activity_name = "Swimming Club"
    email = app_module.activities[activity_name]["participants"][0]

    response = client.post(
        f"/activities/{activity_name}/unregister", params={"email": email}
    )

    assert response.status_code == 200
    assert email not in app_module.activities[activity_name]["participants"]


def test_unregister_rejects_unknown_activity(client):
    response = client.post(
        "/activities/Unknown Activity/unregister", params={"email": "student@mergington.edu"}
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_rejects_non_registered_student(client):
    response = client.post(
        "/activities/Swimming Club/unregister", params={"email": "not.registered@mergington.edu"}
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not registered for this activity"