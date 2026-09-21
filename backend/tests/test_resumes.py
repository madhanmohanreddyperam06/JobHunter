import io
import os
import uuid
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

DUMMY_PDF_CONTENT = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"
DUMMY_DOCX_CONTENT = b"PK\x03\x04\x14\x00\x06\x00\x08\x00\x00\x00!\x00dummy-docx-binary-content-for-testing"


def create_test_user_and_auth() -> dict:
    """Helper to register a unique candidate and return Bearer auth headers."""
    email = f"resume_test_{uuid.uuid4().hex[:8]}@example.com"
    password = "TestPassword123"
    reg_res = client.post("/api/auth/register", json={
        "name": "Resume Test User",
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


def create_test_application(headers: dict, resume_id: int = None) -> int:
    """Helper to create a test application optionally attached to a resume."""
    payload = {
        "company_name": "Tech Corp",
        "job_title": "Software Engineer",
        "status": "APPLIED",
    }
    if resume_id is not None:
        payload["resume_id"] = resume_id

    res = client.post("/api/applications", json=payload, headers=headers)
    assert res.status_code == 201
    return res.json()["id"]


class TestResumeUploadAndValidation:
    def test_upload_pdf_success(self):
        headers = create_test_user_and_auth()
        files = {
            "file": ("Software_Engineer_Resume.pdf", io.BytesIO(DUMMY_PDF_CONTENT), "application/pdf")
        }
        data = {
            "name": "Software Engineer Resume",
            "description": "Tailored for backend positions",
        }
        res = client.post("/api/resumes", data=data, files=files, headers=headers)
        assert res.status_code == 201
        body = res.json()
        assert body["name"] == "Software Engineer Resume"
        assert body["version"] == "1"
        assert body["file_name"] == "Software_Engineer_Resume.pdf"
        assert body["mime_type"] == "application/pdf"
        assert body["file_size"] == len(DUMMY_PDF_CONTENT)
        assert body["is_active"] is True  # First uploaded resume auto-activates
        assert body["application_count"] == 0

    def test_upload_docx_success(self):
        headers = create_test_user_and_auth()
        files = {
            "file": ("Frontend_Resume.docx", io.BytesIO(DUMMY_DOCX_CONTENT), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        }
        data = {
            "name": "Frontend Developer Resume",
        }
        res = client.post("/api/resumes", data=data, files=files, headers=headers)
        assert res.status_code == 201
        body = res.json()
        assert body["name"] == "Frontend Developer Resume"
        assert body["file_name"] == "Frontend_Resume.docx"
        assert body["version"] == "1"

    def test_upload_unsupported_file_returns_422(self):
        headers = create_test_user_and_auth()
        files = {
            "file": ("malicious_script.exe", io.BytesIO(b"MZ\x90\x00executable"), "application/x-msdownload")
        }
        data = {"name": "Malicious File"}
        res = client.post("/api/resumes", data=data, files=files, headers=headers)
        assert res.status_code == 422
        assert "Unsupported file type" in res.json()["detail"]

    def test_upload_oversized_file_returns_error(self):
        headers = create_test_user_and_auth()
        # 10 MB + 1 KB
        oversized = b"0" * (10 * 1024 * 1024 + 1024)
        files = {
            "file": ("huge_resume.pdf", io.BytesIO(oversized), "application/pdf")
        }
        data = {"name": "Huge Resume"}
        res = client.post("/api/resumes", data=data, files=files, headers=headers)
        assert res.status_code == 413
        assert "File is too large" in res.json()["detail"]


class TestResumeCRUDAndMetadata:
    def test_list_resumes(self):
        headers = create_test_user_and_auth()
        # Upload 2 resumes
        files1 = {"file": ("Resume1.pdf", io.BytesIO(DUMMY_PDF_CONTENT), "application/pdf")}
        client.post("/api/resumes", data={"name": "Resume 1"}, files=files1, headers=headers)

        files2 = {"file": ("Resume2.pdf", io.BytesIO(DUMMY_PDF_CONTENT), "application/pdf")}
        client.post("/api/resumes", data={"name": "Resume 2"}, files=files2, headers=headers)

        res = client.get("/api/resumes", headers=headers)
        assert res.status_code == 200
        body = res.json()
        assert body["total"] == 2
        assert len(body["items"]) == 2

    def test_get_resume_detail(self):
        headers = create_test_user_and_auth()
        files = {"file": ("Fullstack.pdf", io.BytesIO(DUMMY_PDF_CONTENT), "application/pdf")}
        create_res = client.post("/api/resumes", data={"name": "Fullstack CV"}, files=files, headers=headers)
        resume_id = create_res.json()["id"]

        res = client.get(f"/api/resumes/{resume_id}", headers=headers)
        assert res.status_code == 200
        assert res.json()["id"] == resume_id
        assert res.json()["name"] == "Fullstack CV"

    def test_update_resume_metadata(self):
        headers = create_test_user_and_auth()
        files = {"file": ("CV.pdf", io.BytesIO(DUMMY_PDF_CONTENT), "application/pdf")}
        create_res = client.post("/api/resumes", data={"name": "Initial Name"}, files=files, headers=headers)
        resume_id = create_res.json()["id"]

        update_res = client.put(f"/api/resumes/{resume_id}", json={
            "name": "Updated Resume Name",
            "description": "Updated notes",
        }, headers=headers)
        assert update_res.status_code == 200
        body = update_res.json()
        assert body["name"] == "Updated Resume Name"
        assert body["description"] == "Updated notes"
        # Version and files should not be altered
        assert body["version"] == "1"


class TestResumeActivation:
    def test_activate_resume_ensures_single_active(self):
        headers = create_test_user_and_auth()
        # Resume 1 -> Auto-activated
        files1 = {"file": ("CV1.pdf", io.BytesIO(DUMMY_PDF_CONTENT), "application/pdf")}
        res1 = client.post("/api/resumes", data={"name": "CV 1"}, files=files1, headers=headers)
        id1 = res1.json()["id"]
        assert res1.json()["is_active"] is True

        # Resume 2 -> Should not be active
        files2 = {"file": ("CV2.pdf", io.BytesIO(DUMMY_PDF_CONTENT), "application/pdf")}
        res2 = client.post("/api/resumes", data={"name": "CV 2"}, files=files2, headers=headers)
        id2 = res2.json()["id"]
        assert res2.json()["is_active"] is False

        # Activate Resume 2
        act_res = client.patch(f"/api/resumes/{id2}/activate", headers=headers)
        assert act_res.status_code == 200
        assert act_res.json()["is_active"] is True

        # Check Resume 1 is now deactivated
        get_res1 = client.get(f"/api/resumes/{id1}", headers=headers)
        assert get_res1.json()["is_active"] is False


class TestResumeVersioning:
    def test_create_new_version_preserves_old_version(self):
        headers = create_test_user_and_auth()
        # Upload v1
        files1 = {"file": ("Backend_v1.pdf", io.BytesIO(DUMMY_PDF_CONTENT), "application/pdf")}
        res1 = client.post("/api/resumes", data={"name": "Backend Resume"}, files=files1, headers=headers)
        v1_id = res1.json()["id"]
        assert res1.json()["version"] == "1"

        # Upload new version
        files2 = {"file": ("Backend_v2.pdf", io.BytesIO(b"%PDF-1.4 updated v2"), "application/pdf")}
        res2 = client.post(f"/api/resumes/{v1_id}/versions", data={"description": "Added cloud certifications"}, files=files2, headers=headers)
        assert res2.status_code == 201
        v2_id = res2.json()["id"]
        assert res2.json()["version"] == "2"
        assert res2.json()["parent_id"] == v1_id

        # Verify v1 still exists
        get_v1 = client.get(f"/api/resumes/{v1_id}", headers=headers)
        assert get_v1.status_code == 200
        assert get_v1.json()["version"] == "1"

    def test_version_increment_logic(self):
        headers = create_test_user_and_auth()
        files = {"file": ("CV_v1.pdf", io.BytesIO(DUMMY_PDF_CONTENT), "application/pdf")}
        res1 = client.post("/api/resumes", data={"name": "ML Engineer"}, files=files, headers=headers)
        v1_id = res1.json()["id"]
        assert res1.json()["version"] == "1"

        # Version 2
        files2 = {"file": ("CV_v2.pdf", io.BytesIO(DUMMY_PDF_CONTENT), "application/pdf")}
        res2 = client.post(f"/api/resumes/{v1_id}/versions", files=files2, headers=headers)
        v2_id = res2.json()["id"]
        assert res2.json()["version"] == "2"

        # Version 3 uploaded from v2
        files3 = {"file": ("CV_v3.pdf", io.BytesIO(DUMMY_PDF_CONTENT), "application/pdf")}
        res3 = client.post(f"/api/resumes/{v2_id}/versions", files=files3, headers=headers)
        assert res3.json()["version"] == "3"

        # Version 4 uploaded from v1 (points to same root)
        files4 = {"file": ("CV_v4.pdf", io.BytesIO(DUMMY_PDF_CONTENT), "application/pdf")}
        res4 = client.post(f"/api/resumes/{v1_id}/versions", files=files4, headers=headers)
        assert res4.json()["version"] == "4"

    def test_get_versions_list(self):
        headers = create_test_user_and_auth()
        files = {"file": ("Data_v1.pdf", io.BytesIO(DUMMY_PDF_CONTENT), "application/pdf")}
        res1 = client.post("/api/resumes", data={"name": "Data Scientist"}, files=files, headers=headers)
        v1_id = res1.json()["id"]

        files2 = {"file": ("Data_v2.pdf", io.BytesIO(DUMMY_PDF_CONTENT), "application/pdf")}
        client.post(f"/api/resumes/{v1_id}/versions", files=files2, headers=headers)

        v_res = client.get(f"/api/resumes/{v1_id}/versions", headers=headers)
        assert v_res.status_code == 200
        versions = v_res.json()
        assert len(versions) == 2
        assert versions[0]["version"] == "2"
        assert versions[1]["version"] == "1"


class TestResumeDownloadAndDelete:
    def test_download_resume_file(self):
        headers = create_test_user_and_auth()
        unique_content = b"%PDF-1.4 unique download test content " + uuid.uuid4().hex.encode()
        files = {"file": ("DownloadTest.pdf", io.BytesIO(unique_content), "application/pdf")}
        create_res = client.post("/api/resumes", data={"name": "Download Test"}, files=files, headers=headers)
        resume_id = create_res.json()["id"]

        dl_res = client.get(f"/api/resumes/{resume_id}/download", headers=headers)
        assert dl_res.status_code == 200
        assert dl_res.content == unique_content
        assert "attachment" in dl_res.headers.get("content-disposition", "")

    def test_delete_resume_removes_db_and_file(self):
        headers = create_test_user_and_auth()
        files = {"file": ("ToDelete.pdf", io.BytesIO(DUMMY_PDF_CONTENT), "application/pdf")}
        create_res = client.post("/api/resumes", data={"name": "To Delete"}, files=files, headers=headers)
        resume_id = create_res.json()["id"]

        del_res = client.delete(f"/api/resumes/{resume_id}", headers=headers)
        assert del_res.status_code == 204

        # Verify DB record is gone
        get_res = client.get(f"/api/resumes/{resume_id}", headers=headers)
        assert get_res.status_code == 404

    def test_delete_referenced_resume_returns_409(self):
        headers = create_test_user_and_auth()
        files = {"file": ("Linked.pdf", io.BytesIO(DUMMY_PDF_CONTENT), "application/pdf")}
        create_res = client.post("/api/resumes", data={"name": "Linked Resume"}, files=files, headers=headers)
        resume_id = create_res.json()["id"]

        # Create application referencing this resume
        create_test_application(headers, resume_id=resume_id)

        # Attempt to delete referenced resume
        del_res = client.delete(f"/api/resumes/{resume_id}", headers=headers)
        assert del_res.status_code == 409
        assert "currently associated with one or more applications" in del_res.json()["detail"]


class TestResumeSecurityAndCrossUser:
    def test_cross_user_get_resume_returns_404(self):
        headers_a = create_test_user_and_auth()
        headers_b = create_test_user_and_auth()

        files = {"file": ("UserA.pdf", io.BytesIO(DUMMY_PDF_CONTENT), "application/pdf")}
        create_res = client.post("/api/resumes", data={"name": "User A Resume"}, files=files, headers=headers_a)
        resume_id = create_res.json()["id"]

        res = client.get(f"/api/resumes/{resume_id}", headers=headers_b)
        assert res.status_code == 404

    def test_cross_user_download_returns_404(self):
        headers_a = create_test_user_and_auth()
        headers_b = create_test_user_and_auth()

        files = {"file": ("SecretA.pdf", io.BytesIO(DUMMY_PDF_CONTENT), "application/pdf")}
        create_res = client.post("/api/resumes", data={"name": "User A Secret"}, files=files, headers=headers_a)
        resume_id = create_res.json()["id"]

        res = client.get(f"/api/resumes/{resume_id}/download", headers=headers_b)
        assert res.status_code == 404

    def test_cross_user_activate_returns_404(self):
        headers_a = create_test_user_and_auth()
        headers_b = create_test_user_and_auth()

        files = {"file": ("UserA.pdf", io.BytesIO(DUMMY_PDF_CONTENT), "application/pdf")}
        create_res = client.post("/api/resumes", data={"name": "User A Resume"}, files=files, headers=headers_a)
        resume_id = create_res.json()["id"]

        res = client.patch(f"/api/resumes/{resume_id}/activate", headers=headers_b)
        assert res.status_code == 404

    def test_cross_user_delete_returns_404(self):
        headers_a = create_test_user_and_auth()
        headers_b = create_test_user_and_auth()

        files = {"file": ("UserA.pdf", io.BytesIO(DUMMY_PDF_CONTENT), "application/pdf")}
        create_res = client.post("/api/resumes", data={"name": "User A Resume"}, files=files, headers=headers_a)
        resume_id = create_res.json()["id"]

        res = client.delete(f"/api/resumes/{resume_id}", headers=headers_b)
        assert res.status_code == 404

    def test_cross_user_application_assignment_returns_404(self):
        headers_a = create_test_user_and_auth()
        headers_b = create_test_user_and_auth()

        # User A creates a resume
        files = {"file": ("UserA.pdf", io.BytesIO(DUMMY_PDF_CONTENT), "application/pdf")}
        create_res = client.post("/api/resumes", data={"name": "User A Resume"}, files=files, headers=headers_a)
        resume_id = create_res.json()["id"]

        # User B attempts to attach User A's resume to their own application
        app_res = client.post("/api/applications", json={
            "company_name": "Target Corp",
            "job_title": "Senior Dev",
            "status": "APPLIED",
            "resume_id": resume_id,
        }, headers=headers_b)
        assert app_res.status_code == 404
        assert "Resume not found" in app_res.json()["detail"]

    def test_unauthenticated_endpoints_return_401(self):
        assert client.get("/api/resumes").status_code == 401
        assert client.get("/api/resumes/1").status_code == 401
        assert client.post("/api/resumes").status_code == 401
        assert client.put("/api/resumes/1", json={"name": "test"}).status_code == 401
        assert client.patch("/api/resumes/1/activate").status_code == 401
        assert client.delete("/api/resumes/1").status_code == 401
        assert client.get("/api/resumes/1/download").status_code == 401

    def test_list_resumes_pagination(self):
        headers = create_test_user_and_auth()
        for i in range(3):
            files = {"file": (f"PageResume_{i}.pdf", io.BytesIO(DUMMY_PDF_CONTENT), "application/pdf")}
            client.post("/api/resumes", data={"name": f"Page Resume {i}"}, files=files, headers=headers)

        res = client.get("/api/resumes?page=1&page_size=2", headers=headers)
        assert res.status_code == 200
        body = res.json()
        assert body["total"] == 3
        assert body["page"] == 1
        assert body["page_size"] == 2
        assert body["total_pages"] == 2
        assert len(body["items"]) == 2
