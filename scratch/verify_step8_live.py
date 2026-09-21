import urllib.request
import urllib.parse
import json
import uuid
import email.message
import http.client

def make_multipart_body(fields, files):
    boundary = uuid.uuid4().hex
    body = bytearray()
    
    for key, value in fields.items():
        body.extend(f"--{boundary}\r\n".encode('utf-8'))
        body.extend(f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode('utf-8'))
        body.extend(f"{value}\r\n".encode('utf-8'))
        
    for key, (filename, content, content_type) in files.items():
        body.extend(f"--{boundary}\r\n".encode('utf-8'))
        body.extend(f'Content-Disposition: form-data; name="{key}"; filename="{filename}"\r\n'.encode('utf-8'))
        body.extend(f'Content-Type: {content_type}\r\n\r\n'.encode('utf-8'))
        body.extend(content)
        body.extend(b"\r\n")
        
    body.extend(f"--{boundary}--\r\n".encode('utf-8'))
    content_type = f"multipart/form-data; boundary={boundary}"
    return body, content_type


def test_live_step8():
    print("1. Testing frontend server...")
    with urllib.request.urlopen("http://127.0.0.1:3000/index.html") as response:
        html = response.read().decode('utf-8')
        assert "resume.service.js" in html
        assert "resumes.controller.js" in html
        print("Frontend OK! HTML length:", len(html))

    print("2. Testing backend health...")
    with urllib.request.urlopen("http://127.0.0.1:8000/api/health") as response:
        health = json.loads(response.read().decode('utf-8'))
        assert health["status"] == "healthy"
        print("Backend Health OK:", health)

    # 3. User Registration & Login
    uid = uuid.uuid4().hex[:8]
    email_addr = f"candidate_{uid}@example.com"
    password = "TestPassword123!"

    reg_payload = json.dumps({
        "name": f"Candidate {uid}",
        "email": email_addr,
        "password": password
    }).encode('utf-8')

    req_reg = urllib.request.Request(
        "http://127.0.0.1:8000/api/auth/register",
        data=reg_payload,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req_reg) as resp:
        reg_data = json.loads(resp.read().decode('utf-8'))
        print(f"Candidate registered, ID: {reg_data['id']}")

    login_payload = json.dumps({
        "email": email_addr,
        "password": password
    }).encode('utf-8')
    req_login = urllib.request.Request(
        "http://127.0.0.1:8000/api/auth/login",
        data=login_payload,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req_login) as resp:
        token = json.loads(resp.read().decode('utf-8'))["access_token"]
        print("Logged in, token received.")

    auth_headers = {"Authorization": f"Bearer {token}"}

    # 4. Upload PDF Resume (v1)
    pdf_bytes = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\n%%EOF"
    fields = {"name": "Senior Fullstack Engineer CV", "description": "Tailored for principal & staff roles"}
    files = {"file": ("Mohan_Fullstack_v1.pdf", pdf_bytes, "application/pdf")}
    body, ctype = make_multipart_body(fields, files)

    req_upload = urllib.request.Request(
        "http://127.0.0.1:8000/api/resumes",
        data=body,
        headers={**auth_headers, "Content-Type": ctype}
    )
    with urllib.request.urlopen(req_upload) as resp:
        assert resp.status == 201
        v1_res = json.loads(resp.read().decode('utf-8'))
        v1_id = v1_res["id"]
        print(f"Created v1 Resume: ID={v1_id}, name='{v1_res['name']}', ver={v1_res['version']}, active={v1_res['is_active']}")
        assert v1_res["version"] == "1"
        assert v1_res["is_active"] is True

    # 5. Upload New Version (v2)
    docx_bytes = b"PK\x03\x04\x14\x00\x06\x00\x08\x00\x00\x00!\x00dummy-docx-bytes"
    fields2 = {"description": "Updated with AI system architecture"}
    files2 = {"file": ("Mohan_Fullstack_v2.docx", docx_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
    body2, ctype2 = make_multipart_body(fields2, files2)

    req_v2 = urllib.request.Request(
        f"http://127.0.0.1:8000/api/resumes/{v1_id}/versions",
        data=body2,
        headers={**auth_headers, "Content-Type": ctype2}
    )
    with urllib.request.urlopen(req_v2) as resp:
        assert resp.status == 201
        v2_res = json.loads(resp.read().decode('utf-8'))
        v2_id = v2_res["id"]
        print(f"Created v2 Resume: ID={v2_id}, ver={v2_res['version']}, active={v2_res['is_active']}")
        assert v2_res["version"] == "2"
        assert v2_res["is_active"] is False

    # 6. Download Resume v1
    req_dl = urllib.request.Request(
        f"http://127.0.0.1:8000/api/resumes/{v1_id}/download",
        headers=auth_headers
    )
    with urllib.request.urlopen(req_dl) as resp:
        assert resp.status == 200
        dl_content = resp.read()
        assert dl_content == pdf_bytes
        disposition = resp.headers.get("Content-Disposition", "")
        print(f"Download verified! Content length: {len(dl_content)}, disposition: {disposition}")

    # 7. Activate Version 2
    req_act = urllib.request.Request(
        f"http://127.0.0.1:8000/api/resumes/{v2_id}/activate",
        headers=auth_headers,
        method="PATCH"
    )
    with urllib.request.urlopen(req_act) as resp:
        assert resp.status == 200
        act_data = json.loads(resp.read().decode('utf-8'))
        assert act_data["is_active"] is True
        print("Version 2 successfully activated.")

    # Verify v1 is now deactivated
    req_get_v1 = urllib.request.Request(f"http://127.0.0.1:8000/api/resumes/{v1_id}", headers=auth_headers)
    with urllib.request.urlopen(req_get_v1) as resp:
        v1_updated = json.loads(resp.read().decode('utf-8'))
        assert v1_updated["is_active"] is False
        print("Version 1 confirmed deactivated.")

    # 8. Create Application referencing v1
    app_payload = json.dumps({
        "company_name": "OpenAI",
        "job_title": "Staff Software Engineer",
        "status": "APPLIED",
        "resume_id": v1_id
    }).encode('utf-8')
    req_app = urllib.request.Request(
        "http://127.0.0.1:8000/api/applications",
        data=app_payload,
        headers={**auth_headers, "Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req_app) as resp:
        assert resp.status == 201
        app_data = json.loads(resp.read().decode('utf-8'))
        app_id = app_data["id"]
        assert app_data["resume_id"] == v1_id
        print(f"Application created: ID={app_id}, linked resume_id={app_data['resume_id']}")

    # 9. Attempt to delete v1 (should be blocked with 409 Conflict)
    req_del_blocked = urllib.request.Request(
        f"http://127.0.0.1:8000/api/resumes/{v1_id}",
        headers=auth_headers,
        method="DELETE"
    )
    try:
        urllib.request.urlopen(req_del_blocked)
        assert False, "Expected 409 Conflict error!"
    except urllib.error.HTTPError as err:
        assert err.code == 409
        err_body = json.loads(err.read().decode('utf-8'))
        print(f"Deletion blocked as required: 409 Conflict - '{err_body['detail']}'")

    # 10. Reassign application resume_id to None
    app_update_payload = json.dumps({
        "resume_id": None
    }).encode('utf-8')
    req_app_update = urllib.request.Request(
        f"http://127.0.0.1:8000/api/applications/{app_id}",
        data=app_update_payload,
        headers={**auth_headers, "Content-Type": "application/json"},
        method="PUT"
    )
    with urllib.request.urlopen(req_app_update) as resp:
        assert resp.status == 200
        print("Application resume_id reassigned to None.")

    # 11. Delete v1 (now unreferenced, should succeed with 204)
    req_del_success = urllib.request.Request(
        f"http://127.0.0.1:8000/api/resumes/{v1_id}",
        headers=auth_headers,
        method="DELETE"
    )
    with urllib.request.urlopen(req_del_success) as resp:
        assert resp.status == 204
        print("Resume v1 deleted successfully (204 No Content).")

    # Verify v1 is 404
    try:
        urllib.request.urlopen(req_get_v1)
        assert False, "Expected 404 Not Found"
    except urllib.error.HTTPError as err:
        assert err.code == 404
        print("Resume v1 confirmed deleted (404 Not Found).")

    # 12. List remaining resumes
    req_list = urllib.request.Request("http://127.0.0.1:8000/api/resumes", headers=auth_headers)
    with urllib.request.urlopen(req_list) as resp:
        list_data = json.loads(resp.read().decode('utf-8'))
        assert list_data["total"] == 1
        assert list_data["items"][0]["id"] == v2_id
        print(f"Resume library listing verified: 1 resume remaining ({list_data['items'][0]['name']} v2).")

    print("\nALL LIVE END-TO-END VERIFICATION CHECKS PASSED PERFECTLY!")


if __name__ == "__main__":
    test_live_step8()
