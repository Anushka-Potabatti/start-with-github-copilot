import pytest
from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)


class TestActivitiesEndpoint:
    """Tests for GET /activities endpoint"""

    def test_get_all_activities(self):
        """Should return all activities"""
        # Arrange
        expected_activities = ["Chess Club", "Programming Class", "Tennis Club"]
        
        # Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        assert response.status_code == 200
        assert isinstance(data, dict)
        for activity in expected_activities:
            assert activity in data

    def test_activity_structure(self):
        """Should have correct structure for each activity"""
        # Arrange
        required_fields = ["description", "schedule", "max_participants", "participants"]
        
        # Act
        response = client.get("/activities")
        data = response.json()
        activity = data["Chess Club"]
        
        # Assert
        for field in required_fields:
            assert field in activity
        assert isinstance(activity["participants"], list)


class TestSignupEndpoint:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_successful_signup(self):
        """Should successfully sign up a new student"""
        # Arrange
        activity_name = "Tennis%20Club"
        email = "newsignup@mergington.edu"
        
        # Act
        response = client.post(f"/activities/{activity_name}/signup?email={email}")
        data = response.json()
        
        # Assert
        assert response.status_code == 200
        assert "Signed up" in data["message"]
        assert email in data["message"]

    def test_signup_duplicate_email(self):
        """Should reject signup for already registered student"""
        # Arrange
        activity_name = "Chess%20Club"
        duplicate_email = "michael@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={duplicate_email}"
        )
        data = response.json()
        
        # Assert
        assert response.status_code == 400
        assert "already signed up" in data["detail"]

    def test_signup_nonexistent_activity(self):
        """Should return 404 when activity does not exist"""
        # Arrange
        nonexistent_activity = "Fake%20Activity"
        email = "test@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{nonexistent_activity}/signup?email={email}"
        )
        data = response.json()
        
        # Assert
        assert response.status_code == 404
        assert "not found" in data["detail"]

    def test_signup_adds_to_participants_list(self):
        """Should add student to activity participants"""
        # Arrange
        activity_name = "Art%20Studio"
        test_email = "participanttest@mergington.edu"
        
        # Act
        client.post(f"/activities/{activity_name}/signup?email={test_email}")
        response = client.get("/activities")
        activity_data = response.json()["Art Studio"]
        
        # Assert
        assert test_email in activity_data["participants"]


class TestRemoveParticipantEndpoint:
    """Tests for DELETE /activities/{activity_name}/participants/{email} endpoint"""

    def test_successful_removal(self):
        """Should successfully remove a participant"""
        # Arrange
        activity_name = "Drama%20Club"
        email_to_remove = "grace@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants/{email_to_remove}"
        )
        data = response.json()
        
        # Assert
        assert response.status_code == 200
        assert "Removed" in data["message"]
        assert email_to_remove in data["message"]

    def test_remove_nonexistent_activity(self):
        """Should return 404 when trying to remove from non-existent activity"""
        # Arrange
        fake_activity = "Fake%20Activity"
        email = "test@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{fake_activity}/participants/{email}"
        )
        data = response.json()
        
        # Assert
        assert response.status_code == 404
        assert "not found" in data["detail"]

    def test_remove_participant_not_signed_up(self):
        """Should return 400 when participant is not in activity"""
        # Arrange
        activity_name = "Chess%20Club"
        not_signed_up_email = "notasignup@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants/{not_signed_up_email}"
        )
        data = response.json()
        
        # Assert
        assert response.status_code == 400
        assert "not signed up" in data["detail"]

    def test_remove_deletes_from_participants_list(self):
        """Should remove student from activity participants"""
        # Arrange
        activity_name = "Debate%20Club"
        email_to_remove = "noah@mergington.edu"
        
        # Act
        client.delete(f"/activities/{activity_name}/participants/{email_to_remove}")
        response = client.get("/activities")
        activity_data = response.json()["Debate Club"]
        
        # Assert
        assert email_to_remove not in activity_data["participants"]


class TestRootEndpoint:
    """Tests for GET / endpoint"""

    def test_root_redirect_to_static_html(self):
        """Should redirect root path to static HTML"""
        # Arrange
        expected_redirect = "/static/index.html"
        
        # Act
        response = client.get("/", follow_redirects=False)
        
        # Assert
        assert response.status_code == 307
        assert response.headers["location"] == expected_redirect


class TestDataIntegrity:
    """Tests to verify data consistency and business logic"""

    def test_participants_count_increments_after_signup(self):
        """Should increment participant count after successful signup"""
        # Arrange
        activity_name = "Gym%20Class"
        test_email = "counttest@mergington.edu"
        response_before = client.get("/activities")
        initial_count = len(response_before.json()["Gym Class"]["participants"])
        
        # Act
        client.post(f"/activities/{activity_name}/signup?email={test_email}")
        response_after = client.get("/activities")
        updated_count = len(response_after.json()["Gym Class"]["participants"])
        
        # Assert
        assert updated_count == initial_count + 1

    def test_availability_within_valid_range(self):
        """Should calculate availability as valid positive number"""
        # Arrange
        max_allowed = 30
        
        # Act
        response = client.get("/activities")
        activities_data = response.json()
        gym_activity = activities_data["Gym Class"]
        spots_left = gym_activity["max_participants"] - len(gym_activity["participants"])
        
        # Assert
        assert spots_left >= 0
        assert spots_left <= gym_activity["max_participants"]
