"""`verify_google_id_claims`: the identity the shared trip planner trusts (no LifeOS login involved)."""

import time

import pytest
from app.core.exceptions import UnauthorizedError
from app.modules.auth.google_auth import GoogleIdentity, verify_google_id_claims, verify_google_id_token
from app.tests.google_support import google_token

pytestmark = pytest.mark.usefixtures("fake_google_identity")


@pytest.mark.asyncio
async def test_valid_token_gives_sub_email_and_name():
    identity = await verify_google_id_claims(google_token("Asha@Gmail.com", sub="g-42", name="Asha Rao"))
    assert identity == GoogleIdentity(sub="g-42", email="asha@gmail.com", name="Asha Rao")
    assert await verify_google_id_token(google_token("Asha@Gmail.com")) == "asha@gmail.com"


@pytest.mark.asyncio
async def test_missing_name_falls_back_to_the_email_name():
    assert (await verify_google_id_claims(google_token("ravi.k@gmail.com"))).name == "ravi.k"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "overrides",
    [
        {"aud": "someone-else.apps.googleusercontent.com"},
        {"email_verified": False},
        {"exp": int(time.time()) - 60},
        {"iss": "https://evil.example.com"},
        {"sub": None},
    ],
    ids=["wrong-audience", "unverified-email", "expired", "wrong-issuer", "no-sub"],
)
async def test_bad_tokens_are_rejected(overrides):
    with pytest.raises(UnauthorizedError):
        await verify_google_id_claims(google_token("asha@gmail.com", **overrides))
