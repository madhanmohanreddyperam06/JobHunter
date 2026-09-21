import uuid
from datetime import datetime, timedelta
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def create_test_user_and_auth() -> dict:
    """Helper to register a unique user and get authentication bearer headers."""
    email = f"task_test_{uuid.uuid4().hex[:8]}@example.com"
    password = "TestPassword123"
    reg_res = client.post("/api/auth/register", json={
        "name": "Task Test User",
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


def create_test_application(headers: dict, company_name: str = "Google", job_title: str = "Frontend Engineer") -> int:
    """Helper to create a test application and return its ID."""
    res = client.post("/api/applications", json={
        "company_name": company_name,
        "job_title": job_title,
        "status": "APPLIED",
    }, headers=headers)
    assert res.status_code == 201
    return res.json()["id"]


class TestTaskCreate:
    def test_create_task_success_with_application(self):
        headers = create_test_user_and_auth()
        app_id = create_test_application(headers, "Amazon", "SDE II")

        due = (datetime.utcnow() + timedelta(days=3)).isoformat()
        payload = {
            "title": "Prepare for Amazon coding assessment",
            "description": "Review dynamic programming and trees on LeetCode.",
            "priority": "HIGH",
            "status": "TODO",
            "due_date": due,
            "application_id": app_id,
        }
        res = client.post("/api/tasks", json=payload, headers=headers)
        assert res.status_code == 201
        data = res.json()
        assert data["id"] is not None
        assert data["title"] == "Prepare for Amazon coding assessment"
        assert data["priority"] == "HIGH"
        assert data["status"] == "TODO"
        assert data["application_id"] == app_id
        assert data["company_name"] == "Amazon"
        assert data["job_title"] == "SDE II"
        assert data["completed_at"] is None
        assert data["is_overdue"] is False

    def test_create_task_general_without_application(self):
        headers = create_test_user_and_auth()
        payload = {
            "title": "Update portfolio and resume PDF",
            "description": "Add latest project achievements.",
            "priority": "MEDIUM",
            "status": "TODO",
        }
        res = client.post("/api/tasks", json=payload, headers=headers)
        assert res.status_code == 201
        data = res.json()
        assert data["application_id"] is None
        assert data["title"] == "Update portfolio and resume PDF"

    def test_create_task_foreign_application_returns_404(self):
        headers_a = create_test_user_and_auth()
        app_id_a = create_test_application(headers_a, "Microsoft", "PM")

        headers_b = create_test_user_and_auth()
        payload = {
            "title": "Hijack Microsoft Task",
            "application_id": app_id_a,
        }
        res = client.post("/api/tasks", json=payload, headers=headers_b)
        assert res.status_code == 404
        assert "not found or access denied" in res.json()["detail"].lower()

    def test_create_task_invalid_status_returns_422(self):
        headers = create_test_user_and_auth()
        payload = {
            "title": "Test Task",
            "status": "NON_EXISTENT_STATUS",
        }
        res = client.post("/api/tasks", json=payload, headers=headers)
        assert res.status_code == 422

    def test_create_task_invalid_priority_returns_422(self):
        headers = create_test_user_and_auth()
        payload = {
            "title": "Test Task",
            "priority": "ULTRA_CRITICAL_INVALID",
        }
        res = client.post("/api/tasks", json=payload, headers=headers)
        assert res.status_code == 422


class TestTaskReadAndUpdate:
    def test_get_task_success(self):
        headers = create_test_user_and_auth()
        app_id = create_test_application(headers, "Stripe", "Backend Eng")

        create_res = client.post("/api/tasks", json={
            "title": "Complete take-home assignment",
            "application_id": app_id,
            "priority": "URGENT",
        }, headers=headers)
        task_id = create_res.json()["id"]

        res = client.get(f"/api/tasks/{task_id}", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert data["id"] == task_id
        assert data["title"] == "Complete take-home assignment"
        assert data["company_name"] == "Stripe"

    def test_update_task_success(self):
        headers = create_test_user_and_auth()
        create_res = client.post("/api/tasks", json={
            "title": "Initial Task",
            "priority": "LOW",
        }, headers=headers)
        task_id = create_res.json()["id"]

        update_payload = {
            "title": "Updated Task Title",
            "priority": "HIGH",
            "description": "Added more details.",
        }
        res = client.put(f"/api/tasks/{task_id}", json=update_payload, headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert data["title"] == "Updated Task Title"
        assert data["priority"] == "HIGH"
        assert data["description"] == "Added more details."

    def test_patch_status_to_completed_sets_completed_at(self):
        headers = create_test_user_and_auth()
        create_res = client.post("/api/tasks", json={
            "title": "Follow up email",
            "status": "TODO",
        }, headers=headers)
        task_id = create_res.json()["id"]
        assert create_res.json()["completed_at"] is None

        # Patch to COMPLETED
        patch_res = client.patch(f"/api/tasks/{task_id}/status", json={"status": "COMPLETED"}, headers=headers)
        assert patch_res.status_code == 200
        data = patch_res.json()
        assert data["status"] == "COMPLETED"
        assert data["completed_at"] is not None

    def test_reopen_task_clears_completed_at(self):
        headers = create_test_user_and_auth()
        create_res = client.post("/api/tasks", json={
            "title": "Follow up email 2",
            "status": "COMPLETED",
        }, headers=headers)
        task_id = create_res.json()["id"]
        assert create_res.json()["completed_at"] is not None

        # Reopen to IN_PROGRESS
        patch_res = client.patch(f"/api/tasks/{task_id}/status", json={"status": "IN_PROGRESS"}, headers=headers)
        assert patch_res.status_code == 200
        data = patch_res.json()
        assert data["status"] == "IN_PROGRESS"
        assert data["completed_at"] is None

    def test_patch_status_invalid_enum_returns_422(self):
        headers = create_test_user_and_auth()
        create_res = client.post("/api/tasks", json={"title": "T1"}, headers=headers)
        task_id = create_res.json()["id"]

        patch_res = client.patch(f"/api/tasks/{task_id}/status", json={"status": "NOT_A_STATUS"}, headers=headers)
        assert patch_res.status_code == 422

    def test_delete_task_success(self):
        headers = create_test_user_and_auth()
        create_res = client.post("/api/tasks", json={"title": "To be deleted"}, headers=headers)
        task_id = create_res.json()["id"]

        del_res = client.delete(f"/api/tasks/{task_id}", headers=headers)
        assert del_res.status_code == 204

        # Confirm 404
        get_res = client.get(f"/api/tasks/{task_id}", headers=headers)
        assert get_res.status_code == 404


class TestTaskCrossUserSecurity:
    def test_get_task_cross_user_returns_404(self):
        headers_a = create_test_user_and_auth()
        task_res = client.post("/api/tasks", json={"title": "User A Private Task"}, headers=headers_a)
        task_id = task_res.json()["id"]

        headers_b = create_test_user_and_auth()
        assert client.get(f"/api/tasks/{task_id}", headers=headers_b).status_code == 404

    def test_update_task_cross_user_returns_404(self):
        headers_a = create_test_user_and_auth()
        task_res = client.post("/api/tasks", json={"title": "User A Private Task"}, headers=headers_a)
        task_id = task_res.json()["id"]

        headers_b = create_test_user_and_auth()
        assert client.put(f"/api/tasks/{task_id}", json={"title": "Hacked"}, headers=headers_b).status_code == 404

    def test_patch_status_cross_user_returns_404(self):
        headers_a = create_test_user_and_auth()
        task_res = client.post("/api/tasks", json={"title": "User A Private Task"}, headers=headers_a)
        task_id = task_res.json()["id"]

        headers_b = create_test_user_and_auth()
        assert client.patch(f"/api/tasks/{task_id}/status", json={"status": "COMPLETED"}, headers=headers_b).status_code == 404

    def test_delete_task_cross_user_returns_404(self):
        headers_a = create_test_user_and_auth()
        task_res = client.post("/api/tasks", json={"title": "User A Private Task"}, headers=headers_a)
        task_id = task_res.json()["id"]

        headers_b = create_test_user_and_auth()
        assert client.delete(f"/api/tasks/{task_id}", headers=headers_b).status_code == 404

    def test_unauthenticated_requests_return_401(self):
        assert client.get("/api/tasks").status_code == 401
        assert client.get("/api/tasks/summary").status_code == 401
        assert client.post("/api/tasks", json={"title": "Test"}).status_code == 401
        assert client.get("/api/tasks/1").status_code == 401
        assert client.put("/api/tasks/1", json={"title": "Test"}).status_code == 401
        assert client.patch("/api/tasks/1/status", json={"status": "COMPLETED"}).status_code == 401
        assert client.delete("/api/tasks/1").status_code == 401


class TestTaskListFiltersAndOverdue:
    def test_list_tasks_search(self):
        headers = create_test_user_and_auth()
        app_id = create_test_application(headers, "Netflix", "Core Infrastructure")
        client.post("/api/tasks", json={
            "title": "Study Chaos Engineering",
            "description": "Simian Army and fault tolerance",
            "application_id": app_id,
        }, headers=headers)

        # Search title
        res1 = client.get("/api/tasks?search=Chaos", headers=headers)
        assert res1.status_code == 200
        assert res1.json()["total"] == 1

        # Search company
        res2 = client.get("/api/tasks?search=Netflix", headers=headers)
        assert res2.status_code == 200
        assert res2.json()["total"] == 1

        # Search non-existent
        res3 = client.get("/api/tasks?search=NonExistentTermXYZ", headers=headers)
        assert res3.status_code == 200
        assert res3.json()["total"] == 0

    def test_list_tasks_filter_by_status_and_priority(self):
        headers = create_test_user_and_auth()
        client.post("/api/tasks", json={"title": "Task 1", "status": "TODO", "priority": "LOW"}, headers=headers)
        client.post("/api/tasks", json={"title": "Task 2", "status": "COMPLETED", "priority": "URGENT"}, headers=headers)

        # Filter status
        res_status = client.get("/api/tasks?status=COMPLETED", headers=headers)
        assert res_status.status_code == 200
        assert res_status.json()["total"] == 1
        assert res_status.json()["items"][0]["title"] == "Task 2"

        # Filter priority
        res_priority = client.get("/api/tasks?priority=URGENT", headers=headers)
        assert res_priority.status_code == 200
        assert res_priority.json()["total"] == 1

    def test_list_tasks_filter_due_overdue(self):
        headers = create_test_user_and_auth()
        past_date = (datetime.utcnow() - timedelta(days=2)).isoformat()
        future_date = (datetime.utcnow() + timedelta(days=5)).isoformat()

        # Overdue task (past due date, incomplete)
        client.post("/api/tasks", json={
            "title": "Overdue Action Item",
            "due_date": past_date,
            "status": "TODO",
        }, headers=headers)

        # Future task
        client.post("/api/tasks", json={
            "title": "Future Action Item",
            "due_date": future_date,
            "status": "TODO",
        }, headers=headers)

        # Overdue filter
        res_overdue = client.get("/api/tasks?due=overdue", headers=headers)
        assert res_overdue.status_code == 200
        assert res_overdue.json()["total"] == 1
        item = res_overdue.json()["items"][0]
        assert item["title"] == "Overdue Action Item"
        assert item["is_overdue"] is True

    def test_list_tasks_pagination(self):
        headers = create_test_user_and_auth()
        for i in range(5):
            client.post("/api/tasks", json={"title": f"Pagination Task {i+1}"}, headers=headers)

        res = client.get("/api/tasks?page=1&page_size=2", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert len(data["items"]) == 2
        assert data["total"] == 5
        assert data["page"] == 1
        assert data["page_size"] == 2
        assert data["total_pages"] == 3

    def test_get_task_summary(self):
        headers = create_test_user_and_auth()
        past_date = (datetime.utcnow() - timedelta(days=2)).isoformat()

        client.post("/api/tasks", json={"title": "Pending Task", "status": "TODO"}, headers=headers)
        client.post("/api/tasks", json={"title": "Completed Task", "status": "COMPLETED"}, headers=headers)
        client.post("/api/tasks", json={"title": "Overdue Task", "status": "TODO", "due_date": past_date}, headers=headers)

        res = client.get("/api/tasks/summary", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert data["total"] == 3
        assert data["pending"] == 2
        assert data["completed"] == 1
        assert data["overdue"] == 1
