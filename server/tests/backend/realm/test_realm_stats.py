# Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 2016-present Scille SAS
from __future__ import annotations

import pytest

from parsec.api.protocol import (
    BlockID,
    RealmStatsRepNotAllowed,
    RealmStatsRepNotFound,
    RealmStatsRepOk,
    VlobID,
)
from tests.backend.common import block_create, realm_stats, vlob_create

REALM_ID_FAKE = VlobID.from_hex("00000000-0000-0000-0000-000000000001")


@pytest.mark.trio
async def test_realm_stats_ok(alice_ws, realm):
    # Create new data
    await block_create(alice_ws, realm_id=realm, block_id=BlockID.new(), block=b"1234")
    rep = await realm_stats(alice_ws, realm_id=realm)
    assert rep == RealmStatsRepOk(blocks_size=4, vlobs_size=0)

    # Create new metadata
    await vlob_create(alice_ws, realm_id=realm, vlob_id=VlobID.new(), blob=b"1234")
    rep = await realm_stats(alice_ws, realm_id=realm)
    assert rep == RealmStatsRepOk(blocks_size=4, vlobs_size=4)


@pytest.mark.trio
async def test_realm_stats_ko(
    backend_asgi_app, alice_ws, bob_ws, ws_from_other_organization_factory, realm
):
    # test with no access to the realm
    rep = await realm_stats(bob_ws, realm_id=realm)
    assert isinstance(rep, RealmStatsRepNotAllowed)

    # test with non existant realm
    rep = await realm_stats(alice_ws, realm_id=REALM_ID_FAKE)
    # The reason is no longer generated
    assert isinstance(rep, RealmStatsRepNotFound)

    # test with no access to the realm
    rep = await realm_stats(bob_ws, realm_id=realm)
    assert isinstance(rep, RealmStatsRepNotAllowed)

    # test with device_id but wrong organization
    async with ws_from_other_organization_factory(backend_asgi_app) as sock:
        rep = await realm_stats(sock, realm_id=realm)
    # The reason is no longer generated
    assert isinstance(rep, RealmStatsRepNotFound)
