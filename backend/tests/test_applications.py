import uuid
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def create_test_user_and_auth() -> dict:
    """Helper to register a unique user and get authentication bearer headers."""
    email = f"app_test_{uuid.uuid4().hex[:8]}@example.com"
    password = "TestPassword123"
    reg_res = client.post("/api/auth/register", json={
        "name": "App Test User",
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


class TestApplicationCreate:
    def test_create_application_success(self):
        headers = create_test_user_and_auth()
        payload = {
            "company_name": "Google",
            "job_title": "Software Engineer III",
            "location": "Bangalore",
            "job_url": "https://careers.google.com/jobs/123",
            "salary": 3500000,
            "employment_type": "Full-time",
            "status": "APPLIED",
            "job_description": "Build high-scale distributed systems.",
            "applied_date": "2026-09-20",
        }
        res = client.post("/api/applications", json=payload, headers=headers)
        assert res.status_code == 201
        data = res.json()
        assert data["id"] is not None
        assert data["job_title"] == "Software Engineer III"
        assert data["company"]["name"] == "Google"
        assert data["status"] == "APPLIED"
        assert data["salary"] == "3500000"
        assert data["applied_date"] == "2026-09-20"

    def test_create_application_unauthorized(self):
        payload = {
            "company_name": "Microsoft",
            "job_title": "Product Manager",
        }
        res = client.post("/api/applications", json=payload)
        assert res.status_code == 401

    def test_create_application_missing_required_fields(self):
        headers = create_test_user_and_auth()
        # Missing job_title
        res = client.post("/api/applications", json={"company_name": "Apple"}, headers=headers)
        assert res.status_code == 422

        # Missing company_name
        res = client.post("/api/applications", json={"job_title": "DevOps Engineer"}, headers=headers)
        assert res.status_code == 422

    def test_create_application_invalid_status(self):
        headers = create_test_user_and_auth()
        payload = {
            "company_name": "Meta",
            "job_title": "Frontend Engineer",
            "status": "NON_EXISTENT_STATUS",
        }
        res = client.post("/api/applications", json=payload, headers=headers)
        assert res.status_code == 422

    def test_company_reuse_and_creation(self):
        headers = create_test_user_and_auth()
        unique_co = f"UniqueCorp_{uuid.uuid4().hex[:6]}"

        res1 = client.post("/api/applications", json={
            "company_name": unique_co,
            "job_title": "Role 1",
        }, headers=headers)
        assert res1.status_code == 201
        co_id_1 = res1.json()["company"]["id"]

        # Second application referencing the same company name in lowercase
        res2 = client.post("/api/applications", json={
            "company_name": unique_co.lower(),
            "job_title": "Role 2",
        }, headers=headers)
        assert res2.status_code == 201
        co_id_2 = res2.json()["company"]["id"]

        # Verifies the same company record is reused
        assert co_id_1 == co_id_2


class TestApplicationRead:
    def test_list_applications_empty(self):
        headers = create_test_user_and_auth()
        res = client.get("/api/applications", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert data["items"] == []
        assert data["total"] == 0
        assert data["page"] == 1

    def test_get_application_detail(self):
        headers = create_test_user_and_auth()
        created = client.post("/api/applications", json={
            "company_name": "Stripe",
            "job_title": "Backend Engineer",
            "location": "Dublin / Remote",
            "status": "INTERVIEW",
        }, headers=headers).json()

        app_id = created["id"]
        res = client.get(f"/api/applications/{app_id}", headers=headers)
        assert res.status_code == 200
        assert res.json()["job_title"] == "Backend Engineer"
        assert res.json()["company"]["name"] == "Stripe"

    def test_get_nonexistent_application_404(self):
        headers = create_test_user_and_auth()
        res = client.get("/api/applications/999999", headers=headers)
        assert res.status_code == 404


class TestApplicationUpdate:
    def test_update_application_success(self):
        headers = create_test_user_and_auth()
        created = client.post("/api/applications", json={
            "company_name": "Amazon",
            "job_title": "SDE 1",
            "salary": "2000000",
        }, headers=headers).json()

        app_id = created["id"]
        update_payload = {
            "job_title": "SDE 2",
            "salary": "2800000",
            "location": "Hyderabad",
        }
        res = client.put(f"/api/applications/{app_id}", json=update_payload, headers=headers)
        assert res.status_code == 200
        updated = res.json()
        assert updated["job_title"] == "SDE 2"
        assert updated["salary"] == "2800000"
        assert updated["location"] == "Hyderabad"
        assert updated["company"]["name"] == "Amazon"

    def test_update_nonexistent_application_404(self):
        headers = create_test_user_and_auth()
        res = client.put("/api/applications/999999", json={"job_title": "New Title"}, headers=headers)
        assert res.status_code == 404


class TestApplicationStatusUpdate:
    def test_patch_status_success(self):
        """Test 1: Valid status update (SAVED -> APPLIED)"""
        headers = create_test_user_and_auth()
        created = client.post("/api/applications", json={
            "company_name": "Netflix",
            "job_title": "Senior UI Engineer",
            "status": "SAVED",
        }, headers=headers).json()

        app_id = created["id"]
        res = client.patch(f"/api/applications/{app_id}/status", json={"status": "APPLIED"}, headers=headers)
        assert res.status_code == 200
        assert res.json()["status"] == "APPLIED"

    def test_patch_status_database_persistence(self):
        """Test 2: Database persistence (verify status actually changed upon re-fetch)"""
        headers = create_test_user_and_auth()
        created = client.post("/api/applications", json={
            "company_name": "Oracle",
            "job_title": "Database Engineer",
            "status": "APPLIED",
        }, headers=headers).json()

        app_id = created["id"]
        # Update status to INTERVIEW
        patch_res = client.patch(f"/api/applications/{app_id}/status", json={"status": "INTERVIEW"}, headers=headers)
        assert patch_res.status_code == 200

        # Query database again to ensure persistence
        get_res = client.get(f"/api/applications/{app_id}", headers=headers)
        assert get_res.status_code == 200
        assert get_res.json()["status"] == "INTERVIEW"

    def test_patch_status_invalid_enum(self):
        """Test 3: Invalid status (expect 422)"""
        headers = create_test_user_and_auth()
        created = client.post("/api/applications", json={
            "company_name": "Netflix",
            "job_title": "Senior UI Engineer",
        }, headers=headers).json()

        app_id = created["id"]
        res = client.patch(f"/api/applications/{app_id}/status", json={"status": "INVALID_STATE"}, headers=headers)
        assert res.status_code == 422

    def test_patch_status_unauthenticated(self):
        """Test 4: Unauthenticated request (expect 401)"""
        headers = create_test_user_and_auth()
        created = client.post("/api/applications", json={
            "company_name": "GitHub",
            "job_title": "Platform Engineer",
            "status": "SAVED",
        }, headers=headers).json()

        app_id = created["id"]
        # Make request without Authorization header
        res = client.patch(f"/api/applications/{app_id}/status", json={"status": "APPLIED"})
        assert res.status_code == 401

    def test_patch_status_cross_user(self):
        """Test 5: Cross-user update (User B attempts to patch User A's application -> expect 404)"""
        headers_a = create_test_user_and_auth()
        headers_b = create_test_user_and_auth()

        created_a = client.post("/api/applications", json={
            "company_name": "Confidential A",
            "job_title": "Staff Architect",
            "status": "APPLIED",
        }, headers=headers_a).json()

        app_id_a = created_a["id"]

        # User B attempts to change status of User A's application
        res = client.patch(f"/api/applications/{app_id_a}/status", json={"status": "REJECTED"}, headers=headers_b)
        assert res.status_code == 404

        # Confirm status remains unchanged for User A
        get_res = client.get(f"/api/applications/{app_id_a}", headers=headers_a)
        assert get_res.status_code == 200
        assert get_res.json()["status"] == "APPLIED"

    def test_patch_status_noop(self):
        """Test 6: No-op update (PATCH SAVED -> SAVED -> 200 and no corruption)"""
        headers = create_test_user_and_auth()
        created = client.post("/api/applications", json={
            "company_name": "Spotify",
            "job_title": "Audio Engineer",
            "status": "SAVED",
        }, headers=headers).json()

        app_id = created["id"]
        res = client.patch(f"/api/applications/{app_id}/status", json={"status": "SAVED"}, headers=headers)
        assert res.status_code == 200
        assert res.json()["status"] == "SAVED"

    def test_patch_status_nonexistent_application_404(self):
        headers = create_test_user_and_auth()
        res = client.patch("/api/applications/999999/status", json={"status": "APPLIED"}, headers=headers)
        assert res.status_code == 404


class TestApplicationDelete:
    def test_delete_application_success(self):
        headers = create_test_user_and_auth()
        created = client.post("/api/applications", json={
            "company_name": "Airbnb",
            "job_title": "Infrastructure Engineer",
        }, headers=headers).json()

        app_id = created["id"]
        del_res = client.delete(f"/api/applications/{app_id}", headers=headers)
        assert del_res.status_code == 204

        # Confirm 404 on subsequent get
        get_res = client.get(f"/api/applications/{app_id}", headers=headers)
        assert get_res.status_code == 404

    def test_delete_nonexistent_application_404(self):
        headers = create_test_user_and_auth()
        res = client.delete("/api/applications/999999", headers=headers)
        assert res.status_code == 404


class TestApplicationSearchAndFilter:
    @pytest.fixture(autouse=True)
    def setup_sample_apps(self):
        self.headers = create_test_user_and_auth()
        client.post("/api/applications", json={
            "company_name": "Uber Technologies",
            "job_title": "Senior Python Backend Engineer",
            "location": "Bangalore",
            "status": "APPLIED",
            "applied_date": "2026-09-01",
        }, headers=self.headers)

        client.post("/api/applications", json={
            "company_name": "Salesforce",
            "job_title": "React Frontend Architect",
            "location": "Hyderabad",
            "status": "INTERVIEW",
            "applied_date": "2026-09-10",
        }, headers=self.headers)

        client.post("/api/applications", json={
            "company_name": "Atlassian",
            "job_title": "Full Stack Engineer",
            "location": "Bengaluru Remote",
            "status": "OFFER",
            "applied_date": "2026-09-15",
        }, headers=self.headers)

    def test_search_by_job_title(self):
        res = client.get("/api/applications?search=Python", headers=self.headers)
        assert res.status_code == 200
        items = res.json()["items"]
        assert len(items) == 1
        assert items[0]["job_title"] == "Senior Python Backend Engineer"

    def test_search_by_company(self):
        res = client.get("/api/applications?search=Salesforce", headers=self.headers)
        assert res.status_code == 200
        items = res.json()["items"]
        assert len(items) == 1
        assert items[0]["company"]["name"] == "Salesforce"

    def test_search_by_location(self):
        res = client.get("/api/applications?search=Hyderabad", headers=self.headers)
        assert res.status_code == 200
        items = res.json()["items"]
        assert len(items) == 1
        assert items[0]["location"] == "Hyderabad"

    def test_filter_by_status(self):
        res = client.get("/api/applications?status=INTERVIEW", headers=self.headers)
        assert res.status_code == 200
        items = res.json()["items"]
        assert len(items) == 1
        assert items[0]["status"] == "INTERVIEW"

    def test_filter_by_location(self):
        res = client.get("/api/applications?location=Hyderabad", headers=self.headers)
        assert res.status_code == 200
        items = res.json()["items"]
        assert len(items) == 1
        assert items[0]["location"] == "Hyderabad"


class TestApplicationSortAndPagination:
    def test_pagination_and_sorting(self):
        headers = create_test_user_and_auth()
        for i in range(12):
            client.post("/api/applications", json={
                "company_name": f"BatchCo_{i}",
                "job_title": f"Engineer {i:02d}",
                "applied_date": f"2026-09-{i+1:02d}",
            }, headers=headers)

        # Page 1, size 5
        res_p1 = client.get("/api/applications?page=1&page_size=5&sort_by=applied_date&sort_order=desc", headers=headers)
        assert res_p1.status_code == 200
        p1 = res_p1.json()
        assert len(p1["items"]) == 5
        assert p1["total"] == 12
        assert p1["total_pages"] == 3
        assert p1["page"] == 1
        assert p1["items"][0]["applied_date"] == "2026-09-12"

        # Page 2, size 5
        res_p2 = client.get("/api/applications?page=2&page_size=5&sort_by=applied_date&sort_order=desc", headers=headers)
        assert res_p2.status_code == 200
        p2 = res_p2.json()
        assert len(p2["items"]) == 5
        assert p2["page"] == 2
        assert p2["items"][0]["applied_date"] == "2026-09-07"


class TestCrossUserSecurity:
    def test_cross_user_isolation(self):
        # User A creates Application A
        headers_a = create_test_user_and_auth()
        headers_b = create_test_user_and_auth()

        created_a = client.post("/api/applications", json={
            "company_name": "Confidential A",
            "job_title": "Top Secret Architect",
        }, headers=headers_a).json()

        app_id_a = created_a["id"]

        # User B cannot GET User A's application -> 404
        res_get = client.get(f"/api/applications/{app_id_a}", headers=headers_b)
        assert res_get.status_code == 404

        # User B cannot PUT User A's application -> 404
        res_put = client.put(f"/api/applications/{app_id_a}", json={
            "job_title": "Hacked Title",
        }, headers=headers_b)
        assert res_put.status_code == 404

        # User B cannot PATCH status of User A's application -> 404
        res_patch = client.patch(f"/api/applications/{app_id_a}/status", json={
            "status": "REJECTED",
        }, headers=headers_b)
        assert res_patch.status_code == 404

        # User B cannot DELETE User A's application -> 404
        res_del = client.delete(f"/api/applications/{app_id_a}", headers=headers_b)
        assert res_del.status_code == 404

        # User B's application list does not include User A's application
        res_list = client.get("/api/applications", headers=headers_b)
        assert res_list.status_code == 200
        user_b_ids = [item["id"] for item in res_list.json()["items"]]
        assert app_id_a not in user_b_ids
