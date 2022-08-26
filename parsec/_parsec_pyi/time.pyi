from typing import Union

class TimeProvider:
    """
    Taking the current time constitutes a side effect, on top of that we want to be able
    to simulate in our tests complex behavior where different Parsec client/server have
    shifting clocks.
    So the solution here is to force the current time to be taken from a non-global object
    (typically each client/server should have it own) that can be independantly mocked.
    """

    def now(self) -> DateTime: ...
    def mock_time(self, time: Union[DateTime, int, None]) -> None: ...

class DateTime:
    """
    A class representing DateTime
    """

    def __init__(
        self, year: int, month: int, day: int, hour: int, minute: int, second: int
    ) -> None: ...
    def __repr__(self) -> str: ...
    def __lt__(self, other: DateTime) -> bool: ...
    def __gt__(self, other: DateTime) -> bool: ...
    def __le__(self, other: DateTime) -> bool: ...
    def __ge__(self, other: DateTime) -> bool: ...
    def __lt__(self, other: DateTime) -> bool: ...
    def __eq__(self, other: DateTime) -> bool: ...
    def __ne__(self, other: DateTime) -> bool: ...
    def __hash__(self) -> int: ...
    def __sub__(self, other: DateTime) -> int: ...
    @property
    def year(self) -> int: ...
    @property
    def month(self) -> int: ...
    @property
    def day(self) -> int: ...
    @property
    def hour(self) -> int: ...
    @property
    def minute(self) -> int: ...
    @property
    def second(self) -> int: ...
    @staticmethod
    def now() -> DateTime: ...
    @staticmethod
    def from_timestamp(ts: float) -> DateTime: ...
    def timestamp(self) -> float: ...
    def add(
        self,
        days: float = 0,
        hours: float = 0,
        minutes: float = 0,
        seconds: float = 0,
        microseconds: float = 0,
    ) -> DateTime: ...
    def subtract(
        self,
        days: float = 0,
        hours: float = 0,
        minutes: float = 0,
        seconds: float = 0,
        microseconds: float = 0,
    ) -> DateTime: ...
    def to_local(self) -> LocalDateTime: ...

class LocalDateTime:
    """
    A class representing LocalDateTime
    """

    def __init__(
        self, year: int, month: int, day: int, hour: int, minute: int, second: int
    ) -> None: ...
    @property
    def year(self) -> int: ...
    @property
    def month(self) -> int: ...
    @property
    def day(self) -> int: ...
    @property
    def hour(self) -> int: ...
    @property
    def minute(self) -> int: ...
    @property
    def second(self) -> int: ...
    @staticmethod
    def from_timestamp(ts: float) -> LocalDateTime: ...
    def timestamp(self) -> float: ...
    def format(self, fmt: str) -> str: ...

def mock_time(time: DateTime | int | None): ...
