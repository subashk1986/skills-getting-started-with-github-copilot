"""
Tests for the FastAPI application endpoints
"""
import pytest
from fastapi.testclient import TestClient
from src.app import app


client = TestClient(app)


class TestActivitiesEndpoints:
    """Test cases for activities endpoints"""

    def test_root_redirect(self):
        """Test that root redirects to static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "static/index.html" in response.headers["location"]

    def test_get_activities(self):
        """Test getting all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        
        activities = response.json()
        assert isinstance(activities, dict)
        assert "Basketball" in activities
        assert "Tennis Club" in activities
        assert "Debate Team" in activities
        
        # Check structure of activity
        basketball = activities["Basketball"]
        assert "description" in basketball
        assert "schedule" in basketball
        assert "max_participants" in basketball
        assert "participants" in basketball
        assert isinstance(basketball["participants"], list)

    def test_signup_for_activity_success(self):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Basketball/signup?email=test@mergington.edu"
        )
        assert response.status_code == 200
        
        result = response.json()
        assert "message" in result
        assert "test@mergington.edu" in result["message"]
        assert "Basketball" in result["message"]

    def test_signup_already_registered(self):
        """Test signup fails if student is already registered"""
        email = "duplicate@mergington.edu"
        
        # First signup should succeed
        response1 = client.post(
            f"/activities/Tennis Club/signup?email={email}"
        )
        assert response1.status_code == 200
        
        # Second signup with same email should fail
        response2 = client.post(
            f"/activities/Tennis Club/signup?email={email}"
        )
        assert response2.status_code == 400
        assert "already signed up" in response2.json()["detail"]

    def test_signup_nonexistent_activity(self):
        """Test signup fails for non-existent activity"""
        response = client.post(
            "/activities/Nonexistent Activity/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_unregister_success(self):
        """Test successful unregistration from an activity"""
        email = "unregister-test@mergington.edu"
        
        # First, sign up
        client.post(f"/activities/Art Studio/signup?email={email}")
        
        # Then unregister
        response = client.post(
            f"/activities/Art Studio/unregister?email={email}"
        )
        assert response.status_code == 200
        
        result = response.json()
        assert "message" in result
        assert email in result["message"]
        
        # Verify participant is removed
        activities = client.get("/activities").json()
        assert email not in activities["Art Studio"]["participants"]

    def test_unregister_not_registered(self):
        """Test unregister fails if student is not registered"""
        response = client.post(
            "/activities/Math Olympiad/unregister?email=notregistered@mergington.edu"
        )
        assert response.status_code == 400
        assert "not registered" in response.json()["detail"]

    def test_unregister_nonexistent_activity(self):
        """Test unregister fails for non-existent activity"""
        response = client.post(
            "/activities/Fake Activity/unregister?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_participants_list_integrity(self):
        """Test that participant list is maintained correctly"""
        # Get initial count
        initial = client.get("/activities").json()
        initial_count = len(initial["Drama Club"]["participants"])
        
        email = "integrity-test@mergington.edu"
        
        # Sign up
        client.post(f"/activities/Drama Club/signup?email={email}")
        
        # Check count increased
        after_signup = client.get("/activities").json()
        assert len(after_signup["Drama Club"]["participants"]) == initial_count + 1
        assert email in after_signup["Drama Club"]["participants"]
        
        # Unregister
        client.post(f"/activities/Drama Club/unregister?email={email}")
        
        # Check count back to original
        after_unregister = client.get("/activities").json()
        assert len(after_unregister["Drama Club"]["participants"]) == initial_count
        assert email not in after_unregister["Drama Club"]["participants"]


class TestEmailValidation:
    """Test cases for email validation"""

    def test_signup_with_invalid_email_no_at_symbol(self):
        """Test signup fails with email missing @ symbol"""
        response = client.post(
            "/activities/Basketball/signup?email=testmergington.edu"
        )
        assert response.status_code == 400
        assert "Invalid email format" in response.json()["detail"]

    def test_signup_with_invalid_email_no_domain(self):
        """Test signup fails with email missing domain"""
        response = client.post(
            "/activities/Basketball/signup?email=test@"
        )
        assert response.status_code == 400
        assert "Invalid email format" in response.json()["detail"]

    def test_signup_with_invalid_email_no_extension(self):
        """Test signup fails with email missing extension"""
        response = client.post(
            "/activities/Basketball/signup?email=test@mergington"
        )
        assert response.status_code == 400
        assert "Invalid email format" in response.json()["detail"]

    def test_signup_with_empty_email(self):
        """Test signup fails with empty email"""
        response = client.post(
            "/activities/Basketball/signup?email="
        )
        assert response.status_code == 400
        assert "Invalid email format" in response.json()["detail"]

    def test_signup_with_email_with_spaces(self):
        """Test signup fails with email containing spaces"""
        response = client.post(
            "/activities/Basketball/signup?email=test user@mergington.edu"
        )
        assert response.status_code == 400
        assert "Invalid email format" in response.json()["detail"]

    def test_signup_with_valid_email_variations(self):
        """Test signup succeeds with various valid email formats (mergington.edu domain)"""
        valid_emails = [
            "simple@mergington.edu",
            "user.name@mergington.edu",
            "user_name@mergington.edu",
            "user123@mergington.edu"
        ]
        
        for email in valid_emails:
            response = client.post(
                f"/activities/Chess Club/signup?email={email}"
            )
            # Email validation should pass (activity might be full, but email format is valid)
            assert response.status_code in [200, 400]
            if response.status_code == 400:
                # If error, should be about activity, not email format
                assert "Invalid email format" not in response.json()["detail"]

    def test_signup_with_wrong_domain(self):
        """Test signup fails with non-mergington.edu domain"""
        invalid_domain_emails = [
            "user@example.com",
            "user@gmail.com",
            "user@mergington.com",
            "user@mergington.org"
        ]
        
        for email in invalid_domain_emails:
            response = client.post(
                f"/activities/Basketball/signup?email={email}"
            )
            assert response.status_code == 400
            assert "Invalid email format" in response.json()["detail"]
