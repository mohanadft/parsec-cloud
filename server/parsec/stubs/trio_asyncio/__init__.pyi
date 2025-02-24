# Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 2016-present Scille SAS

from __future__ import annotations

from typing import Awaitable, Callable, TypeVar

_R = TypeVar("_R")

def run(proc: Callable[..., Awaitable[_R]], *args: object, queue_len: int | None = None) -> _R: ...
