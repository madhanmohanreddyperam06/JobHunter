import uuid
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def create_test_user_and_auth() -> dict:
    """Helper to register a unique user and get authentication bearer headers."""
    email = f"interview_test_{uuid.uuid4().hex[:8]}@example.com"
    password = "TestPassword123"
    reg_res = client.post("/api/auth/register", json={
        "name": "Interview Test User",
        "email": email,
        "password": password,
    })
    assert reg_res.status_code == 201

    login_res = client.post("/api/auth/login", json={
        "email": email,
        "password": password,
    })
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def create_test_application(headers: dict, company_name: str = "Stripe", job_title: str = "Staff Engineer") -> int:
    """Helper to create a test application and return its ID."""
    res = client.post("/api/applications", json={
        "company_name": company_name,
        "job_title": job_title,
        "status": "INTERVIEW",
    }, headers=headers)
    assert res.status_code == 201
    return res.json()["id"]


class TestInterviewCreate:
    def test_create_interview_success(self):
        headers = create_test_user_and_auth()
        app_id = create_test_application(headers, "Stripe", "Senior Backend Engineer")

        payload = {
            "application_id": app_id,
            "round_name": "Technical Screen",
            "interview_type": "VIDEO",
            "scheduled_at": "2026-10-15T10:00:00",
            "duration_minutes": 60,
            "meeting_link": "https://meet.google.com/abc-defg-hij",
            "interviewer": "Sarah Senior Eng",
            "interviewer_email": "sarah@stripe.com",
            "location": "Google Meet",
            "status": "SCHEDULED",
            "notes": "Review distributed locking and idempotency patterns."
        }
        res = client.post("/api/interviews", json=payload, headers=headers)
        assert res.status_code == 201
        data = res.json()
        assert data["id"] is not None
        assert data["application_id"] == app_id
        assert data["round_name"] == "Technical Screen"
        assert data["interview_type"] == "VIDEO"
        assert data["duration_minutes"] == 60
        assert data["meeting_link"] == "https://meet.google.com/abc-defg-hij"
        assert data["interviewer"] == "Sarah Senior Eng"
        assert data["interviewer_email"] == "sarah@stripe.com"
        assert data["status"] == "SCHEDULED"
        assert data["notes"] == "Review distributed locking and idempotency patterns."
        assert data["job_title"] == "Senior Backend Engineer"
        assert data["company_name"] == "Stripe"
        assert data["application"]["id"] == app_id

    def test_create_interview_with_aliases(self):
        headers = create_test_user_and_auth()
        app_id = create_test_application(headers, "Meta", "Software Engineer")

        payload = {
            "application_id": app_id,
            "round_name": "System Design",
            "interview_type": "TECHNICAL",
            "meeting_url": "https://zoom.us/j/123456789",
            "interviewer_name": "Mark Zuckerberg",
        }
        res = client.post("/api/interviews", json=payload, headers=headers)
        assert res.status_code == 201
        data = res.json()
        assert data["meeting_link"] == "https://zoom.us/j/123456789"
        assert data["interviewer"] == "Mark Zuckerberg"

    def test_create_interview_unowned_application_returns_404(self):
        headers_user_a = create_test_user_and_auth()
        app_id_user_a = create_test_application(headers_user_a, "Apple", "iOS Dev")

        headers_user_b = create_test_user_and_auth()
        payload = {
            "application_id": app_id_user_a,
            "round_name": "Malicious Round",
            "interview_type": "VIDEO",
        }
        res = client.post("/api/interviews", json=payload, headers=headers_user_b)
        assert res.status_code == 404
        assert "not found or access denied" in res.json()["detail"].lower()

    def test_create_interview_nonexistent_application_returns_404(self):
        headers = create_test_user_and_auth()
        payload = {
            "application_id": 999999,
            "round_name": "Ghost Round",
        }
        res = client.post("/api/interviews", json=payload, headers=headers)
        assert res.status_code == 404

    def test_create_interview_invalid_status_returns_422(self):
        headers = create_test_user_and_auth()
        app_id = create_test_application(headers)
        payload = {
            "application_id": app_id,
            "round_name": "Screen",
            "status": "NON_EXISTENT_STATUS",
        }
        res = client.post("/api/interviews", json=payload, headers=headers)
        assert res.status_code == 422


