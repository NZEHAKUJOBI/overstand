"""
Tests for accounts app: 2FA views, login flow, and AuthenticationService.
"""

import base64
import hashlib
import hmac
import struct
import time

from django.contrib.messages import get_messages
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import User


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_user(email="tester@example.com", password="Str0ng!Pass", **kwargs):
    user = User.objects.create_user(email=email, password=password, **kwargs)
    user.email_verified = True
    user.save(update_fields=["email_verified"])
    return user


def _totp_code(secret_b32: str, t: int | None = None) -> str:
    """Pure-Python HOTP/TOTP for test token generation — no external dependency."""
    padded = secret_b32 + "=" * (-len(secret_b32) % 8)
    key = base64.b32decode(padded, casefold=True)
    counter = (t if t is not None else int(time.time())) // 30
    msg = struct.pack(">Q", counter)
    h = hmac.new(key, msg, hashlib.sha1).digest()
    offset = h[-1] & 0xF
    code = (
        ((h[offset] & 0x7F) << 24)
        | ((h[offset + 1] & 0xFF) << 16)
        | ((h[offset + 2] & 0xFF) << 8)
        | (h[offset + 3] & 0xFF)
    ) % 10**6
    return f"{code:06d}"


def _make_2fa_user(email="tfa@example.com", password="Str0ng!Pass", user_type="ipawas_admin"):
    """Return (user, secret) with 2FA enabled.

    Defaults to ipawas_admin rather than ipa_staff because the profile template
    renders ``{% url 'dashboard:country:overview' user.ipa_profile.member_state.slug %}``
    for ipa_staff users, which raises NoReverseMatch when no IPAUser/MemberState exists
    (as is the case in unit tests that don't set up a full IPA profile).  ipawas_admin
    users hit the safe ``{% url 'dashboard:hq:overview' %}`` branch instead.
    """
    import secrets as sec
    raw = sec.token_bytes(20)
    secret = base64.b32encode(raw).decode("utf-8").rstrip("=")
    user = _make_user(email=email, password=password, user_type=user_type)
    user.two_factor_enabled = True
    user.two_factor_secret = secret
    user.save(update_fields=["two_factor_enabled", "two_factor_secret"])
    return user, secret


# ---------------------------------------------------------------------------
# Setup2FAView tests
# ---------------------------------------------------------------------------

@override_settings(ALLOWED_HOSTS=["*"])
class Setup2FAViewGetTests(TestCase):

    def setUp(self):
        self.user = _make_user()
        self.client.force_login(self.user)
        self.url = reverse("accounts:setup_2fa")

    def test_get_renders_200(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_get_sets_session_secret(self):
        self.client.get(self.url)
        self.assertIn("_2fa_setup_secret", self.client.session)

    def test_get_provides_qr_b64_and_secret_to_template(self):
        response = self.client.get(self.url)
        self.assertIn("qr_b64", response.context)
        self.assertIn("secret", response.context)
        self.assertTrue(response.context["qr_b64"])

    def test_unauthenticated_redirects_to_login(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response["Location"])


@override_settings(ALLOWED_HOSTS=["*"])
class Setup2FAViewPostTests(TestCase):

    def setUp(self):
        self.user = _make_user()
        self.client.force_login(self.user)
        self.url = reverse("accounts:setup_2fa")

    def _get_session_secret(self):
        self.client.get(self.url)
        return self.client.session["_2fa_setup_secret"]

    def test_valid_token_enables_2fa(self):
        secret = self._get_session_secret()
        token = _totp_code(secret)
        response = self.client.post(self.url, {"token": token})
        self.assertRedirects(response, reverse("accounts:profile"), fetch_redirect_response=False)
        self.user.refresh_from_db()
        self.assertTrue(self.user.two_factor_enabled)
        self.assertEqual(self.user.two_factor_secret, secret)

    def test_valid_token_clears_session_secret(self):
        secret = self._get_session_secret()
        token = _totp_code(secret)
        self.client.post(self.url, {"token": token})
        self.assertNotIn("_2fa_setup_secret", self.client.session)

    def test_invalid_token_redirects_back(self):
        self._get_session_secret()
        response = self.client.post(self.url, {"token": "000000"})
        self.assertRedirects(response, self.url, fetch_redirect_response=False)

    def test_invalid_token_does_not_enable_2fa(self):
        self._get_session_secret()
        self.client.post(self.url, {"token": "000000"})
        self.user.refresh_from_db()
        self.assertFalse(self.user.two_factor_enabled)

    def test_invalid_token_shows_error_message(self):
        self._get_session_secret()
        response = self.client.post(self.url, {"token": "000000"}, follow=True)
        msgs = [str(m) for m in get_messages(response.wsgi_request)]
        self.assertTrue(any("invalid" in m.lower() for m in msgs))

    def test_expired_session_shows_error(self):
        # POST without GET — no session secret
        response = self.client.post(self.url, {"token": "123456"}, follow=True)
        msgs = [str(m) for m in get_messages(response.wsgi_request)]
        self.assertTrue(any("expired" in m.lower() for m in msgs))

    def test_success_message_shown(self):
        secret = self._get_session_secret()
        token = _totp_code(secret)
        response = self.client.post(self.url, {"token": token}, follow=True)
        msgs = [str(m) for m in get_messages(response.wsgi_request)]
        self.assertTrue(
            any("two-factor" in m.lower() or "active" in m.lower() for m in msgs)
        )

    def test_unauthenticated_post_redirects_to_login(self):
        self.client.logout()
        response = self.client.post(self.url, {"token": "123456"})
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response["Location"])


