# Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 2016-present Scille SAS
from __future__ import annotations

from contextlib import contextmanager
from typing import Type
from unittest.mock import ANY

import attr
import pytest
import trio

from parsec._parsec import BackendEvent, DateTime
from parsec.event_bus import EventBus, MetaEvent
from tests.common import real_clock_timeout


class PartialDict(dict):
    """
    Allow to do partial comparison with a dict::

        assert PartialDict(a=1, b=2) == {'a': 1, 'b': 2, 'c': 3}
    """

    def __repr__(self):
        return f"PartialDict<{super().__repr__()}>"

    def __eq__(self, other):
        for key, expected_value in self.items():
            if key not in other or other[key] != expected_value:
                return False
        return True


class PartialObj:
    """
    Allow to do partial comparison with a object::

        assert PartialObj(Foo, a=1, b=2) == Foo(a=1, b=2, c=3)
    """

    def __init__(self, obj_cls, **kwargs):
        self._obj_cls = obj_cls
        self._obj_kwargs = kwargs

    def __repr__(self):
        args = ", ".join([f"{k}={v!r}" for k, v in self._obj_kwargs.items()])
        return f"PartialObj<{self._obj_cls.__name__}({args})>"

    def __eq__(self, other):
        if type(other) is not self._obj_cls:
            return False
        for key, expected_value in self._obj_kwargs.items():
            if not hasattr(other, key) or getattr(other, key) != expected_value:
                return False
        return True


@attr.s(frozen=True, slots=True, eq=False)
class SpiedEvent:
    event = attr.ib()
    kwargs = attr.ib(factory=dict)
    dt = attr.ib(factory=DateTime.now)

    # When using Rust with pyo3 with some types,
    # unittest.mock.ANY cannot be passed to the binding
    # without implementing some specific magic in the binding
    # itself.
    # Instead, we try to let the ANY class do the comparaison.
    # So, calls that were VlobID.__eq__(self, ANY) (which causes
    # problems because ANY cannot be converted to VlobID) become
    # ANY.__eq__(self, VlobID) instead.
    def __eq__(self, other):
        ret = True

        if other.event is ANY:
            ret &= other.event == self.event
        else:
            ret &= self.event == other.event

        if other.dt is ANY:
            ret &= other.dt == self.dt
        else:
            ret &= self.dt == other.dt

        if other.kwargs is ANY:
            return ret
        elif self.kwargs is ANY:
            return ret

        ret &= len(other.kwargs) == len(self.kwargs)
        ret &= all(k in self.kwargs for k in other.kwargs)

        if not ret:
            return ret

        for k, v in other.kwargs.items():
            if v is ANY:
                ret &= v == self.kwargs[k]
            else:
                ret &= self.kwargs[k] == v

        return ret