class TestInterviewRead:
    def test_get_interview_by_id_success(self):
        headers = create_test_user_and_auth()
        app_id = create_test_application(headers, "Netflix", "Core Systems Engineer")

        create_res = client.post("/api/interviews", json={
            "application_id": app_id,
            "round_name": "Hiring Manager Chat",
            "interview_type": "BEHAVIORAL",
            "status": "SCHEDULED",
        }, headers=headers)
        assert create_res.status_code == 201
        interview_id = create_res.json()["id"]

        get_res = client.get(f"/api/interviews/{interview_id}", headers=headers)
        assert get_res.status_code == 200
        data = get_res.json()
        assert data["id"] == interview_id
        assert data["round_name"] == "Hiring Manager Chat"
        assert data["company_name"] == "Netflix"

    def test_get_interview_cross_user_returns_404(self):
        headers_user_a = create_test_user_and_auth()
        app_id_a = create_test_application(headers_user_a, "Amazon", "SDE II")

        create_res = client.post("/api/interviews", json={
            "application_id": app_id_a,
            "round_name": "Bar Raiser",
        }, headers=headers_user_a)
        assert create_res.status_code == 201
        interview_id = create_res.json()["id"]

        headers_user_b = create_test_user_and_auth()
        get_res = client.get(f"/api/interviews/{interview_id}", headers=headers_user_b)
        assert get_res.status_code == 404

    def test_get_interview_nonexistent_returns_404(self):
        headers = create_test_user_and_auth()
        get_res = client.get("/api/interviews/999999", headers=headers)
        assert get_res.status_code == 404