# ---------------------------------------------------------------------------
# Disable2FAView tests
# ---------------------------------------------------------------------------

@override_settings(ALLOWED_HOSTS=["*"])
class Disable2FAViewTests(TestCase):

    def setUp(self):
        self.user, self.secret = _make_2fa_user()
        self.client.force_login(self.user)
        self.url = reverse("accounts:disable_2fa")

    def test_valid_token_disables_2fa(self):
        token = _totp_code(self.secret)
        response = self.client.post(self.url, {"token": token})
        self.assertRedirects(response, reverse("accounts:profile"), fetch_redirect_response=False)
        self.user.refresh_from_db()
        self.assertFalse(self.user.two_factor_enabled)
        self.assertEqual(self.user.two_factor_secret, "")

    def test_valid_token_shows_success_message(self):
        token = _totp_code(self.secret)
        response = self.client.post(self.url, {"token": token}, follow=True)
        msgs = [str(m) for m in get_messages(response.wsgi_request)]
        self.assertTrue(any("disabled" in m.lower() for m in msgs))

    def test_invalid_token_keeps_2fa_enabled(self):
        self.client.post(self.url, {"token": "000000"})
        self.user.refresh_from_db()
        self.assertTrue(self.user.two_factor_enabled)

    def test_invalid_token_shows_error_message(self):
        response = self.client.post(self.url, {"token": "000000"}, follow=True)
        msgs = [str(m) for m in get_messages(response.wsgi_request)]
        self.assertTrue(any("invalid" in m.lower() for m in msgs))

    def test_invalid_token_redirects_to_profile(self):
        response = self.client.post(self.url, {"token": "000000"})
        self.assertRedirects(response, reverse("accounts:profile"), fetch_redirect_response=False)

    def test_user_without_2fa_redirected_with_info_message(self):
        user = _make_user(email="no2fa@example.com")
        self.client.force_login(user)
        response = self.client.post(self.url, {"token": "123456"}, follow=True)
        msgs = [str(m) for m in get_messages(response.wsgi_request)]
        self.assertTrue(any("not currently enabled" in m.lower() for m in msgs))

    def test_unauthenticated_redirects_to_login(self):
        self.client.logout()
        response = self.client.post(self.url, {"token": "123456"})
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response["Location"])

    def test_get_not_allowed(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)


# ---------------------------------------------------------------------------
# VerifyTOTPView tests (2FA login flow)
# ---------------------------------------------------------------------------

