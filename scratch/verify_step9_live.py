import urllib.request
import urllib.parse
import json
import uuid

API_BASE = "http://localhost:8000/api"
FRONTEND_BASE = "http://localhost:3000"


def make_request(url, method="GET", data=None, headers=None):
    if headers is None:
        headers = {}
    encoded_data = None
    if data is not None:
        encoded_data = json.dumps(data).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=encoded_data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as response:
            resp_body = response.read().decode("utf-8")
            return response.status, json.loads(resp_body) if resp_body else {}
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        try:
            parsed = json.loads(err_body)
        except Exception:
            parsed = err_body
        return e.code, parsed


def run_live_verification():
    print("=== STARTING STEP 9 LIVE VERIFICATION ===")

    # 1. Frontend Asset Reachability
    print("\n1. Testing Frontend Static Assets...")
    assets = [
        "/index.html",
        "/app/views/job-descriptions.html",
        "/app/services/job-description.service.js",
        "/app/controllers/job-descriptions.controller.js",
    ]
    for asset in assets:
        req = urllib.request.Request(FRONTEND_BASE + asset)
        with urllib.request.urlopen(req) as resp:
            assert resp.status == 200, f"Asset {asset} failed with {resp.status}"
            print(f"  [OK] {asset} loaded (200 OK, {len(resp.read())} bytes)")

    # 2. Register & Login Candidate
    print("\n2. Registering & Authenticating Candidate...")
    user_email = f"live_candidate_{uuid.uuid4().hex[:8]}@example.com"
    reg_status, reg_data = make_request(f"{API_BASE}/auth/register", "POST", {
        "name": "Live Verification Candidate",
        "email": user_email,
        "password": "Password123!"
    })
    assert reg_status == 201, f"Registration failed: {reg_data}"

    login_status, login_data = make_request(f"{API_BASE}/auth/login", "POST", {
        "email": user_email,
        "password": "Password123!"
    })
    assert login_status == 200, f"Login failed: {login_data}"
    token = login_data["access_token"]
    auth_headers = {"Authorization": f"Bearer {token}"}
    print(f"  [OK] Registered and authenticated as {user_email}")

    # 3. Create Application
    print("\n3. Creating Job Application...")
    app_status, app_data = make_request(f"{API_BASE}/applications", "POST", {
        "company_name": "Stripe",
        "job_title": "Senior Distributed Systems Engineer",
        "status": "APPLIED",
        "location": "San Francisco, CA / Remote"
    }, auth_headers)
    assert app_status == 201, f"Create application failed: {app_data}"
    app_id = app_data["id"]
    print(f"  [OK] Application created: ID {app_id} - '{app_data['job_title']}'")
    assert app_data["has_job_description"] is False
    assert app_data["job_description_id"] is None
    print("  [OK] has_job_description is initially False")

    # 4. Create Job Description
    print("\n4. Creating Structured Job Description linked 1-to-1...")
    jd_payload = {
        "application_id": app_id,
        "title": "Senior Distributed Systems Engineer",
        "company_name": "Stripe",
        "job_url": "https://stripe.com/jobs/dist-sys-101",
        "location": "San Francisco, CA / Remote",
        "employment_type": "FULL_TIME",
        "work_arrangement": "REMOTE",
        "salary": "$210,000 - $260,000 + Equity",
        "experience_required": "6+ years in distributed backend systems",
        "description": "Join Stripe's Core Infrastructure organization building ultra-reliable transaction settlement systems.",
        "responsibilities": "- Architect high-throughput event processing pipelines.\n- Lead cross-functional disaster recovery drills.\n- Maintain 99.999% availability SLAs.",
        "requirements": "- Expertise with Raft/Paxos consensus algorithms.\n- Deep fluency in Python, Go, and MySQL partitioning.\n- Experience in high-volume banking systems.",
        "qualifications": "- B.S. or M.S. in Computer Science or equivalent.\n- Open-source contributions to distributed databases.",
        "benefits": "- Comprehensive healthcare with 100% premium coverage.\n- 401(k) with 50% match up to IRS limit.\n- Unlimited PTO and $1,500 home office stipend."
    }
    jd_status, jd_data = make_request(f"{API_BASE}/job-descriptions", "POST", jd_payload, auth_headers)
    assert jd_status == 201, f"Create JD failed: {jd_data}"
    jd_id = jd_data["id"]
    captured_at = jd_data["captured_at"]
    print(f"  [OK] Job Description created: ID {jd_id}, captured_at: {captured_at}")
    assert jd_data["application_id"] == app_id
    assert jd_data["employment_type"] == "FULL_TIME"
    assert jd_data["work_arrangement"] == "REMOTE"

    # 5. Verify Application shows JD link
    print("\n5. Verifying Application model reflects linked Job Description...")
    app_get_status, app_get_data = make_request(f"{API_BASE}/applications/{app_id}", "GET", headers=auth_headers)
    assert app_get_status == 200
    assert app_get_data["has_job_description"] is True
    assert app_get_data["job_description_id"] == jd_id
    print(f"  [OK] Application {app_id} correctly reports has_job_description=True, job_description_id={jd_id}")

    # 6. Attempt 1-to-1 Conflict
    print("\n6. Testing 1-to-1 Unique constraint (attempting duplicate JD)...")
    dup_status, dup_data = make_request(f"{API_BASE}/job-descriptions", "POST", {
        "application_id": app_id,
        "title": "Duplicate Role",
        "company_name": "Stripe"
    }, auth_headers)
    assert dup_status == 409, f"Expected 409 Conflict, got {dup_status}: {dup_data}"
    print(f"  [OK] Duplicate creation correctly rejected with 409 Conflict: {dup_data['detail']}")

    # 7. Update Job Description & Immutability Check
    print("\n7. Updating JD and verifying captured_at immutability...")
    upd_status, upd_data = make_request(f"{API_BASE}/job-descriptions/{jd_id}", "PUT", {
        "salary": "$225,000 - $275,000 + Equity",
        "captured_at": "1990-01-01T00:00:00"
    }, auth_headers)
    assert upd_status == 200
    assert upd_data["salary"] == "$225,000 - $275,000 + Equity"
    assert upd_data["captured_at"] == captured_at, "captured_at was modified!"
    print("  [OK] Salary updated successfully; captured_at stayed strictly immutable")

    # 8. Query by Application ID
    print("\n8. Querying JD directly by Application ID...")
    by_app_status, by_app_data = make_request(f"{API_BASE}/job-descriptions/by-application/{app_id}", "GET", headers=auth_headers)
    assert by_app_status == 200
    assert by_app_data["id"] == jd_id
    print(f"  [OK] Found JD {by_app_data['id']} via /job-descriptions/by-application/{app_id}")

    # 9. Search and Filter
    print("\n9. Testing Search and Controlled Filters...")
    search_status, search_data = make_request(f"{API_BASE}/job-descriptions?search=consensus", "GET", headers=auth_headers)
    assert search_status == 200
    assert len(search_data["items"]) == 1
    print("  [OK] Full-text search for 'consensus' found matching JD in requirements section")

    filter_status, filter_data = make_request(f"{API_BASE}/job-descriptions?work_arrangement=REMOTE", "GET", headers=auth_headers)
    assert filter_status == 200
    assert len(filter_data["items"]) == 1
    print("  [OK] Filter by work_arrangement=REMOTE returned 1 matching record")

    filter_none_status, filter_none_data = make_request(f"{API_BASE}/job-descriptions?work_arrangement=ONSITE", "GET", headers=auth_headers)
    assert filter_none_status == 200
    assert len(filter_none_data["items"]) == 0
    print("  [OK] Filter by work_arrangement=ONSITE correctly returned 0 records")

    # 10. Deletion and Application Preservation
    print("\n10. Deleting Job Description and testing Application preservation...")
    del_status, _ = make_request(f"{API_BASE}/job-descriptions/{jd_id}", "DELETE", headers=auth_headers)
    assert del_status == 204
    print(f"  [OK] Deleted JD {jd_id} (204 No Content)")

    # Verify JD is gone
    get_jd_status, _ = make_request(f"{API_BASE}/job-descriptions/{jd_id}", "GET", headers=auth_headers)
    assert get_jd_status == 404
    print("  [OK] Verified JD returns 404 Not Found after deletion")

    # Verify Application is still intact!
    app_check_status, app_check_data = make_request(f"{API_BASE}/applications/{app_id}", "GET", headers=auth_headers)
    assert app_check_status == 200
    assert app_check_data["id"] == app_id
    assert app_check_data["has_job_description"] is False
    assert app_check_data["job_description_id"] is None
    print(f"  [OK] Application {app_id} ('{app_check_data['job_title']}') is completely preserved and active!")

    print("\n=== ALL STEP 9 LIVE VERIFICATION CHECKS PASSED PERFECTLY ===")


if __name__ == "__main__":
    run_live_verification()
