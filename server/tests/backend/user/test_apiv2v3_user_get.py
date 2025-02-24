# Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 2016-present Scille SAS
from __future__ import annotations

import pytest

from parsec._parsec import DateTime, authenticated_cmds
from parsec.api.protocol import (
    UserID,
    UserProfile,
    packb,
)
from parsec.backend.asgi import app_factory
from tests.backend.common import apiv2v3_user_get
from tests.common import customize_fixtures, freeze_time

Trustchain = authenticated_cmds.v3.user_get.Trustchain
UserGetRep = authenticated_cmds.v3.user_get.Rep
UserGetRepOk = authenticated_cmds.v3.user_get.RepOk
UserGetRepNotFound = authenticated_cmds.v3.user_get.RepNotFound
UserGetRepUnknownStatus = authenticated_cmds.v3.user_get.RepUnknownStatus


@pytest.fixture
async def access_testbed(
    backend_factory,
    backend_data_binder_factory,
    backend_authenticated_ws_factory,
    organization_factory,
    local_device_factory,
):
    async with backend_factory(populated=False) as backend:
        binder = backend_data_binder_factory(backend)
        org = organization_factory("IFD")
        device = local_device_factory("Godfrey@dev1", org)
        with freeze_time("2000-01-01"):
            await binder.bind_organization(org, device)

        backend_asgi_app = app_factory(backend)

        async with backend_authenticated_ws_factory(backend_asgi_app, device) as sock:
            yield binder, org, device, sock


@pytest.mark.trio
async def test_api_user_get_ok(access_testbed):
    binder, org, device, sock = access_testbed

    rep = await apiv2v3_user_get(sock, device.user_id)
    assert rep == UserGetRepOk(
        user_certificate=binder.certificates_store.get_user(device),
        revoked_user_certificate=None,
        device_certificates=[binder.certificates_store.get_device(device)],
        trustchain=Trustchain(devices=[], revoked_users=[], users=[]),
    )


@pytest.mark.trio
@customize_fixtures(bob_profile=UserProfile.OUTSIDER)
async def test_api_user_get_outsider_get_redacted_certifs(
    certificates_store, bob_ws, alice, alice2, adam, bob
):
    # Backend populates CoolOrg trustchain this way:
    # <root> --> alice@dev1 --> alice@dev2 --> adam@dev1 --> bob@dev1
    rep = await apiv2v3_user_get(bob_ws, bob.user_id)
    cooked_rep = {
        "user_certificate": certificates_store.translate_certif(rep.user_certificate),
        "revoked_user_certificate": rep.revoked_user_certificate,
        "device_certificates": certificates_store.translate_certifs(rep.device_certificates),
        "trustchain": {
            "users": certificates_store.translate_certifs(rep.trustchain.users),
            "revoked_users": rep.trustchain.revoked_users,
            "devices": certificates_store.translate_certifs(rep.trustchain.devices),
        },
    }
    assert cooked_rep == {
        "user_certificate": "<bob redacted user certif>",
        "revoked_user_certificate": None,
        "device_certificates": ["<bob@dev1 redacted device certif>"],
        "trustchain": {
            "users": ["<adam redacted user certif>", "<alice redacted user certif>"],
            "revoked_users": [],
            "devices": [
                "<adam@dev1 redacted device certif>",
                "<alice@dev1 redacted device certif>",
                "<alice@dev2 redacted device certif>",
            ],
        },
    }