class TestInterviewListAndFilters:
    def test_list_interviews_user_isolation(self):
        headers_a = create_test_user_and_auth()
        app_a = create_test_application(headers_a, "Uber", "Driver Platform Eng")
        client.post("/api/interviews", json={"application_id": app_a, "round_name": "Round 1"}, headers=headers_a)
        client.post("/api/interviews", json={"application_id": app_a, "round_name": "Round 2"}, headers=headers_a)

        headers_b = create_test_user_and_auth()
        app_b = create_test_application(headers_b, "Lyft", "Rider Experience")
        client.post("/api/interviews", json={"application_id": app_b, "round_name": "Round B1"}, headers=headers_b)

        res_a = client.get("/api/interviews", headers=headers_a)
        assert res_a.status_code == 200
        assert res_a.json()["total"] == 2

        res_b = client.get("/api/interviews", headers=headers_b)
        assert res_b.status_code == 200
        assert res_b.json()["total"] == 1

    def test_list_interviews_pagination(self):
        headers = create_test_user_and_auth()
        app_id = create_test_application(headers, "Datadog", "Software Engineer")
        for i in range(5):
            client.post("/api/interviews", json={
                "application_id": app_id,
                "round_name": f"Round {i+1}",
            }, headers=headers)

        res = client.get("/api/interviews?page=1&page_size=2", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert len(data["items"]) == 2
        assert data["total"] == 5
        assert data["page"] == 1
        assert data["page_size"] == 2
        assert data["total_pages"] == 3

    def test_list_interviews_filter_by_status(self):
        headers = create_test_user_and_auth()
        app_id = create_test_application(headers, "Snowflake", "DB Kernel Eng")
        client.post("/api/interviews", json={"application_id": app_id, "round_name": "R1", "status": "SCHEDULED"}, headers=headers)
        client.post("/api/interviews", json={"application_id": app_id, "round_name": "R2", "status": "COMPLETED"}, headers=headers)

        res = client.get("/api/interviews?status=COMPLETED", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert data["total"] == 1
        assert data["items"][0]["status"] == "COMPLETED"

    def test_list_interviews_search(self):
        headers = create_test_user_and_auth()
        app_id = create_test_application(headers, "Palantir", "Forward Deployed Eng")
        client.post("/api/interviews", json={
            "application_id": app_id,
            "round_name": "Foundry Architecture Review",
            "interviewer": "Dr. Alex Karp",
            "notes": "Ontology pipeline design"
        }, headers=headers)

        # Search by interviewer
        res1 = client.get("/api/interviews?search=Alex", headers=headers)
        assert res1.status_code == 200
        assert res1.json()["total"] == 1

        # Search by company name
        res2 = client.get("/api/interviews?search=Palantir", headers=headers)
        assert res2.status_code == 200
        assert res2.json()["total"] == 1

        # Search non-matching
        res3 = client.get("/api/interviews?search=NonExistentEntityXYZ", headers=headers)
        assert res3.status_code == 200
        assert res3.json()["total"] == 0


class TestInterviewUpdateAndDelete:
    def test_update_interview_success(self):
        headers = create_test_user_and_auth()
        app_id = create_test_application(headers, "Airbnb", "Search Team")
        create_res = client.post("/api/interviews", json={
            "application_id": app_id,
            "round_name": "Initial Screen",
            "duration_minutes": 30,
        }, headers=headers)
        interview_id = create_res.json()["id"]

        update_payload = {
            "round_name": "Deep Dive Technical Interview",
            "duration_minutes": 75,
            "notes": "Prepare query optimization presentation.",
        }
        res = client.put(f"/api/interviews/{interview_id}", json=update_payload, headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert data["round_name"] == "Deep Dive Technical Interview"
        assert data["duration_minutes"] == 75
        assert data["notes"] == "Prepare query optimization presentation."

    def test_patch_interview_status_success(self):
        headers = create_test_user_and_auth()
        app_id = create_test_application(headers)
        create_res = client.post("/api/interviews", json={
            "application_id": app_id,
            "round_name": "Onsite 1",
            "status": "SCHEDULED"
        }, headers=headers)
        interview_id = create_res.json()["id"]

        patch_res = client.patch(f"/api/interviews/{interview_id}/status", json={"status": "COMPLETED"}, headers=headers)
        assert patch_res.status_code == 200
        assert patch_res.json()["status"] == "COMPLETED"

    def test_patch_interview_status_invalid_enum_returns_422(self):
        headers = create_test_user_and_auth()
        app_id = create_test_application(headers)
        create_res = client.post("/api/interviews", json={
            "application_id": app_id,
            "round_name": "Onsite 2",
        }, headers=headers)
        interview_id = create_res.json()["id"]

        patch_res = client.patch(f"/api/interviews/{interview_id}/status", json={"status": "BAD_STATUS"}, headers=headers)
        assert patch_res.status_code == 422

    def test_delete_interview_success(self):
        headers = create_test_user_and_auth()
        app_id = create_test_application(headers)
        create_res = client.post("/api/interviews", json={
            "application_id": app_id,
            "round_name": "To be deleted",
        }, headers=headers)
        interview_id = create_res.json()["id"]

        del_res = client.delete(f"/api/interviews/{interview_id}", headers=headers)
        assert del_res.status_code == 204

        # Confirm deleted
        get_res = client.get(f"/api/interviews/{interview_id}", headers=headers)
        assert get_res.status_code == 404

    def test_delete_interview_cross_user_returns_404(self):
        headers_a = create_test_user_and_auth()
        app_id = create_test_application(headers_a)
        create_res = client.post("/api/interviews", json={
            "application_id": app_id,
            "round_name": "User A Private Round",
        }, headers=headers_a)
        interview_id = create_res.json()["id"]

        headers_b = create_test_user_and_auth()
        del_res = client.delete(f"/api/interviews/{interview_id}", headers=headers_b)
        assert del_res.status_code == 404


class TestInterviewUnauthenticated:
    def test_unauthenticated_endpoints_return_401(self):
        assert client.get("/api/interviews").status_code == 401
        assert client.post("/api/interviews", json={"round_name": "Test"}).status_code == 401
        assert client.get("/api/interviews/1").status_code == 401
        assert client.put("/api/interviews/1", json={"round_name": "Test"}).status_code == 401
        assert client.patch("/api/interviews/1/status", json={"status": "COMPLETED"}).status_code == 401
        assert client.delete("/api/interviews/1").status_code == 401
