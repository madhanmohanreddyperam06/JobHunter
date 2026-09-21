import uuid
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def create_test_user_and_auth() -> dict:
    """Helper to register a unique candidate and return Bearer auth headers."""
    email = f"jd_test_{uuid.uuid4().hex[:8]}@example.com"
    password = "TestPassword123"
    reg_res = client.post("/api/auth/register", json={
        "name": "JD Test User",
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


def create_test_application(headers: dict, title: str = "Software Engineer", company: str = "Tech Corp") -> int:
    """Helper to create a test application."""
    payload = {
        "company_name": company,
        "job_title": title,
        "status": "APPLIED",
    }
    res = client.post("/api/applications", json=payload, headers=headers)
    assert res.status_code == 201
    return res.json()["id"]


class TestJobDescriptionCreation:
    def test_create_job_description_success(self):
        """Scenario 1: Create a job description linked to an existing application -> 201 Created."""
        headers = create_test_user_and_auth()
        app_id = create_test_application(headers, "Backend Engineer", "Stripe")

        payload = {
            "application_id": app_id,
            "title": "Backend Engineer",
            "company_name": "Stripe",
            "job_url": "https://stripe.com/jobs/123",
            "location": "San Francisco, CA",
            "employment_type": "FULL_TIME",
            "work_arrangement": "HYBRID",
            "salary": "$160,000 - $190,000",
            "experience_required": "4+ years",
            "description": "Building scalable payments infrastructure.",
            "responsibilities": "Design distributed microservices and handle millions of transactions.",
            "requirements": "Proficiency in Python, Go, and SQL databases.",
            "qualifications": "B.S. in Computer Science or equivalent experience.",
            "benefits": "Health, 401(k), unlimited PTO, equity.",
        }
        res = client.post("/api/job-descriptions", json=payload, headers=headers)
        assert res.status_code == 201
        data = res.json()
        assert data["id"] is not None
        assert data["application_id"] == app_id
        assert data["title"] == "Backend Engineer"
        assert data["company_name"] == "Stripe"
        assert data["employment_type"] == "FULL_TIME"
        assert data["work_arrangement"] == "HYBRID"

    def test_verify_all_sections_saved(self):
        """Scenario 2: Verify all sections are saved accurately."""
        headers = create_test_user_and_auth()
        app_id = create_test_application(headers, "Data Architect", "Snowflake")

        payload = {
            "application_id": app_id,
            "title": "Data Architect",
            "company_name": "Snowflake",
            "description": "Architect cloud data warehouses.",
            "responsibilities": "Optimize warehouse partitioning and clustering.",
            "requirements": "Deep SQL, distributed storage, metadata layers.",
            "qualifications": "Proven cloud architecture track record.",
            "benefits": "Generous equity grant and wellness stipend.",
        }
        res = client.post("/api/job-descriptions", json=payload, headers=headers)
        assert res.status_code == 201
        data = res.json()
        assert data["description"] == "Architect cloud data warehouses."
        assert data["responsibilities"] == "Optimize warehouse partitioning and clustering."
        assert data["requirements"] == "Deep SQL, distributed storage, metadata layers."
        assert data["qualifications"] == "Proven cloud architecture track record."
        assert data["benefits"] == "Generous equity grant and wellness stipend."

    def test_verify_captured_at_populated(self):
        """Scenario 3: Verify captured_at timestamp is automatically populated."""
        headers = create_test_user_and_auth()
        app_id = create_test_application(headers)

        payload = {
            "application_id": app_id,
            "title": "Platform Engineer",
            "company_name": "Datadog",
        }
        res = client.post("/api/job-descriptions", json=payload, headers=headers)
        assert res.status_code == 201
        data = res.json()
        assert data["captured_at"] is not None
        assert "T" in data["captured_at"]

    def test_verify_employment_type_and_work_arrangement(self):
        """Scenario 4: Verify controlled enums and invalid values rejected."""
        headers = create_test_user_and_auth()
        app_id = create_test_application(headers)

        # Invalid employment_type
        invalid_res = client.post(
            "/api/job-descriptions",
            json={
                "application_id": app_id,
                "title": "Engineer",
                "company_name": "Corp",
                "employment_type": "GIG_WORKER",
            },
            headers=headers,
        )
        assert invalid_res.status_code == 422

        # Invalid work_arrangement
        invalid_res2 = client.post(
            "/api/job-descriptions",
            json={
                "application_id": app_id,
                "title": "Engineer",
                "company_name": "Corp",
                "work_arrangement": "OUTER_SPACE",
            },
            headers=headers,
        )
        assert invalid_res2.status_code == 422

        # Valid controlled types
        valid_res = client.post(
            "/api/job-descriptions",
            json={
                "application_id": app_id,
                "title": "Contractor",
                "company_name": "Corp",
                "employment_type": "CONTRACT",
                "work_arrangement": "REMOTE",
            },
            headers=headers,
        )
        assert valid_res.status_code == 201
        assert valid_res.json()["employment_type"] == "CONTRACT"
        assert valid_res.json()["work_arrangement"] == "REMOTE"

    def test_create_duplicate_jd_for_application_returns_409(self):
        """Scenario 5: Attempt to create a second JD for an application -> 409 Conflict."""
        headers = create_test_user_and_auth()
        app_id = create_test_application(headers)

        res1 = client.post(
            "/api/job-descriptions",
            json={"application_id": app_id, "title": "Dev 1", "company_name": "Corp"},
            headers=headers,
        )
        assert res1.status_code == 201

        # Second attempt
        res2 = client.post(
            "/api/job-descriptions",
            json={"application_id": app_id, "title": "Dev 2", "company_name": "Corp"},
            headers=headers,
        )
        assert res2.status_code == 409
        assert "already linked" in res2.json()["detail"]

    def test_create_jd_nonexistent_application_returns_404(self):
        """Scenario 6: Attempt to link JD to non-existent application -> 404 Not Found."""
        headers = create_test_user_and_auth()
        res = client.post(
            "/api/job-descriptions",
            json={"application_id": 999999, "title": "Dev", "company_name": "Corp"},
            headers=headers,
        )
        assert res.status_code == 404

    def test_create_jd_other_user_application_returns_403_or_404(self):
        """Scenario 7: Attempt to link JD to another user's application -> 403 or 404."""
        user1 = create_test_user_and_auth()
        user2 = create_test_user_and_auth()
        app_id = create_test_application(user1, "Dev", "OwnerCorp")

        # user2 tries to attach JD to user1's app
        res = client.post(
            "/api/job-descriptions",
            json={"application_id": app_id, "title": "Hacker Dev", "company_name": "OwnerCorp"},
            headers=user2,
        )
        assert res.status_code in (403, 404)


class TestJobDescriptionUpdateAndImmutability:
    def test_update_job_description_success(self):
        """Scenario 8: Update an existing JD -> Returns 200 OK with updated values."""
        headers = create_test_user_and_auth()
        app_id = create_test_application(headers)
        created = client.post(
            "/api/job-descriptions",
            json={
                "application_id": app_id,
                "title": "Initial Title",
                "company_name": "Initial Corp",
                "salary": "$100k",
                "requirements": "Initial reqs",
            },
            headers=headers,
        ).json()

        update_payload = {
            "title": "Senior Staff Engineer",
            "salary": "$180,000 - $220,000",
            "requirements": "10+ years experience, Go, Kubernetes",
        }
        res = client.put(f"/api/job-descriptions/{created['id']}", json=update_payload, headers=headers)
        assert res.status_code == 200
        updated = res.json()
        assert updated["title"] == "Senior Staff Engineer"
        assert updated["salary"] == "$180,000 - $220,000"
        assert updated["requirements"] == "10+ years experience, Go, Kubernetes"
        # Unchanged fields preserved
        assert updated["company_name"] == "Initial Corp"

    def test_captured_at_immutable_on_update(self):
        """Scenario 9: Verify captured_at does NOT change after an update."""
        headers = create_test_user_and_auth()
        app_id = create_test_application(headers)
        created = client.post(
            "/api/job-descriptions",
            json={"application_id": app_id, "title": "Engineer", "company_name": "Corp"},
            headers=headers,
        ).json()

        initial_captured_at = created["captured_at"]

        # Attempt to overwrite captured_at via update
        res = client.put(
            f"/api/job-descriptions/{created['id']}",
            json={"title": "Updated Title", "captured_at": "1999-01-01T00:00:00"},
            headers=headers,
        )
        assert res.status_code == 200
        assert res.json()["captured_at"] == initial_captured_at

    def test_update_other_user_jd_returns_404(self):
        """Scenario 10: Attempt to update another user's JD -> 404 Not Found."""
        user1 = create_test_user_and_auth()
        user2 = create_test_user_and_auth()
        app_id = create_test_application(user1)
        created = client.post(
            "/api/job-descriptions",
            json={"application_id": app_id, "title": "Dev", "company_name": "Corp"},
            headers=user1,
        ).json()

        res = client.put(
            f"/api/job-descriptions/{created['id']}",
            json={"title": "Malicious Update"},
            headers=user2,
        )
        assert res.status_code == 404


class TestJobDescriptionReadAndQueries:
    def test_get_jd_by_id(self):
        """Scenario 11: Get JD by ID -> Returns full payload with section data."""
        headers = create_test_user_and_auth()
        app_id = create_test_application(headers)
        created = client.post(
            "/api/job-descriptions",
            json={
                "application_id": app_id,
                "title": "Fullstack Dev",
                "company_name": "Meta",
                "responsibilities": "Develop React and Python services",
            },
            headers=headers,
        ).json()

        res = client.get(f"/api/job-descriptions/{created['id']}", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert data["id"] == created["id"]
        assert data["responsibilities"] == "Develop React and Python services"
        assert data["application"] is not None
        assert data["application"]["id"] == app_id

    def test_get_jd_by_application_id(self):
        """Scenario 12: Get JD by application ID -> Returns correct JD."""
        headers = create_test_user_and_auth()
        app_id = create_test_application(headers)
        created = client.post(
            "/api/job-descriptions",
            json={"application_id": app_id, "title": "ML Engineer", "company_name": "OpenAI"},
            headers=headers,
        ).json()

        res = client.get(f"/api/job-descriptions/by-application/{app_id}", headers=headers)
        assert res.status_code == 200
        assert res.json()["id"] == created["id"]
        assert res.json()["company_name"] == "OpenAI"

    def test_get_jd_other_user_application_returns_404(self):
        """Scenario 13: Get JD for another user's application -> Returns 404."""
        user1 = create_test_user_and_auth()
        user2 = create_test_user_and_auth()
        app_id = create_test_application(user1)
        client.post(
            "/api/job-descriptions",
            json={"application_id": app_id, "title": "Dev", "company_name": "Corp"},
            headers=user1,
        )

        res = client.get(f"/api/job-descriptions/by-application/{app_id}", headers=user2)
        assert res.status_code == 404

    def test_list_jds_pagination(self):
        """Scenario 14: List JDs with pagination -> Returns correct page, total, items."""
        headers = create_test_user_and_auth()
        for i in range(3):
            app_id = create_test_application(headers, f"Role {i}", f"Company {i}")
            client.post(
                "/api/job-descriptions",
                json={"application_id": app_id, "title": f"Role {i}", "company_name": f"Company {i}"},
                headers=headers,
            )

        res = client.get("/api/job-descriptions?page=1&page_size=2", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert len(data["items"]) == 2
        assert data["total"] == 3
        assert data["total_pages"] == 2
        assert data["page"] == 1


class TestJobDescriptionSearchAndFilters:
    def test_search_jds_by_keyword_in_requirements(self):
        """Scenario 15: Search JDs by keyword in requirements -> Returns matching JDs."""
        headers = create_test_user_and_auth()
        app1 = create_test_application(headers, "Role A", "Company A")
        app2 = create_test_application(headers, "Role B", "Company B")

        client.post(
            "/api/job-descriptions",
            json={
                "application_id": app1,
                "title": "Role A",
                "company_name": "Company A",
                "requirements": "Must know Rust and WebAssembly expertly.",
            },
            headers=headers,
        )
        client.post(
            "/api/job-descriptions",
            json={
                "application_id": app2,
                "title": "Role B",
                "company_name": "Company B",
                "requirements": "Standard Java SpringBoot development.",
            },
            headers=headers,
        )

        res = client.get("/api/job-descriptions?search=WebAssembly", headers=headers)
        assert res.status_code == 200
        items = res.json()["items"]
        assert len(items) == 1
        assert items[0]["application_id"] == app1

    def test_search_jds_by_company_name(self):
        """Scenario 16: Search JDs by company name -> Returns matching JDs."""
        headers = create_test_user_and_auth()
        app1 = create_test_application(headers, "Dev", "Anthropic")
        app2 = create_test_application(headers, "Dev", "Google")

        client.post("/api/job-descriptions", json={"application_id": app1, "title": "Dev", "company_name": "Anthropic"}, headers=headers)
        client.post("/api/job-descriptions", json={"application_id": app2, "title": "Dev", "company_name": "Google"}, headers=headers)

        res = client.get("/api/job-descriptions?search=Anthropic", headers=headers)
        assert res.status_code == 200
        items = res.json()["items"]
        assert len(items) == 1
        assert items[0]["company_name"] == "Anthropic"

    def test_filter_jds_by_employment_type(self):
        """Scenario 17: Filter JDs by employment_type -> Returns only matching type."""
        headers = create_test_user_and_auth()
        app1 = create_test_application(headers, "Dev", "Corp1")
        app2 = create_test_application(headers, "Dev", "Corp2")

        client.post("/api/job-descriptions", json={"application_id": app1, "title": "Dev", "company_name": "Corp1", "employment_type": "CONTRACT"}, headers=headers)
        client.post("/api/job-descriptions", json={"application_id": app2, "title": "Dev", "company_name": "Corp2", "employment_type": "FULL_TIME"}, headers=headers)

        res = client.get("/api/job-descriptions?employment_type=CONTRACT", headers=headers)
        assert res.status_code == 200
        items = res.json()["items"]
        assert len(items) == 1
        assert items[0]["employment_type"] == "CONTRACT"

    def test_filter_jds_by_work_arrangement(self):
        """Scenario 18: Filter JDs by work_arrangement -> Returns only matching arrangement."""
        headers = create_test_user_and_auth()
        app1 = create_test_application(headers, "Dev", "Corp1")
        app2 = create_test_application(headers, "Dev", "Corp2")

        client.post("/api/job-descriptions", json={"application_id": app1, "title": "Dev", "company_name": "Corp1", "work_arrangement": "REMOTE"}, headers=headers)
        client.post("/api/job-descriptions", json={"application_id": app2, "title": "Dev", "company_name": "Corp2", "work_arrangement": "ONSITE"}, headers=headers)

        res = client.get("/api/job-descriptions?work_arrangement=REMOTE", headers=headers)
        assert res.status_code == 200
        items = res.json()["items"]
        assert len(items) == 1
        assert items[0]["work_arrangement"] == "REMOTE"


class TestJobDescriptionDeletionAndApplicationPreservation:
    def test_delete_jd_success(self):
        """Scenario 19: Delete a JD -> 204 No Content, verified deleted."""
        headers = create_test_user_and_auth()
        app_id = create_test_application(headers)
        created = client.post(
            "/api/job-descriptions",
            json={"application_id": app_id, "title": "Dev", "company_name": "Corp"},
            headers=headers,
        ).json()

        del_res = client.delete(f"/api/job-descriptions/{created['id']}", headers=headers)
        assert del_res.status_code == 204

        # Verify 404 on subsequent get
        get_res = client.get(f"/api/job-descriptions/{created['id']}", headers=headers)
        assert get_res.status_code == 404

    def test_delete_jd_preserves_application(self):
        """Scenario 20: Verify deleting a JD does NOT delete the associated Application."""
        headers = create_test_user_and_auth()
        app_id = create_test_application(headers, "Lead Architect", "Acme Inc")
        created = client.post(
            "/api/job-descriptions",
            json={"application_id": app_id, "title": "Lead Architect", "company_name": "Acme Inc"},
            headers=headers,
        ).json()

        # Delete JD
        del_res = client.delete(f"/api/job-descriptions/{created['id']}", headers=headers)
        assert del_res.status_code == 204

        # Verify application is still 100% present and intact
        app_res = client.get(f"/api/applications/{app_id}", headers=headers)
        assert app_res.status_code == 200
        app_data = app_res.json()
        assert app_data["id"] == app_id
        assert app_data["job_title"] == "Lead Architect"
        assert app_data["has_job_description"] is False
        assert app_data["job_description_id"] is None

    def test_application_has_job_description_flag(self):
        """Bonus: verify Application model reflects has_job_description and job_description_id."""
        headers = create_test_user_and_auth()
        app_id = create_test_application(headers, "Site Reliability Engineer", "Netflix")

        # Before JD creation
        app_res1 = client.get(f"/api/applications/{app_id}", headers=headers)
        assert app_res1.json()["has_job_description"] is False

        # Create JD
        created = client.post(
            "/api/job-descriptions",
            json={"application_id": app_id, "title": "Site Reliability Engineer", "company_name": "Netflix"},
            headers=headers,
        ).json()

        # After JD creation
        app_res2 = client.get(f"/api/applications/{app_id}", headers=headers)
        assert app_res2.json()["has_job_description"] is True
        assert app_res2.json()["job_description_id"] == created["id"]
