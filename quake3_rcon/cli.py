import typing as t
import validators

import asyncclick as click


def address_validator(ctx: click.Context, param: click.Parameter, value: t.Any):
    port = ctx.params.get("port")

    if port is not None and ':' in value:
        raise click.BadParameter("You can't specify the port twice")

    address_without_port = ":".join(value.split(":")[:-1])

    if port is None:
        try:
            port = value.split(":")[-1]
        except IndexError:
            raise click.UsageError("You must specify the port in the address or as a parameter with --port <value>")

        ctx.params["port"] = port

    if not (validators.domain(address_without_port) or validators.ipv4(address_without_port) or validators.ipv6(address_without_port)):
        raise click.BadParameter("Specified address is neither a valid domain name or IP address")

    return value


def port_validator(ctx: click.Context, param: click.Parameter, value: t.Any):
    if value is None:
        value = ctx.params.get("port")

    try:
        value = int(value)
    except ValueError:
        raise click.BadParameter("Port must be an integer")

    if 0 < value or value > 65535:
        raise click.BadParameter("Port must be between 0 and 65535")

    return value


@click.command()
@click.argument('address', callback=address_validator)
@click.option('-p', '--port', callback=port_validator)
async def rcon(address: str, port: int):
    print(f"address={address!r}, port={port!r}")
