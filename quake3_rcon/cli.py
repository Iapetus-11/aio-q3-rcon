import asyncio
import logging
import typing as t
import validators  # type: ignore

import click

from quake3_rcon import Client, IncorrectPasswordError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('quake3-rcon')

EXTRA_VALID_ADDRESSES = {
    'localhost',
    '::1',
}


def address_cb(ctx: click.Context, param: click.Parameter, value: t.Any) -> str:
    port = ctx.params.get("port")

    if port is not None and ':' in value:
        raise click.BadParameter("You can't specify the port twice")

    address_has_port = ':' in value
    address_without_port = ":".join(value.split(":")[:-1]) if ":" in value else value

    if port is None and address_has_port:
        try:
            port = value.split(":")[-1]
        except IndexError:
            raise click.UsageError("You must specify the port in the address or as a parameter with --port <value>")

        # jank to set port value to port parsed from addressed
        if ctx.default_map is None:
            ctx.default_map = {}
        ctx.default_map['port'] = port

    if not (validators.domain(address_without_port) or validators.ipv4(address_without_port) or validators.ipv6(address_without_port) or address_without_port.lower() in EXTRA_VALID_ADDRESSES):
        raise click.BadParameter("Specified address is neither a valid domain name or IP address")

    return value


def integer_range_cb(ctx: click.Context, param: click.Parameter, value: t.Any) -> int | None:
    if not param.required and not value:
        return param.get_default(ctx)

    try:
        value = int(value)
    except ValueError:
        raise click.BadParameter(f"{param.human_readable_name} must be an integer value")

    assert isinstance(param.type, click.IntRange)

    if param.type.min > value > param.type.max:
        raise click.BadParameter(f"{param.human_readable_name} must be between {param.type.min} and {param.type.max}")

    return value


def float_range_cb(ctx: click.Context, param: click.Parameter, value: t.Any) -> float | None:
    if not param.required and not value:
        return param.get_default(ctx)

    try:
        value = float(value)
    except ValueError:
        raise click.BadParameter(f"{param.human_readable_name} must be a decimal value")

    assert isinstance(param.type, click.FloatRange)

    if param.type.min > value > param.type.max:
        raise click.BadParameter(f"{param.human_readable_name} must be between {param.type.min} and {param.type.max}")

    return value


def port_cb(ctx: click.Context, param: click.Parameter, value: t.Any):
    if value is None:
        value = ctx.params.get("port")

    return integer_range_cb(ctx, param, value)


def debug_cb(ctx: click.Context, param: click.Parameter, value: t.Any):
    if value:
        logger.setLevel(logging.DEBUG)


@click.command()
@click.argument('address', callback=address_cb)
@click.option('-p', '--port', type=click.IntRange(1, 65535), callback=port_cb, default=27960)
@click.argument('password')
@click.option('--timeout', type=click.FloatRange(0.01), callback=float_range_cb, default=2.0)
@click.option('--fragment-read-timeout', '--fr-timeout', type=click.FloatRange(0.01), callback=float_range_cb, default=0.35)
@click.option('--retries', type=click.IntRange(1), callback=integer_range_cb, default=2)
@click.option('--debug', is_flag=True, expose_value=False, is_eager=True, callback=debug_cb)
def rcon(address: str, port: int, password: str, timeout: float, fragment_read_timeout: float, retries: int):
    async def _rcon():
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
            logger.error('', exc_info=True)
        finally:
            await client.close()

    asyncio.run(_rcon())
