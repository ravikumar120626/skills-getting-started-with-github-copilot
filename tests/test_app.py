from fastapi.testclient import TestClient
import pytest

from src.app import app, activities

TEST_ACTIVITIES = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    }
}

@ pytest.fixture(autouse=True)
def reset_activities():
    # Arrange: restore a known activity state before each test
    activities.clear()
    for name, data in TEST_ACTIVITIES.items():
        activities[name] = {
            "description": data["description"],
            "schedule": data["schedule"],
            "max_participants": data["max_participants"],
            "participants": list(data["participants"])
        }

    yield


@pytest.fixture
def client():
    return TestClient(app)


def test_root_redirects_to_static_index(client):
    # Arrange: client fixture is ready
    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activity_list(client):
    # Arrange
    expected_names = set(TEST_ACTIVITIES.keys())

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    returned = response.json()
    assert set(returned.keys()) == expected_names
    assert returned["Chess Club"]["schedule"] == "Fridays, 3:30 PM - 5:00 PM"


def test_signup_for_activity_succeeds_for_new_student(client):
    # Arrange
    body = {"email": "student@mergington.edu"}

    # Act
    response = client.post("/activities/Chess Club/signup", params=body)

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": "Signed up student@mergington.edu for Chess Club"}
    assert "student@mergington.edu" in activities["Chess Club"]["participants"]


def test_signup_for_missing_activity_returns_404(client):
    # Arrange
    body = {"email": "student@mergington.edu"}

    # Act
    response = client.post("/activities/Unknown/signup", params=body)

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_for_existing_student_returns_400(client):
    # Arrange
    body = {"email": "michael@mergington.edu"}

    # Act
    response = client.post("/activities/Chess Club/signup", params=body)

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up"


def test_remove_participant_succeeds_for_existing_student(client):
    # Arrange
    params = {"email": "michael@mergington.edu"}

    # Act
    response = client.delete("/activities/Chess Club/participants", params=params)

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": "Removed michael@mergington.edu from Chess Club"}
    assert "michael@mergington.edu" not in activities["Chess Club"]["participants"]


def test_remove_participant_from_unknown_activity_returns_404(client):
    # Arrange
    params = {"email": "student@mergington.edu"}

    # Act
    response = client.delete("/activities/Unknown/participants", params=params)

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_remove_unknown_participant_returns_404(client):
    # Arrange
    params = {"email": "missing@mergington.edu"}

    # Act
    response = client.delete("/activities/Chess Club/participants", params=params)

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Participant not found"
