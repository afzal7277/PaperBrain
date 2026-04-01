"""
test_auth.py — Auth module tests.
Tests: hashing, verification, user CRUD, roles, enable/disable.
"""
import pytest


class TestPasswordHashing:
    def test_password_is_hashed(self):
        from auth import _hash_password
        hashed = _hash_password("mypassword")
        assert hashed != "mypassword"
        assert len(hashed) > 20

    def test_correct_password_verifies(self):
        from auth import _hash_password, _verify_password
        hashed = _hash_password("correctpass")
        assert _verify_password("correctpass", hashed) is True

    def test_wrong_password_fails(self):
        from auth import _hash_password, _verify_password
        hashed = _hash_password("correctpass")
        assert _verify_password("wrongpass", hashed) is False

    def test_empty_password_hashes(self):
        from auth import _hash_password, _verify_password
        hashed = _hash_password("")
        assert _verify_password("", hashed) is True
        assert _verify_password("notempty", hashed) is False

    def test_two_hashes_of_same_password_differ(self):
        """bcrypt uses random salt — same password = different hash."""
        from auth import _hash_password
        h1 = _hash_password("samepass")
        h2 = _hash_password("samepass")
        assert h1 != h2


class TestDefaultUsers:
    def test_admin_exists_after_init(self):
        from auth import init_default_users, _load_users
        init_default_users()
        users = _load_users()
        assert "admin" in users

    def test_admin_has_correct_role(self):
        from auth import _load_users
        users = _load_users()
        assert users["admin"]["role"] == "admin"

    def test_admin_has_all_bucket_access(self):
        from auth import _load_users
        users = _load_users()
        assert "*" in users["admin"]["buckets"]

    def test_admin_is_enabled(self):
        from auth import _load_users
        users = _load_users()
        assert users["admin"].get("enabled", True) is True


class TestUserCreation:
    def test_create_user_success(self, temp_user):
        from auth import _load_users
        users = _load_users()
        assert temp_user in users

    def test_created_user_has_correct_role(self, temp_user):
        from auth import _load_users
        users = _load_users()
        assert users[temp_user]["role"] == "user"

    def test_created_user_is_enabled(self, temp_user):
        from auth import _load_users
        users = _load_users()
        assert users[temp_user].get("enabled", True) is True

    def test_duplicate_user_rejected(self, temp_user):
        from auth import create_user
        ok, msg = create_user(temp_user, "anypass", "user", [])
        assert not ok
        assert "already exists" in msg.lower()

    def test_empty_username_rejected(self):
        from auth import create_user
        ok, msg = create_user("", "somepass", "user", [])
        assert not ok

    def test_short_password_rejected(self):
        from auth import create_user, delete_user
        ok, msg = create_user("__shortpw__", "abc", "user", [])
        if ok:
            delete_user("__shortpw__")  # safety cleanup
        assert not ok
        assert "6" in msg  # mentions 6 char minimum


class TestUserDeletion:
    def test_user_deleted_after_fixture(self):
        """Verify fixture cleanup works — user should not exist after test."""
        from auth import create_user, delete_user, _load_users
        create_user("__delete_test__", "pass123", "user", [])
        delete_user("__delete_test__")
        users = _load_users()
        assert "__delete_test__" not in users


class TestUserEnableDisable:
    def test_toggle_disables_user(self, temp_user):
        from auth import toggle_user_enabled, _load_users
        toggle_user_enabled(temp_user)
        users = _load_users()
        assert users[temp_user]["enabled"] is False

    def test_toggle_twice_re_enables(self, temp_user):
        from auth import toggle_user_enabled, _load_users
        toggle_user_enabled(temp_user)
        toggle_user_enabled(temp_user)
        users = _load_users()
        assert users[temp_user]["enabled"] is True


class TestBucketPermissions:
    def test_update_user_buckets(self, temp_user):
        from auth import update_user_buckets, _load_users
        update_user_buckets(temp_user, ["Medical", "Sales"])
        users = _load_users()
        assert users[temp_user]["buckets"] == ["Medical", "Sales"]

    def test_clear_user_buckets(self, temp_user):
        from auth import update_user_buckets, _load_users
        update_user_buckets(temp_user, [])
        users = _load_users()
        assert users[temp_user]["buckets"] == []


class TestPasswordChange:
    def test_change_password_success(self, temp_user):
        from auth import change_password, _load_users, _verify_password
        ok, msg = change_password(temp_user, "newpass123")
        assert ok
        users = _load_users()
        assert _verify_password("newpass123", users[temp_user]["password"])

    def test_change_password_too_short(self, temp_user):
        from auth import change_password
        ok, msg = change_password(temp_user, "abc")
        assert not ok

    def test_change_password_nonexistent_user(self):
        from auth import change_password
        ok, msg = change_password("__nonexistent__", "newpass123")
        assert not ok
