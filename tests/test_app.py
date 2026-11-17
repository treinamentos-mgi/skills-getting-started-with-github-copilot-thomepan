from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


client = TestClient(app)
ACTIVITY_NAME = "Basketball Team"


@pytest.fixture(autouse=True)
def restore_activities():
    original_activities = deepcopy(activities)
    yield
    activities.clear()
    activities.update(original_activities)


def test_get_activities_returns_all_activities():
    response = client.get("/activities")

    assert response.status_code == 200
    assert response.json() == activities


def test_signup_adds_student_to_activity():
    email = "student@mergington.edu"

    response = client.post(
        f"/activities/{ACTIVITY_NAME}/signup", params={"email": email}
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": f"Signed up {email} for {ACTIVITY_NAME}"
    }
    assert email in activities[ACTIVITY_NAME]["participants"]


def test_signup_returns_404_for_unknown_activity():
    response = client.post(
        "/activities/Unknown Activity/signup",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_returns_400_for_duplicate_student():
    email = "student@mergington.edu"
    activities[ACTIVITY_NAME]["participants"].append(email)

    response = client.post(
        f"/activities/{ACTIVITY_NAME}/signup", params={"email": email}
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"
    assert activities[ACTIVITY_NAME]["participants"].count(email) == 1


def test_signup_returns_400_when_activity_is_full():
    activity = activities[ACTIVITY_NAME]
    activity["participants"] = [
        f"participant-{index}@mergington.edu"
        for index in range(activity["max_participants"])
    ]

    response = client.post(
        f"/activities/{ACTIVITY_NAME}/signup",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Activity is full"
    assert len(activity["participants"]) == activity["max_participants"]


def test_cancel_signup_removes_student_from_activity():
    email = "student@mergington.edu"
    activities[ACTIVITY_NAME]["participants"].append(email)

    response = client.delete(
        f"/activities/{ACTIVITY_NAME}/signup", params={"email": email}
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": f"Canceled {email}'s signup for {ACTIVITY_NAME}"
    }
    assert email not in activities[ACTIVITY_NAME]["participants"]


def test_cancel_signup_returns_404_for_unknown_activity():
    response = client.delete(
        "/activities/Unknown Activity/signup",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_cancel_signup_returns_404_for_student_not_signed_up():
    response = client.delete(
        f"/activities/{ACTIVITY_NAME}/signup",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"