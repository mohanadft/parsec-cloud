# Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 2016-present Scille SAS

from __future__ import annotations

from . import (
    invite_1_claimer_wait_peer,
    invite_2a_claimer_send_hashed_nonce,
    invite_2b_claimer_send_nonce,
    invite_3a_claimer_signify_trust,
    invite_3b_claimer_wait_peer_trust,
    invite_4_claimer_communicate,
    invite_info,
    ping,
)

class AnyCmdReq:
    @classmethod
    def load(
        cls, raw: bytes
    ) -> (
        invite_1_claimer_wait_peer.Req
        | invite_2a_claimer_send_hashed_nonce.Req
        | invite_2b_claimer_send_nonce.Req
        | invite_3a_claimer_signify_trust.Req
        | invite_3b_claimer_wait_peer_trust.Req
        | invite_4_claimer_communicate.Req
        | invite_info.Req
        | ping.Req
    ): ...

__all__ = [
    "AnyCmdReq",
    "invite_1_claimer_wait_peer",
    "invite_2a_claimer_send_hashed_nonce",
    "invite_2b_claimer_send_nonce",
    "invite_3a_claimer_signify_trust",
    "invite_3b_claimer_wait_peer_trust",
    "invite_4_claimer_communicate",
    "invite_info",
    "ping",
]
