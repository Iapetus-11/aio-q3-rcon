from __future__ import annotations

import asyncio
import logging
import time
import typing as t

import asyncio_dgram

from .errors import IncorrectPasswordError, RCONError

T = t.TypeVar("T")


class Client:
    def __init__(
        self,
        host: str,
        port: int = 27960,
        password: str = "secret",
        *,
        timeout: float = 2.0,
        fragment_read_timeout: float = 0.25,
        retries: int = 2,
        logger: logging.Logger | None = None,
    ):
        self.host = host
        self.port = port

        self.password = password

        self.timeout = timeout
        self.fragment_read_timeout = fragment_read_timeout
        self.retries = retries

        self.logger = logger or logging.getLogger("quake3-rcon")
        if logger is None:
            self.logger.disabled = True

        self._dgram: asyncio_dgram.DatagramClient | None = None

    async def __aenter__(self) -> Client:
        await self.connect()
        return self

    async def __aexit__(
        self, exc_type: t.Type[Exception], exc_val: Exception, exc_tb: t.Any
    ) -> None:
        await self.close()

        if exc_val:
            raise exc_val

    def _get_dgram(self) -> asyncio_dgram.DatagramClient:
        if self._dgram is None:
            raise RuntimeError("Connection not yet established")

        return self._dgram

    async def _retry(self, call: t.Callable[[], t.Coroutine[t.Any, t.Any, T]]) -> T | None:
        exc: Exception | None = None

        for _ in range(self.retries):
            try:
                self.logger.debug("Calling %s with retry logic", call)

                return await call()
            except Exception as e:
                self.logger.debug(
                    "The call to %s failed and it may be retried", call, exc_info=True
                )

                if exc is not None:
                    exc = e

        if exc is not None:
            raise exc

        return None

    async def connect(self, verify: bool = True) -> None:
        """
        Connects to the remote server.

        If verify is True, this attempts to verify if the server is indeed a working Quake 3 server by using
        the heartbeat command
        """

        self.logger.debug("Connecting to %s:%s", self.host, self.port)

        self._dgram = await self._retry(
            lambda: asyncio.wait_for(asyncio_dgram.connect((self.host, self.port)), self.timeout)
        )

        if verify and not (await self.send_command("heartbeat")).startswith("print\n"):
            raise RCONError("Invalid / unsupported server")

    async def close(self) -> None:
        """Closes the connection between the server and client."""

        self.logger.debug("Closing")

        if self._dgram is None:
            return

        try:
            self._get_dgram().close()
        finally:
            self._dgram = None

    @staticmethod
    def _process_response(data: bytes, interpret: bool) -> bytes:
        """
        Process a response from the server.

        If interpret is True, we do a lazy attempt of parsing the data like an actual Quake3 client might for displaying
        in the chat.
        """

        if not data.startswith(b"\xFF" * 4):
            raise ValueError("Invalid data received from server")

        data = data[4:]

        if data == b"Bad rconpassword.":
            raise IncorrectPasswordError()

        if interpret:
            data = data.removeprefix(b"print\n").removeprefix(b"broadcast: ")

            if data.startswith(b"print "):
                data = data.removeprefix(b"print ")

            data = data.strip(b'" \n\r')

        return data

    async def _get_response(self, interpret: bool) -> bytes:
        """
        Read a response from the server

        Since packets may be fragmented and there is no way to tell if they are, the client makes an attempt to read
        more from the server until either the timeout is passed or the fragment_read_timeout is passed for an
        individual call to asyncio_dgram.DatagramClient(...).recv().
        """

        start_time = time.perf_counter()
        data = bytearray()

        while (time.perf_counter() - start_time) < self.timeout:
            try:
                part: bytes
                part, remote = await asyncio.wait_for(
                    self._get_dgram().recv(), self.fragment_read_timeout
                )
                self.logger.debug("Received %s from %s", part, remote)
                data.extend(self._process_response(part, interpret=interpret))
            except asyncio.TimeoutError:
                break

        return bytes(data)

    async def send_command(self, command: str, *, interpret: bool = False) -> str:
        """
        Sends a command to the server and reads the response back.

        If interpret is true, the response will be processed to be more similar to what would actually appear
        in the in-game chat.
        """

        message = (b"\xFF" * 4) + f'rcon "{self.password}" {command}'.encode("ascii")
        await self._retry(lambda: asyncio.wait_for(self._get_dgram().send(message), self.timeout))

        response = await asyncio.wait_for(self._get_response(interpret), self.timeout)

        return response.decode("ascii")
