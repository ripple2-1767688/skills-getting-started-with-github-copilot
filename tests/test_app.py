import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities to initial state before each test"""
    from app import activities
    
    # Store original activities
    original = {
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
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": ["john@mergington.edu", "olivia@mergington.edu"]
        }
    }
    
    # Clear and reset
    activities.clear()
    activities.update(original)
    
    yield
    
    # Reset again after test
    activities.clear()
    activities.update(original)


class TestRoot:
    """Test the root endpoint"""
    
    def test_root_redirect(self, client):
        """Test that root redirects to /static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivities:
    """Test the get activities endpoint"""
    
    def test_get_activities_success(self, client):
        """Test getting all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        
        data = response.json()
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data
        
    def test_get_activities_has_correct_structure(self, client):
        """Test that activities have the correct structure"""
        response = client.get("/activities")
        data = response.json()
        
        activity = data["Chess Club"]
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity
        assert isinstance(activity["participants"], list)


class TestSignup:
    """Test the signup endpoint"""
    
    def test_signup_success(self, client):
        """Test successful signup"""
        response = client.post(
            "/activities/Chess%20Club/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "Signed up" in data["message"]
        assert "newstudent@mergington.edu" in data["message"]
        
    def test_signup_adds_participant(self, client):
        """Test that signup actually adds the participant"""
        client.post(
            "/activities/Chess%20Club/signup",
            params={"email": "test@mergington.edu"}
        )
        
        response = client.get("/activities")
        data = response.json()
        assert "test@mergington.edu" in data["Chess Club"]["participants"]
        
    def test_signup_already_registered(self, client):
        """Test that signing up twice fails"""
        email = "michael@mergington.edu"
        response = client.post(
            "/activities/Chess%20Club/signup",
            params={"email": email}
        )
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]
        
    def test_signup_activity_not_found(self, client):
        """Test signup to non-existent activity"""
        response = client.post(
            "/activities/Nonexistent%20Activity/signup",
            params={"email": "test@mergington.edu"}
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
        
    def test_signup_participant_count_increases(self, client):
        """Test that participant count increases after signup"""
        response_before = client.get("/activities")
        count_before = len(response_before.json()["Chess Club"]["participants"])
        
        client.post(
            "/activities/Chess%20Club/signup",
            params={"email": "newuser@mergington.edu"}
        )
        
        response_after = client.get("/activities")
        count_after = len(response_after.json()["Chess Club"]["participants"])
        
        assert count_after == count_before + 1


class TestUnregister:
    """Test the unregister endpoint"""
    
    def test_unregister_success(self, client):
        """Test successful unregister"""
        response = client.post(
            "/activities/Chess%20Club/unregister",
            params={"email": "michael@mergington.edu"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"]
        assert "michael@mergington.edu" in data["message"]
        
    def test_unregister_removes_participant(self, client):
        """Test that unregister actually removes the participant"""
        client.post(
            "/activities/Chess%20Club/unregister",
            params={"email": "michael@mergington.edu"}
        )
        
        response = client.get("/activities")
        data = response.json()
        assert "michael@mergington.edu" not in data["Chess Club"]["participants"]
        
    def test_unregister_not_registered(self, client):
        """Test unregistering someone not in the activity"""
        response = client.post(
            "/activities/Chess%20Club/unregister",
            params={"email": "notregistered@mergington.edu"}
        )
        assert response.status_code == 400
        assert "not registered" in response.json()["detail"]
        
    def test_unregister_activity_not_found(self, client):
        """Test unregister from non-existent activity"""
        response = client.post(
            "/activities/Nonexistent%20Activity/unregister",
            params={"email": "michael@mergington.edu"}
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
        
    def test_unregister_participant_count_decreases(self, client):
        """Test that participant count decreases after unregister"""
        response_before = client.get("/activities")
        count_before = len(response_before.json()["Chess Club"]["participants"])
        
        client.post(
            "/activities/Chess%20Club/unregister",
            params={"email": "michael@mergington.edu"}
        )
        
        response_after = client.get("/activities")
        count_after = len(response_after.json()["Chess Club"]["participants"])
        
        assert count_after == count_before - 1


class TestIntegration:
    """Integration tests"""
    
    def test_signup_then_unregister(self, client):
        """Test signing up and then unregistering"""
        email = "integration@mergington.edu"
        activity = "Chess%20Club"
        
        # Signup
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert response.status_code == 200
        
        # Verify participant added
        response = client.get("/activities")
        assert email in response.json()["Chess Club"]["participants"]
        
        # Unregister
        response = client.post(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )
        assert response.status_code == 200
        
        # Verify participant removed
        response = client.get("/activities")
        assert email not in response.json()["Chess Club"]["participants"]
        
    def test_multiple_signups_and_unregisters(self, client):
        """Test multiple signup and unregister operations"""
        activity = "Gym%20Class"
        emails = ["user1@mergington.edu", "user2@mergington.edu", "user3@mergington.edu"]
        
        # Sign up all users
        for email in emails:
            response = client.post(
                f"/activities/{activity}/signup",
                params={"email": email}
            )
            assert response.status_code == 200
        
        # Verify all added
        response = client.get("/activities")
        for email in emails:
            assert email in response.json()["Gym Class"]["participants"]
        
        # Unregister some
        for email in emails[:2]:
            client.post(
                f"/activities/{activity}/unregister",
                params={"email": email}
            )
        
        # Verify correct ones removed
        response = client.get("/activities")
        participants = response.json()["Gym Class"]["participants"]
        assert emails[0] not in participants
        assert emails[1] not in participants
        assert emails[2] in participants
