import asyncio
import logging
import typing as t

import click
import validators

from . import Client, IncorrectPasswordError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("aio-q3-rcon")

EXTRA_VALID_ADDRESSES = {
    "localhost",
    "::1",
}


def address_cb(ctx: click.Context, param: click.Parameter, value: t.Any) -> str:
    if not (
        validators.domain(value)
        or validators.ipv4(value)
        or validators.ipv6(value)
        or value.lower() in EXTRA_VALID_ADDRESSES
    ):
        raise click.BadParameter("Specified address is neither a valid domain name or IP address")

    return t.cast(str, value)


def debug_cb(ctx: click.Context, param: click.Parameter, value: t.Any) -> None:
    if value:
        logger.setLevel(logging.DEBUG)


@click.command()
@click.argument("address", callback=address_cb)
@click.option("-p", "--port", type=click.IntRange(1, 65535), default=27960)
@click.argument("password")
@click.option("--timeout", type=click.FloatRange(0.01), default=2.0)
@click.option(
    "--fragment-read-timeout",
    "--fr-timeout",
    type=click.FloatRange(0.01),
    default=0.35,
)
@click.option("--retries", type=click.IntRange(1), default=2)
@click.option("--debug", is_flag=True, expose_value=False, is_eager=True, callback=debug_cb)
def rcon(
    address: str,
    port: int,
    password: str,
    timeout: float,
    fragment_read_timeout: float,
    retries: int,
) -> None:
    async def _rcon() -> None:
        client = Client(
            address,
            port,
            password,
            timeout=timeout,
            fragment_read_timeout=fragment_read_timeout,
            retries=retries,
            logger=logger,
        )

        try:
            await client.connect()

            click.echo(f"Connected to Quake 3 server at {client.host}:{client.port}")

            while True:
                command = input("> ")
                click.echo(await client.send_command(command, interpret=True))
        except IncorrectPasswordError:
            raise click.BadParameter("Incorrect password specified!")
        except Exception:
            click.echo("An exception occurred:")
            logger.error("", exc_info=True)
        finally:
            await client.close()

    asyncio.run(_rcon())
