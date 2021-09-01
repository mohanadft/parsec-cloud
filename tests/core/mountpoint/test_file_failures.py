# Parsec Cloud (https://parsec.cloud) Copyright (c) AGPLv3 2016-2021 Scille SAS

import os
import sys
import trio
import pytest
from pathlib import Path

from parsec.core.fs import FsPath
from parsec.core.core_events import CoreEvent
from parsec.core.mountpoint.manager import mountpoint_manager_factory

from tests.common import create_shared_workspace


@pytest.mark.mountpoint
@pytest.mark.skipif(sys.platform == "darwin", reason="TODO: Passes on macOS but freezes")
def test_fuse_grow_by_truncate(tmpdir, mountpoint_service):
    mountpoint = mountpoint_service.wpath

    oracle_fd = os.open(tmpdir / f"oracle-test", os.O_RDWR | os.O_CREAT)
    fd = os.open(mountpoint / "bar.txt", os.O_RDWR | os.O_CREAT)

    length = 1
    os.ftruncate(fd, length)
    os.ftruncate(oracle_fd, length)

    size = 1
    data = os.read(fd, size)
    expected_data = os.read(oracle_fd, size)
    assert data == expected_data


@pytest.mark.mountpoint
@pytest.mark.skipif(sys.platform == "darwin", reason="TODO: Passes on macOS but freezes")
def test_empty_read_then_reopen(tmpdir, mountpoint_service):
    mountpoint = mountpoint_service.wpath

    oracle_fd = os.open(tmpdir / f"oracle-test", os.O_RDWR | os.O_CREAT)
    fd = os.open(mountpoint / "bar.txt", os.O_RDWR | os.O_CREAT)

    content = b"\x00"
    expected_ret = os.write(oracle_fd, content)
    ret = os.write(fd, content)
    assert ret == expected_ret

    size = 1
    expected_data = os.read(oracle_fd, size)
    data = os.read(fd, size)
    assert data == expected_data

    size = 0
    expected_data = os.read(oracle_fd, size)
    data = os.read(fd, size)
    assert data == expected_data

    os.close(oracle_fd)
    os.close(fd)
    oracle_fd = os.open(tmpdir / f"oracle-test", os.O_RDWR)
    fd = os.open(mountpoint / "bar.txt", os.O_RDWR)

    size = 1
    expected_data = os.read(oracle_fd, size)
    data = os.read(fd, size)
    assert data == expected_data


@pytest.mark.trio
@pytest.mark.mountpoint
@pytest.mark.skipif(sys.platform == "darwin", reason="TODO : crash on macOS")
async def test_remote_error_event(
    tmpdir, monkeypatch, caplog, running_backend, alice_user_fs, bob_user_fs, monitor
):
    wid = await create_shared_workspace("w1", bob_user_fs, alice_user_fs)

    base_mountpoint = Path(tmpdir / "alice_mountpoint")
    async with mountpoint_manager_factory(
        alice_user_fs, alice_user_fs.event_bus, base_mountpoint, debug=False
    ) as mountpoint_manager:

        await mountpoint_manager.mount_workspace(wid)

        # Create shared data
        bob_w = bob_user_fs.get_workspace(wid)
        await bob_w.touch("/foo.txt")
        await bob_w.write_bytes("/foo.txt", b"hello")
        await bob_w.sync()
        alice_w = alice_user_fs.get_workspace(wid)
        await alice_w.sync()
        # Force manifest cache
        await alice_w.path_id("/")
        await alice_w.path_id("/foo.txt")

        trio_w = trio.Path(mountpoint_manager.get_path_in_mountpoint(wid, FsPath("/")))

        # Offline test

        def _testbed_offline():
            # Accessing workspace data in the backend should end up in remote error
            with alice_user_fs.event_bus.listen() as spy:
                fd = os.open(str(trio_w / "foo.txt"), os.O_RDONLY)
                with pytest.raises(OSError):
                    os.read(fd, 10)
            spy.assert_event_occured(CoreEvent.MOUNTPOINT_REMOTE_ERROR)

            # But should still be able to do local stuff though without remote errors
            with alice_user_fs.event_bus.listen() as spy:
                os.open(str(trio_w / "bar.txt"), os.O_RDWR | os.O_CREAT)
            assert os.listdir(str(trio_w)) == ["bar.txt", "foo.txt"]
            assert CoreEvent.MOUNTPOINT_REMOTE_ERROR not in [e.event for e in spy.events]

        with running_backend.offline():
            await trio.to_thread.run_sync(_testbed_offline)

        # Online test

        def _testbed_online():
            # Finally test unhandled error
            def _crash(*args, **kwargs):
                raise RuntimeError("D'Oh !")

            monkeypatch.setattr(
                "parsec.core.fs.workspacefs.entry_transactions.EntryTransactions.folder_create",
                _crash,
            )
            with alice_user_fs.event_bus.listen() as spy:
                with pytest.raises(OSError):
                    os.mkdir(str(trio_w / "dummy"))
            if sys.platform == "win32":
                expected_log = "[error    ] Unhandled exception in winfsp mountpoint [parsec.core.mountpoint.winfsp_operations]"
            else:
                expected_log = "[error    ] Unhandled exception in fuse mountpoint [parsec.core.mountpoint.fuse_operations]"
            caplog.assert_occured_once(expected_log)
            spy.assert_event_occured(CoreEvent.MOUNTPOINT_UNHANDLED_ERROR)

        await trio.to_thread.run_sync(_testbed_online)