@override_settings(ALLOWED_HOSTS=["*"], AXES_ENABLED=False)
class VerifyTOTPViewTests(TestCase):

    def setUp(self):
        # 2FA gate only fires for ipawas_admin / ipa_staff users
        self.user, self.secret = _make_2fa_user(
            email="login2fa@example.com", user_type="ipawas_admin"
        )
        self.login_url = reverse("accounts:login")
        self.verify_url = reverse("accounts:verify_totp")

    def _start_login(self):
        self.client.post(
            self.login_url, {"email": "login2fa@example.com", "password": "Str0ng!Pass"}
        )

    def test_verify_totp_without_session_redirects_to_login(self):
        response = self.client.get(self.verify_url)
        self.assertRedirects(response, self.login_url, fetch_redirect_response=False)

    def test_login_with_2fa_redirects_to_verify(self):
        response = self.client.post(
            self.login_url, {"email": "login2fa@example.com", "password": "Str0ng!Pass"}
        )
        self.assertRedirects(response, self.verify_url, fetch_redirect_response=False)

    def test_valid_token_completes_login(self):
        self._start_login()
        token = _totp_code(self.secret)
        response = self.client.post(self.verify_url, {"token": token})
        self.assertEqual(response.status_code, 302)
        self.assertNotIn("verify", response["Location"])

    def test_valid_token_authenticates_user(self):
        self._start_login()
        token = _totp_code(self.secret)
        self.client.post(self.verify_url, {"token": token})
        self.assertIn("_auth_user_id", self.client.session)

    def test_invalid_token_keeps_user_unauthenticated(self):
        self._start_login()
        self.client.post(self.verify_url, {"token": "000000"})
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_invalid_token_shows_error(self):
        self._start_login()
        response = self.client.post(self.verify_url, {"token": "000000"})
        self.assertEqual(response.status_code, 200)
        msgs = [str(m) for m in get_messages(response.wsgi_request)]
        self.assertTrue(any("invalid" in m.lower() for m in msgs))


# ---------------------------------------------------------------------------
# LoginView tests
# ---------------------------------------------------------------------------

@override_settings(ALLOWED_HOSTS=["*"], AXES_ENABLED=False)
class LoginViewTests(TestCase):

    def setUp(self):
        self.url = reverse("accounts:login")

    def test_get_renders_200(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_valid_credentials_no_2fa_logs_in(self):
        _make_user(email="plain@example.com")
        self.client.post(self.url, {"email": "plain@example.com", "password": "Str0ng!Pass"})
        self.assertIn("_auth_user_id", self.client.session)

    def test_valid_no_2fa_redirects_away_from_login(self):
        _make_user(email="plain2@example.com")
        response = self.client.post(
            self.url, {"email": "plain2@example.com", "password": "Str0ng!Pass"}
        )
        self.assertEqual(response.status_code, 302)
        self.assertNotIn("login", response["Location"])

    def test_invalid_password_stays_on_login(self):
        _make_user(email="badpass@example.com")
        response = self.client.post(
            self.url, {"email": "badpass@example.com", "password": "WrongPass"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_inactive_user_cannot_login(self):
        user = _make_user(email="inactive@example.com")
        user.is_active = False
        user.save(update_fields=["is_active"])
        self.client.post(self.url, {"email": "inactive@example.com", "password": "Str0ng!Pass"})
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_authenticated_user_redirected_away_from_login(self):
        user = _make_user(email="already@example.com")
        self.client.force_login(user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)


# ---------------------------------------------------------------------------
# AuthenticationService unit tests
# ---------------------------------------------------------------------------

@override_settings(ALLOWED_HOSTS=["*"])
class AuthenticationServiceTests(TestCase):

    def setUp(self):
        from accounts.services import AuthenticationService
        self.svc = AuthenticationService
        self.user = _make_user()

    def test_change_password_with_correct_current(self):
        success, _ = self.svc.change_password(self.user, "Str0ng!Pass", "NewPass!456")
        self.assertTrue(success)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("NewPass!456"))

    def test_change_password_wrong_current(self):
        success, _ = self.svc.change_password(self.user, "WrongPass", "NewPass!456")
        self.assertFalse(success)

    def test_enable_two_factor_generates_secret(self):
        secret = self.svc.enable_two_factor(self.user)
        self.user.refresh_from_db()
        self.assertTrue(self.user.two_factor_enabled)
        self.assertEqual(self.user.two_factor_secret, secret)
        self.assertTrue(len(secret) > 10)

    def test_enable_two_factor_idempotent(self):
        """Calling enable_two_factor twice returns the same secret."""
        secret1 = self.svc.enable_two_factor(self.user)
        secret2 = self.svc.enable_two_factor(self.user)
        self.assertEqual(secret1, secret2)

    def test_disable_two_factor(self):
        self.user.two_factor_enabled = True
        self.user.two_factor_secret = "SOMEDUMMYSECRET"
        self.user.save(update_fields=["two_factor_enabled", "two_factor_secret"])
        self.svc.disable_two_factor(self.user)
        self.user.refresh_from_db()
        self.assertFalse(self.user.two_factor_enabled)
        self.assertEqual(self.user.two_factor_secret, "")
