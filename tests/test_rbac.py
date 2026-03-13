"""Tests for role-based access control — role gates, ownership, record access."""

from tests.conftest import login_as, make_client, make_contact, make_followup


# ── Role gates ──────────────────────────────────────────────────


class TestRoleGates:
    def test_user_cannot_access_settings(self, client, regular_user):
        login_as(client, regular_user)
        resp = client.get("/settings/")
        assert resp.status_code == 403

    def test_user_cannot_access_users(self, client, regular_user):
        login_as(client, regular_user)
        resp = client.get("/users/")
        assert resp.status_code == 403

    def test_manager_can_access_users(self, client, manager_user):
        login_as(client, manager_user)
        resp = client.get("/users/")
        assert resp.status_code == 200

    def test_manager_cannot_access_settings(self, client, manager_user):
        login_as(client, manager_user)
        resp = client.get("/settings/")
        assert resp.status_code == 403

    def test_admin_can_access_settings(self, client, admin_user):
        login_as(client, admin_user)
        resp = client.get("/settings/")
        assert resp.status_code == 200

    def test_admin_can_access_users(self, client, admin_user):
        login_as(client, admin_user)
        resp = client.get("/users/")
        assert resp.status_code == 200


# ── Ownership filtering ────────────────────────────────────────


class TestOwnershipFiltering:
    def test_user_sees_only_own_clients(self, client, regular_user, other_user):
        login_as(client, regular_user)
        make_client(regular_user, company_name="My Corp")
        make_client(other_user, company_name="Other Corp")

        resp = client.get("/clients/")
        assert b"My Corp" in resp.data
        assert b"Other Corp" not in resp.data

    def test_manager_sees_all_clients(self, client, manager_user, regular_user):
        login_as(client, manager_user)
        make_client(regular_user, company_name="User Corp")
        make_client(manager_user, company_name="Mgr Corp")

        resp = client.get("/clients/")
        assert b"User Corp" in resp.data
        assert b"Mgr Corp" in resp.data


# ── Record access ───────────────────────────────────────────────


class TestRecordAccess:
    def test_user_can_access_own_client(self, client, regular_user):
        login_as(client, regular_user)
        c = make_client(regular_user, company_name="Mine")
        resp = client.get(f"/clients/{c.id}")
        assert resp.status_code == 200

    def test_user_cannot_access_other_client(self, client, regular_user, other_user):
        login_as(client, regular_user)
        c = make_client(other_user, company_name="Not Mine")
        resp = client.get(f"/clients/{c.id}")
        assert resp.status_code == 403

    def test_manager_can_access_any_client(self, client, manager_user, regular_user):
        login_as(client, manager_user)
        c = make_client(regular_user, company_name="User's Corp")
        resp = client.get(f"/clients/{c.id}")
        assert resp.status_code == 200


# ── Edit/delete access ──────────────────────────────────────────


class TestEditDeleteAccess:
    def test_user_cannot_edit_other_client(self, client, regular_user, other_user):
        login_as(client, regular_user)
        c = make_client(other_user, company_name="Foreign Corp")
        resp = client.post(
            f"/clients/{c.id}/edit",
            data={"company_name": "Hacked Corp", "status": "active"},
        )
        assert resp.status_code == 403

    def test_user_cannot_delete_other_client(self, client, regular_user, other_user):
        login_as(client, regular_user)
        c = make_client(other_user, company_name="Victim Corp")
        resp = client.post(f"/clients/{c.id}/delete")
        assert resp.status_code == 403


# ── Reassignment access ────────────────────────────────────────


class TestReassignment:
    def test_user_cannot_reassign(self, client, regular_user, other_user):
        login_as(client, regular_user)
        c = make_client(regular_user, company_name="My Biz")
        resp = client.post(
            f"/clients/{c.id}/reassign",
            json={"target_user_id": other_user.id},
        )
        assert resp.status_code == 403

    def test_manager_can_reassign(self, client, manager_user, regular_user):
        login_as(client, manager_user)
        c = make_client(manager_user, company_name="Reassign Corp")
        resp = client.post(
            f"/clients/{c.id}/reassign",
            json={"target_user_id": regular_user.id},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["ok"] is True

    def test_user_cannot_bulk_reassign(self, client, regular_user, other_user):
        login_as(client, regular_user)
        c = make_client(regular_user, company_name="Bulk Corp")
        resp = client.post(
            "/clients/bulk-reassign",
            json={"ids": [c.id], "target_user_id": other_user.id},
        )
        assert resp.status_code == 403

    def test_manager_can_bulk_reassign(self, client, manager_user, regular_user):
        login_as(client, manager_user)
        c = make_client(manager_user, company_name="Bulk2 Corp")
        resp = client.post(
            "/clients/bulk-reassign",
            json={"ids": [c.id], "target_user_id": regular_user.id},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["ok"] is True

    def test_user_cannot_reassign_followup(self, client, regular_user, other_user):
        login_as(client, regular_user)
        c = make_client(regular_user, company_name="FU Corp")
        fu = make_followup(c, regular_user)
        resp = client.post(
            f"/followups/{fu.id}/reassign",
            json={"target_user_id": other_user.id},
        )
        assert resp.status_code == 403

    def test_user_cannot_reassign_contact(self, client, regular_user, other_user):
        login_as(client, regular_user)
        c = make_client(regular_user, company_name="Ct Corp")
        ct = make_contact(c, regular_user)
        resp = client.post(
            f"/contacts/{ct.id}/reassign",
            json={"target_user_id": other_user.id},
        )
        assert resp.status_code == 403
