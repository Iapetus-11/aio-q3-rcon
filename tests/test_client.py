import asyncio
from collections.abc import Sequence

import pytest

from aioq3rcon import Client

PACKET_HEADER = b"\xff" * 4
REMOTE_ADDRESS = ("127.0.0.1", 27960)


class DatagramStub:
    def __init__(self, packets: Sequence[bytes]):
        self.packets = list(packets)

    async def recv(self) -> tuple[bytes, tuple[str, int]]:
        if self.packets:
            return self.packets.pop(0), REMOTE_ADDRESS

        await asyncio.Event().wait()
        raise AssertionError("unreachable")


async def get_response(packets: Sequence[bytes], *, interpret: bool) -> bytes:
    client = Client("127.0.0.1", fragment_read_timeout=0.001)
    client._dgram = DatagramStub(packets)  # type: ignore[assignment]
    return await client._get_response(interpret)


def test_interpret_response_preserves_cvar_quotes_and_removes_colors() -> None:
    response = Client._interpret_response(
        b'"g_gametype" is: "dm^7" default: "dm^7" ' b'info: "Current game type^7"\r\n'
    )

    assert response == (b'"g_gametype" is: "dm" default: "dm" info: "Current game type"')


def test_interpret_response_preserves_significant_spaces() -> None:
    response = Client._interpret_response(b"  padded output  \n")

    assert response == b"  padded output  "


def test_interpret_response_uses_quake_alphanumeric_color_syntax() -> None:
    response = Client._interpret_response(b"^1Red ^AGreen ^!literal caret\n")

    assert response == b"Red Green ^!literal caret"


def test_fragmented_color_code_is_interpreted_after_assembly() -> None:
    packets = [
        PACKET_HEADER + b"print\nServer ^",
        PACKET_HEADER + b"print\n7ready\n",
    ]

    response = asyncio.run(get_response(packets, interpret=True))

    assert response == b"Server ready"


def test_interpreted_broadcast_removes_framing_and_extended_colors() -> None:
    packets = [PACKET_HEADER + b'print\nbroadcast: print "^1Server ^Arestarting^7"\n']

    response = asyncio.run(get_response(packets, interpret=True))

    assert response == b'"Server restarting"'


def test_raw_response_is_unchanged_except_for_packet_header() -> None:
    payload = b'print\n"g_gametype" is: "dm^7"\n'

    response = asyncio.run(get_response([PACKET_HEADER + payload], interpret=False))

    assert response == payload


def test_response_without_connectionless_packet_header_is_rejected() -> None:
    with pytest.raises(ValueError, match="Invalid data received from server"):
        Client._process_response(b"print\nresponse", interpret=True)
