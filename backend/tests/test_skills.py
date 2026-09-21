import uuid
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def create_test_user_and_auth() -> dict:
    """Helper to register a unique candidate and return Bearer auth headers."""
    email = f"skill_test_{uuid.uuid4().hex[:8]}@example.com"
    password = "TestPassword123"
    reg_res = client.post("/api/auth/register", json={
        "name": "Skill Test Candidate",
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


def create_test_application(headers: dict, title: str = "Full Stack Engineer", company: str = "Acme Corp") -> int:
    """Helper to create a test application."""
    res = client.post("/api/applications", json={
        "company_name": company,
        "job_title": title,
        "status": "INTERVIEW",
    }, headers=headers)
    assert res.status_code == 201
    return res.json()["id"]


def create_test_job_description(headers: dict, application_id: int) -> int:
    """Helper to create a test job description."""
    res = client.post("/api/job-descriptions", json={
        "application_id": application_id,
        "title": "Full Stack Engineer",
        "company_name": "Acme Corp",
        "employment_type": "FULL_TIME",
        "work_arrangement": "HYBRID",
        "description": "Building modern web platforms.",
    }, headers=headers)
    assert res.status_code == 201
    return res.json()["id"]


# =====================================================================
# 1. Skill Catalog Creation & Duplicate Prevention
# =====================================================================

class TestSkillCatalogCreation:
    def test_create_skill_success(self):
        """Scenario 1: Create a skill with valid fields -> 201 Created."""
        headers = create_test_user_and_auth()
        payload = {
            "name": "Python",
            "category": "PROGRAMMING_LANGUAGE",
            "description": "Core language for backend microservices",
            "aliases": "py, python3",
        }
        res = client.post("/api/skills", json=payload, headers=headers)
        assert res.status_code == 201
        data = res.json()
        assert data["name"] == "Python"
        assert data["normalized_name"] == "python"
        assert data["category"] == "PROGRAMMING_LANGUAGE"
        assert data["description"] == "Core language for backend microservices"
        assert data["aliases"] == "py, python3"
        assert data["application_count"] == 0
        assert data["job_description_count"] == 0
        assert "id" in data

    def test_create_duplicate_skill_exact_name(self):
        """Scenario 2: Creating an exact duplicate skill -> 409 Conflict."""
        headers = create_test_user_and_auth()
        client.post("/api/skills", json={"name": "FastAPI", "category": "BACKEND"}, headers=headers)
        res = client.post("/api/skills", json={"name": "FastAPI", "category": "BACKEND"}, headers=headers)
        assert res.status_code == 409
        assert "already exists" in res.json()["detail"].lower()

    def test_create_duplicate_skill_different_casing(self):
        """Scenario 3: Case-insensitive duplicate prevention ('python' vs 'Python') -> 409 Conflict."""
        headers = create_test_user_and_auth()
        client.post("/api/skills", json={"name": "Python", "category": "PROGRAMMING_LANGUAGE"}, headers=headers)
        res = client.post("/api/skills", json={"name": "python", "category": "PROGRAMMING_LANGUAGE"}, headers=headers)
        assert res.status_code == 409
        assert "already exists" in res.json()["detail"].lower()

    def test_create_duplicate_skill_extra_whitespace(self):
        """Scenario 4: Leading/trailing whitespace duplicate prevention (' Docker ' vs 'Docker') -> 409 Conflict."""
        headers = create_test_user_and_auth()
        client.post("/api/skills", json={"name": "Docker", "category": "DEVOPS"}, headers=headers)
        res = client.post("/api/skills", json={"name": "  Docker  ", "category": "DEVOPS"}, headers=headers)
        assert res.status_code == 409

    def test_create_duplicate_skill_multiple_internal_whitespace(self):
        """Scenario 5: Collapsed internal whitespace ('Machine   Learning' vs 'Machine Learning') -> 409 Conflict."""
        headers = create_test_user_and_auth()
        client.post("/api/skills", json={"name": "Machine Learning", "category": "AI_ML"}, headers=headers)
        res = client.post("/api/skills", json={"name": "Machine   Learning", "category": "AI_ML"}, headers=headers)
        assert res.status_code == 409

    def test_create_skill_invalid_category(self):
        """Scenario 6: Invalid category rejected -> 422 Unprocessable Entity."""
        headers = create_test_user_and_auth()
        res = client.post("/api/skills", json={"name": "Rust", "category": "NON_EXISTENT_CAT"}, headers=headers)
        assert res.status_code == 422

    def test_create_skill_empty_name(self):
        """Scenario 7: Empty skill name rejected -> 422."""
        headers = create_test_user_and_auth()
        res = client.post("/api/skills", json={"name": "", "category": "TOOLS"}, headers=headers)
        assert res.status_code == 422

    def test_create_skill_whitespace_only_name(self):
        """Scenario 8: Whitespace-only name rejected -> 422."""
        headers = create_test_user_and_auth()
        res = client.post("/api/skills", json={"name": "   ", "category": "TOOLS"}, headers=headers)
        assert res.status_code == 422


# =====================================================================
# 2. Skill Catalog Read, Query, Pagination & Search
# =====================================================================

class TestSkillCatalogReadAndQuery:
    def test_list_skills_pagination(self):
        """Scenario 9: Pagination returns correct pages and total counts."""
        headers = create_test_user_and_auth()
        for i in range(12):
            client.post("/api/skills", json={"name": f"Skill-{i:02d}", "category": "TOOLS"}, headers=headers)

        res = client.post("/api/skills", json={"name": "Skill-Extra", "category": "TOOLS"}, headers=headers)
        assert res.status_code == 201

        page1 = client.get("/api/skills?page=1&page_size=5", headers=headers)
        assert page1.status_code == 200
        data1 = page1.json()
        assert len(data1["items"]) == 5
        assert data1["page"] == 1
        assert data1["page_size"] == 5
        assert data1["total"] == 13
        assert data1["total_pages"] == 3

    def test_list_skills_filter_by_category(self):
        """Scenario 10: Filtering by category returns only matching records."""
        headers = create_test_user_and_auth()
        client.post("/api/skills", json={"name": "TypeScript", "category": "PROGRAMMING_LANGUAGE"}, headers=headers)
        client.post("/api/skills", json={"name": "AngularJS", "category": "FRONTEND"}, headers=headers)
        client.post("/api/skills", json={"name": "React", "category": "FRONTEND"}, headers=headers)

        res = client.get("/api/skills?category=FRONTEND", headers=headers)
        assert res.status_code == 200
        items = res.json()["items"]
        assert len(items) == 2
        assert all(item["category"] == "FRONTEND" for item in items)

    def test_list_skills_search_by_name(self):
        """Scenario 11: Text search matches skill name."""
        headers = create_test_user_and_auth()
        client.post("/api/skills", json={"name": "PostgreSQL", "category": "DATABASE"}, headers=headers)
        client.post("/api/skills", json={"name": "MySQL", "category": "DATABASE"}, headers=headers)
        client.post("/api/skills", json={"name": "Redis", "category": "DATABASE"}, headers=headers)

        res = client.get("/api/skills?search=postgre", headers=headers)
        assert res.status_code == 200
        items = res.json()["items"]
        assert len(items) == 1
        assert items[0]["name"] == "PostgreSQL"

    def test_list_skills_search_by_alias(self):
        """Scenario 12: Text search matches skill aliases."""
        headers = create_test_user_and_auth()
        client.post(
            "/api/skills",
            json={"name": "Kubernetes", "category": "DEVOPS", "aliases": "k8s, kube"},
            headers=headers,
        )

        res = client.get("/api/skills?search=k8s", headers=headers)
        assert res.status_code == 200
        items = res.json()["items"]
        assert len(items) == 1
        assert items[0]["name"] == "Kubernetes"

    def test_list_skills_sorting(self):
        """Scenario 13: Sorting by name asc and desc."""
        headers = create_test_user_and_auth()
        client.post("/api/skills", json={"name": "Banana Language", "category": "OTHER"}, headers=headers)
        client.post("/api/skills", json={"name": "Apple Framework", "category": "OTHER"}, headers=headers)

        res_asc = client.get("/api/skills?sort_by=name&sort_order=asc", headers=headers)
        names_asc = [x["name"] for x in res_asc.json()["items"]]
        assert names_asc[0] == "Apple Framework"
        assert names_asc[1] == "Banana Language"

        res_desc = client.get("/api/skills?sort_by=name&sort_order=desc", headers=headers)
        names_desc = [x["name"] for x in res_desc.json()["items"]]
        assert names_desc[0] == "Banana Language"
        assert names_desc[1] == "Apple Framework"

    def test_get_skill_by_id(self):
        """Scenario 14: Retrieve single skill by ID."""
        headers = create_test_user_and_auth()
        create_res = client.post(
            "/api/skills",
            json={"name": "GraphQL", "category": "BACKEND", "description": "Query language for APIs"},
            headers=headers,
        )
        skill_id = create_res.json()["id"]

        get_res = client.get(f"/api/skills/{skill_id}", headers=headers)
        assert get_res.status_code == 200
        assert get_res.json()["name"] == "GraphQL"
        assert get_res.json()["category"] == "BACKEND"

    def test_get_nonexistent_skill(self):
        """Scenario 15: Retrieve non-existent skill ID -> 404."""
        headers = create_test_user_and_auth()
        res = client.get("/api/skills/999999", headers=headers)
        assert res.status_code == 404


# =====================================================================
# 3. Skill Catalog Update & Deletion Guard
# =====================================================================

class TestSkillCatalogUpdateAndDelete:
    def test_update_skill_name_success(self):
        """Scenario 16: Update skill name updates name and normalized_name."""
        headers = create_test_user_and_auth()
        create_res = client.post(
            "/api/skills", json={"name": "Vue", "category": "FRONTEND"}, headers=headers
        )
        skill_id = create_res.json()["id"]

        update_res = client.put(
            f"/api/skills/{skill_id}",
            json={"name": "Vue.js", "category": "FRONTEND"},
            headers=headers,
        )
        assert update_res.status_code == 200
        assert update_res.json()["name"] == "Vue.js"
        assert update_res.json()["normalized_name"] == "vue.js"

    def test_update_skill_name_duplicate_conflict(self):
        """Scenario 17: Renaming skill to an existing name -> 409 Conflict."""
        headers = create_test_user_and_auth()
        client.post("/api/skills", json={"name": "AWS", "category": "CLOUD"}, headers=headers)
        res2 = client.post("/api/skills", json={"name": "GCP", "category": "CLOUD"}, headers=headers)
        skill_id = res2.json()["id"]

        rename_res = client.put(f"/api/skills/{skill_id}", json={"name": "aws"}, headers=headers)
        assert rename_res.status_code == 409

    def test_update_skill_category_invalid(self):
        """Scenario 18: Updating to an invalid category -> 422."""
        headers = create_test_user_and_auth()
        create_res = client.post(
            "/api/skills", json={"name": "Java", "category": "PROGRAMMING_LANGUAGE"}, headers=headers
        )
        skill_id = create_res.json()["id"]

        res = client.put(f"/api/skills/{skill_id}", json={"category": "INVALID_CAT"}, headers=headers)
        assert res.status_code == 422

    def test_delete_unused_skill_success(self):
        """Scenario 19: Delete unreferenced skill -> 204 No Content."""
        headers = create_test_user_and_auth()
        create_res = client.post(
            "/api/skills", json={"name": "Perl", "category": "PROGRAMMING_LANGUAGE"}, headers=headers
        )
        skill_id = create_res.json()["id"]

        del_res = client.delete(f"/api/skills/{skill_id}", headers=headers)
        assert del_res.status_code == 204

        get_res = client.get(f"/api/skills/{skill_id}", headers=headers)
        assert get_res.status_code == 404

    def test_delete_skill_linked_to_application_blocked(self):
        """Scenario 20: Deleting a skill referenced by an application -> 409 Conflict."""
        headers = create_test_user_and_auth()
        app_id = create_test_application(headers)
        skill_res = client.post(
            "/api/skills", json={"name": "Django", "category": "BACKEND"}, headers=headers
        )
        skill_id = skill_res.json()["id"]

        # Link to application
        link_res = client.post(
            f"/api/applications/{app_id}/skills",
            json={"skill_id": skill_id, "proficiency": "ADVANCED"},
            headers=headers,
        )
        assert link_res.status_code == 201

        # Attempt to delete skill from catalog
        del_res = client.delete(f"/api/skills/{skill_id}", headers=headers)
        assert del_res.status_code == 409
        assert "linked to 1 application" in del_res.json()["detail"].lower()

    def test_delete_skill_linked_to_job_description_blocked(self):
        """Scenario 21: Deleting a skill referenced by a JD -> 409 Conflict."""
        headers = create_test_user_and_auth()
        app_id = create_test_application(headers)
        jd_id = create_test_job_description(headers, app_id)
        skill_res = client.post(
            "/api/skills", json={"name": "Terraform", "category": "DEVOPS"}, headers=headers
        )
        skill_id = skill_res.json()["id"]

        # Link to JD
        link_res = client.post(
            f"/api/job-descriptions/{jd_id}/skills",
            json={"skill_id": skill_id, "importance": "REQUIRED"},
            headers=headers,
        )
        assert link_res.status_code == 201

        # Attempt to delete skill from catalog
        del_res = client.delete(f"/api/skills/{skill_id}", headers=headers)
        assert del_res.status_code == 409
        assert "linked to" in del_res.json()["detail"].lower()


# =====================================================================
# 4. Application ↔ Skill Mapping
# =====================================================================

class TestApplicationSkillMapping:
    def test_map_skill_to_application_success(self):
        """Scenario 22: Link skill to application with proficiency, years, and primary flag -> 201."""
        headers = create_test_user_and_auth()
        app_id = create_test_application(headers)
        skill_res = client.post(
            "/api/skills", json={"name": "Flask", "category": "BACKEND"}, headers=headers
        )
        skill_id = skill_res.json()["id"]

        res = client.post(
            f"/api/applications/{app_id}/skills",
            json={
                "skill_id": skill_id,
                "proficiency": "EXPERT",
                "years_experience": 4.5,
                "is_primary": True,
            },
            headers=headers,
        )
        assert res.status_code == 201
        data = res.json()
        assert data["application_id"] == app_id
        assert data["skill_id"] == skill_id
        assert data["skill_name"] == "Flask"
        assert data["category"] == "BACKEND"
        assert data["proficiency"] == "EXPERT"
        assert data["years_experience"] == 4.5
        assert data["is_primary"] is True

    def test_map_duplicate_skill_to_application(self):
        """Scenario 23: Mapping duplicate skill to the same application -> 409 Conflict."""
        headers = create_test_user_and_auth()
        app_id = create_test_application(headers)
        skill_res = client.post(
            "/api/skills", json={"name": "SQL", "category": "DATABASE"}, headers=headers
        )
        skill_id = skill_res.json()["id"]

        client.post(f"/api/applications/{app_id}/skills", json={"skill_id": skill_id}, headers=headers)
        dup_res = client.post(f"/api/applications/{app_id}/skills", json={"skill_id": skill_id}, headers=headers)
        assert dup_res.status_code == 409

    def test_map_skill_to_application_invalid_proficiency(self):
        """Scenario 24: Invalid proficiency level -> 422."""
        headers = create_test_user_and_auth()
        app_id = create_test_application(headers)
        skill_res = client.post(
            "/api/skills", json={"name": "Git", "category": "TOOLS"}, headers=headers
        )
        skill_id = skill_res.json()["id"]

        res = client.post(
            f"/api/applications/{app_id}/skills",
            json={"skill_id": skill_id, "proficiency": "SUPER_EXPERT"},
            headers=headers,
        )
        assert res.status_code == 422

    def test_map_skill_to_application_invalid_years(self):
        """Negative years of experience -> 422."""
        headers = create_test_user_and_auth()
        app_id = create_test_application(headers)
        skill_res = client.post(
            "/api/skills", json={"name": "Bash", "category": "TOOLS"}, headers=headers
        )
        skill_id = skill_res.json()["id"]

        res = client.post(
            f"/api/applications/{app_id}/skills",
            json={"skill_id": skill_id, "years_experience": -1.5},
            headers=headers,
        )
        assert res.status_code == 422

    def test_update_application_skill_mapping(self):
        """Scenario 25: Update proficiency, years, and primary flag -> 200."""
        headers = create_test_user_and_auth()
        app_id = create_test_application(headers)
        skill_res = client.post(
            "/api/skills", json={"name": "MongoDB", "category": "DATABASE"}, headers=headers
        )
        skill_id = skill_res.json()["id"]

        client.post(
            f"/api/applications/{app_id}/skills",
            json={"skill_id": skill_id, "proficiency": "BEGINNER", "years_experience": 1.0, "is_primary": False},
            headers=headers,
        )

        update_res = client.put(
            f"/api/applications/{app_id}/skills/{skill_id}",
            json={"proficiency": "ADVANCED", "years_experience": 3.0, "is_primary": True},
            headers=headers,
        )
        assert update_res.status_code == 200
        data = update_res.json()
        assert data["proficiency"] == "ADVANCED"
        assert data["years_experience"] == 3.0
        assert data["is_primary"] is True

    def test_remove_skill_from_application(self):
        """Scenario 26: Remove skill mapping from application -> 204."""
        headers = create_test_user_and_auth()
        app_id = create_test_application(headers)
        skill_res = client.post(
            "/api/skills", json={"name": "Sass", "category": "FRONTEND"}, headers=headers
        )
        skill_id = skill_res.json()["id"]

        client.post(f"/api/applications/{app_id}/skills", json={"skill_id": skill_id}, headers=headers)

        del_res = client.delete(f"/api/applications/{app_id}/skills/{skill_id}", headers=headers)
        assert del_res.status_code == 204

        list_res = client.get(f"/api/applications/{app_id}/skills", headers=headers)
        assert len(list_res.json()) == 0

    def test_application_includes_skills_in_response(self):
        """Verify Application response eagerly returns skill_count, primary_skill_count, and skills list."""
        headers = create_test_user_and_auth()
        app_id = create_test_application(headers)
        s1 = client.post("/api/skills", json={"name": "AngularJS", "category": "FRONTEND"}, headers=headers).json()["id"]
        s2 = client.post("/api/skills", json={"name": "Node.js", "category": "BACKEND"}, headers=headers).json()["id"]

        client.post(f"/api/applications/{app_id}/skills", json={"skill_id": s1, "is_primary": True}, headers=headers)
        client.post(f"/api/applications/{app_id}/skills", json={"skill_id": s2, "is_primary": False}, headers=headers)

        get_app = client.get(f"/api/applications/{app_id}", headers=headers)
        assert get_app.status_code == 200
        app_data = get_app.json()
        assert app_data["skill_count"] == 2
        assert app_data["primary_skill_count"] == 1
        assert len(app_data["skills"]) == 2


# =====================================================================
# 5. Job Description ↔ Skill Mapping
# =====================================================================

class TestJobDescriptionSkillMapping:
    def test_map_skill_to_job_description_success(self):
        """Scenario 27: Map skill to JD with importance and source section -> 201."""
        headers = create_test_user_and_auth()
        app_id = create_test_application(headers)
        jd_id = create_test_job_description(headers, app_id)
        skill_res = client.post(
            "/api/skills", json={"name": "Kubernetes", "category": "DEVOPS"}, headers=headers
        )
        skill_id = skill_res.json()["id"]

        res = client.post(
            f"/api/job-descriptions/{jd_id}/skills",
            json={
                "skill_id": skill_id,
                "importance": "REQUIRED",
                "source_section": "REQUIREMENTS",
            },
            headers=headers,
        )
        assert res.status_code == 201
        data = res.json()
        assert data["job_description_id"] == jd_id
        assert data["skill_id"] == skill_id
        assert data["skill_name"] == "Kubernetes"
        assert data["category"] == "DEVOPS"
        assert data["importance"] == "REQUIRED"
        assert data["source_section"] == "REQUIREMENTS"

    def test_map_duplicate_skill_to_job_description(self):
        """Scenario 28: Mapping duplicate skill to the same JD -> 409 Conflict."""
        headers = create_test_user_and_auth()
        app_id = create_test_application(headers)
        jd_id = create_test_job_description(headers, app_id)
        skill_res = client.post(
            "/api/skills", json={"name": "Golang", "category": "PROGRAMMING_LANGUAGE"}, headers=headers
        )
        skill_id = skill_res.json()["id"]

        client.post(f"/api/job-descriptions/{jd_id}/skills", json={"skill_id": skill_id}, headers=headers)
        dup_res = client.post(f"/api/job-descriptions/{jd_id}/skills", json={"skill_id": skill_id}, headers=headers)
        assert dup_res.status_code == 409

    def test_update_job_description_skill_mapping(self):
        """Scenario 29: Update importance and section for a JD skill -> 200."""
        headers = create_test_user_and_auth()
        app_id = create_test_application(headers)
        jd_id = create_test_job_description(headers, app_id)
        skill_res = client.post(
            "/api/skills", json={"name": "Docker", "category": "DEVOPS"}, headers=headers
        )
        skill_id = skill_res.json()["id"]

        client.post(
            f"/api/job-descriptions/{jd_id}/skills",
            json={"skill_id": skill_id, "importance": "REQUIRED", "source_section": "REQUIREMENTS"},
            headers=headers,
        )

        update_res = client.put(
            f"/api/job-descriptions/{jd_id}/skills/{skill_id}",
            json={"importance": "PREFERRED", "source_section": "QUALIFICATIONS"},
            headers=headers,
        )
        assert update_res.status_code == 200
        data = update_res.json()
        assert data["importance"] == "PREFERRED"
        assert data["source_section"] == "QUALIFICATIONS"

    def test_remove_skill_from_job_description(self):
        """Scenario 30: Remove skill mapping from JD -> 204."""
        headers = create_test_user_and_auth()
        app_id = create_test_application(headers)
        jd_id = create_test_job_description(headers, app_id)
        skill_res = client.post(
            "/api/skills", json={"name": "Tailwind CSS", "category": "FRONTEND"}, headers=headers
        )
        skill_id = skill_res.json()["id"]

        client.post(f"/api/job-descriptions/{jd_id}/skills", json={"skill_id": skill_id}, headers=headers)

        del_res = client.delete(f"/api/job-descriptions/{jd_id}/skills/{skill_id}", headers=headers)
        assert del_res.status_code == 204

        list_res = client.get(f"/api/job-descriptions/{jd_id}/skills", headers=headers)
        assert len(list_res.json()) == 0

    def test_job_description_includes_skills_in_response(self):
        """Verify Job Description response eagerly returns skill_count, required_skill_count, preferred_skill_count, and skills."""
        headers = create_test_user_and_auth()
        app_id = create_test_application(headers)
        jd_id = create_test_job_description(headers, app_id)
        s1 = client.post("/api/skills", json={"name": "Python", "category": "PROGRAMMING_LANGUAGE"}, headers=headers).json()["id"]
        s2 = client.post("/api/skills", json={"name": "Terraform", "category": "DEVOPS"}, headers=headers).json()["id"]

        client.post(f"/api/job-descriptions/{jd_id}/skills", json={"skill_id": s1, "importance": "REQUIRED"}, headers=headers)
        client.post(f"/api/job-descriptions/{jd_id}/skills", json={"skill_id": s2, "importance": "PREFERRED"}, headers=headers)

        get_jd = client.get(f"/api/job-descriptions/{jd_id}", headers=headers)
        assert get_jd.status_code == 200
        jd_data = get_jd.json()
        assert jd_data["skill_count"] == 2
        assert jd_data["required_skill_count"] == 1
        assert jd_data["preferred_skill_count"] == 1
        assert len(jd_data["skills"]) == 2


# =====================================================================
# 6. Skill Stats & Multi-User Security Isolation
# =====================================================================

class TestSkillStatsAndSecurity:
    def test_skill_stats_endpoint(self):
        """Scenario 31: Verify skill statistics calculation."""
        headers = create_test_user_and_auth()
        app_id = create_test_application(headers)
        jd_id = create_test_job_description(headers, app_id)

        s1 = client.post("/api/skills", json={"name": "Skill A", "category": "BACKEND"}, headers=headers).json()["id"]
        s2 = client.post("/api/skills", json={"name": "Skill B", "category": "FRONTEND"}, headers=headers).json()["id"]
        client.post("/api/skills", json={"name": "Skill C", "category": "CLOUD"}, headers=headers)

        client.post(f"/api/applications/{app_id}/skills", json={"skill_id": s1}, headers=headers)
        client.post(f"/api/job-descriptions/{jd_id}/skills", json={"skill_id": s1}, headers=headers)
        client.post(f"/api/applications/{app_id}/skills", json={"skill_id": s2}, headers=headers)

        stats_res = client.get("/api/skills/stats", headers=headers)
        assert stats_res.status_code == 200
        stats = stats_res.json()
        assert stats["total_skills"] == 3
        assert stats["skills_in_applications"] == 2
        assert stats["skills_in_job_descriptions"] == 1
        assert stats["category_counts"]["BACKEND"] == 1
        assert stats["category_counts"]["FRONTEND"] == 1
        assert stats["category_counts"]["CLOUD"] == 1
        assert len(stats["top_used_skills"]) > 0
        assert stats["top_used_skills"][0]["name"] == "Skill A"
        assert stats["top_used_skills"][0]["total_usage"] == 2

    def test_skills_user_isolation(self):
        """Scenario 32: Candidate A's skills and mappings are completely inaccessible and invisible to Candidate B."""
        headers_a = create_test_user_and_auth()
        headers_b = create_test_user_and_auth()

        # User A creates a skill
        skill_a = client.post(
            "/api/skills", json={"name": "Secret Tech", "category": "SECURITY"}, headers=headers_a
        ).json()["id"]

        # User B cannot see it in catalog
        list_b = client.get("/api/skills", headers=headers_b)
        assert not any(x["id"] == skill_a for x in list_b.json()["items"])

        # User B cannot get it directly
        assert client.get(f"/api/skills/{skill_a}", headers=headers_b).status_code == 404

        # User B cannot update it
        assert client.put(f"/api/skills/{skill_a}", json={"name": "Hacked"}, headers=headers_b).status_code == 404

        # User B cannot delete it
        assert client.delete(f"/api/skills/{skill_a}", headers=headers_b).status_code == 404

        # User B cannot link User A's skill to User B's application
        app_b = create_test_application(headers_b)
        link_res = client.post(
            f"/api/applications/{app_b}/skills", json={"skill_id": skill_a}, headers=headers_b
        )
        assert link_res.status_code == 404