@attr.s(repr=False, eq=False)
class EventBusSpy:
    ANY = ANY  # Easier to use than doing an import
    events = attr.ib(factory=list)
    _waiters = attr.ib(factory=set)

    def partial_dict(self, *args, **kwargs):
        return PartialDict(*args, **kwargs)

    def partial_obj(self, obj_cls, **kwargs):
        return PartialObj(obj_cls, **kwargs)

    def __repr__(self):
        return f"<{type(self).__name__}({[e.event for e in self.events]})>"

    def _on_event_cb(self, event, **kwargs):
        cooked_event = SpiedEvent(event, kwargs)
        self.events.append(cooked_event)
        for waiter in self._waiters.copy():
            waiter(cooked_event)

    def clear(self):
        self.events.clear()

    async def wait_with_timeout(self, event, kwargs=ANY, dt=ANY, update_event_func=None):
        async with real_clock_timeout():
            await self.wait(event, kwargs, dt, update_event_func)

    async def wait(self, event, kwargs=ANY, dt=ANY, update_event_func=None):
        if isinstance(event, BackendEvent):
            assert kwargs is ANY  # Ignored value
            expected = SpiedEvent(type(event), {"event_id": ANY, "payload": event}, dt)
        else:
            expected = SpiedEvent(event, kwargs, dt)
        for occurred_event in reversed(self.events):
            if update_event_func:
                occurred_event = update_event_func(occurred_event)
            if expected == occurred_event:
                return occurred_event

        return await self._wait(expected, update_event_func)

    async def _wait(self, cooked_expected_event, update_event_func=None):
        send_channel, receive_channel = trio.open_memory_channel(1)

        def _waiter(cooked_event):
            if update_event_func:
                cooked_event = update_event_func(cooked_event)
            if cooked_expected_event == cooked_event:
                send_channel.send_nowait(cooked_event)
                self._waiters.remove(_waiter)

        self._waiters.add(_waiter)
        return await receive_channel.receive()

    async def wait_multiple_with_timeout(self, events, in_order=True):
        async with real_clock_timeout():
            await self.wait_multiple(events, in_order=in_order)

    async def wait_multiple(self, events, in_order=True):
        expected_events = self._cook_events_params(events)
        try:
            self.assert_events_occurred(expected_events, in_order=in_order)
            return
        except AssertionError:
            pass

        done = trio.Event()

        def _waiter(cooked_event):
            try:
                self.assert_events_occurred(expected_events, in_order=in_order)
                self._waiters.remove(_waiter)
                done.set()
            except AssertionError:
                pass

        self._waiters.add(_waiter)
        await done.wait()

    def _cook_events_params(self, events):
        cooked_events = [self._cook_event_params(event) for event in events]
        return cooked_events

    def _cook_event_params(self, event):
        if isinstance(event, SpiedEvent):
            return event
        elif isinstance(event, BackendEvent):
            return SpiedEvent(type(event), {"event_id": ANY, "payload": event}, ANY)
        elif issubclass(event, BackendEvent):
            return SpiedEvent(event, ANY, ANY)
        elif event is ANY:
            return event
        elif isinstance(event, tuple):
            event = event + (ANY,) * (3 - len(event))
            return SpiedEvent(*event)
        else:
            raise ValueError(
                "event must be provided as `SpiedEvent`, `(<event>, <kwargs>, <dt>)` tuple "
                "or an Enum"
            )

    def assert_event_occurred(self, event, kwargs=ANY, dt=ANY):
        if isinstance(event, BackendEvent):
            assert kwargs is ANY  # Ignored value
            expected = SpiedEvent(type(event), {"event_id": ANY, "payload": event}, dt)
        else:
            expected = SpiedEvent(event, kwargs, dt)
        for occurred in self.events:
            if occurred == expected:
                break
        else:
            raise AssertionError(f"Event {expected} didn't occurred")

    def assert_events_occurred(self, events, in_order=True):
        expected_events = self._cook_events_params(events)
        current_events = self.events
        for event in expected_events:
            assert event in current_events, self.events
            if in_order:
                i = current_events.index(event)
                current_events = current_events[i + 1 :]

    def assert_events_exactly_occurred(self, events):
        events = self._cook_events_params(events)
        filtered = [event for event in self.events if not isinstance(event.event, MetaEvent)]
        assert events == filtered


class SpiedEventBus(EventBus):
    ANY = ANY  # Easier to use than doing an import

    def __init__(self):
        super().__init__()
        self._spies = []
        self._muted_events = set()

    def send(self, event, **kwargs):
        if event in self._muted_events:
            return
        for spy in self._spies:
            spy._on_event_cb(event, **kwargs)
        super().send(event, **kwargs)

    def mute(self, event):
        self._muted_events.add(event)

    def unmute(self, event):
        self._muted_events.discard(event)

    def create_spy(self):
        spy = EventBusSpy()
        self._spies.append(spy)
        return spy

    def destroy_spy(self, spy):
        self._spies.remove(spy)

    @contextmanager
    def listen(self):
        spy = self.create_spy()
        try:
            yield spy

        finally:
            self.destroy_spy(spy)


@pytest.fixture(scope="session")
def event_bus_factory() -> Type[SpiedEventBus]:
    return SpiedEventBus


@pytest.fixture
def event_bus(event_bus_factory):
    return event_bus_factory()