@pytest.mark.trio
async def test_api_user_get_ok_deep_trustchain(
    access_testbed, organization_factory, local_device_factory
):
    binder, org, godfrey1, sock = access_testbed
    certificates_store = binder.certificates_store
    d1 = DateTime(2000, 1, 1)
    d2 = DateTime(2000, 1, 2)

    roger1 = local_device_factory("roger@dev1", org)
    mike1 = local_device_factory("mike@dev1", org)
    mike2 = local_device_factory("mike@dev2", org)
    ph1 = local_device_factory("philippe@dev1", org)
    ph2 = local_device_factory("philippe@dev2", org)

    # <root> --> godfrey@dev1 --> roger@dev1 --> mike@dev1 --> mike@dev2
    #                         --> philippe@dev1 --> philippe@dev2
    with freeze_time(d1):
        await binder.bind_device(roger1, certifier=godfrey1)
        await binder.bind_device(mike1, certifier=roger1)
        await binder.bind_device(ph1, certifier=godfrey1)
        await binder.bind_device(ph2, certifier=ph1)
        await binder.bind_device(mike2, certifier=mike1)

    with freeze_time(d2):
        await binder.bind_revocation(roger1.user_id, certifier=ph1)
        await binder.bind_revocation(mike1.user_id, certifier=ph2)

    rep = await apiv2v3_user_get(sock, mike2.device_id.user_id)
    cooked_rep = {
        "user_certificate": certificates_store.translate_certif(rep.user_certificate),
        "device_certificates": certificates_store.translate_certifs(rep.device_certificates),
        "revoked_user_certificate": certificates_store.translate_certif(
            rep.revoked_user_certificate
        ),
        "trustchain": {
            "devices": certificates_store.translate_certifs(rep.trustchain.devices),
            "users": certificates_store.translate_certifs(rep.trustchain.users),
            "revoked_users": certificates_store.translate_certifs(rep.trustchain.revoked_users),
        },
    }

    assert cooked_rep == {
        "user_certificate": "<mike user certif>",
        "device_certificates": ["<mike@dev1 device certif>", "<mike@dev2 device certif>"],
        "revoked_user_certificate": "<mike revoked user certif>",
        "trustchain": {
            "devices": [
                "<Godfrey@dev1 device certif>",
                "<mike@dev1 device certif>",
                "<philippe@dev1 device certif>",
                "<philippe@dev2 device certif>",
                "<roger@dev1 device certif>",
            ],
            "users": [
                "<Godfrey user certif>",
                "<mike user certif>",
                "<philippe user certif>",
                "<roger user certif>",
            ],
            "revoked_users": ["<mike revoked user certif>", "<roger revoked user certif>"],
        },
    }


@pytest.mark.parametrize("bad_msg", [{"user_id": 42}, {"user_id": None}, {}])
@pytest.mark.trio
async def test_api_user_get_bad_msg(alice_ws, bad_msg):
    await alice_ws.send(packb({"cmd": "user_get", **bad_msg}))
    raw_rep = await alice_ws.receive()
    rep = UserGetRep.load(raw_rep)
    assert isinstance(rep, UserGetRepUnknownStatus)
    assert rep.status == "invalid_msg_format"


@pytest.mark.trio
async def test_api_user_get_not_found(alice_ws, coolorg):
    rep = await apiv2v3_user_get(alice_ws, UserID("dummy"))
    assert isinstance(rep, UserGetRepNotFound)


@pytest.mark.trio
async def test_api_user_get_other_organization(
    backend_asgi_app, alice, ws_from_other_organization_factory
):
    # Organizations should be isolated
    async with ws_from_other_organization_factory(backend_asgi_app) as sock:
        rep = await apiv2v3_user_get(sock, alice.user_id)
        assert isinstance(rep, UserGetRepNotFound)


@pytest.mark.trio
async def test_dump_users(backend, coolorg, alice, alice2, bob, adam):
    users, devices = await backend.user.dump_users(coolorg.organization_id)

    assert {u.user_id for u in users} == {alice.user_id, adam.user_id, bob.user_id}
    assert {d.device_id for d in devices} == {
        alice.device_id,
        alice2.device_id,
        adam.device_id,
        bob.device_id,
    }

    # Deeper check
    for user in users:
        expected_user = await backend.user.get_user(
            organization_id=coolorg.organization_id, user_id=user.user_id
        )
        assert user == expected_user
    for device in devices:
        _, expected_device = await backend.user.get_user_with_device(
            organization_id=coolorg.organization_id, device_id=device.device_id
        )
        assert device == expected_device
