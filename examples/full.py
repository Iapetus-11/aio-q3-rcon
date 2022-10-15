import asyncio
import logging

from aioq3rcon import Client


async def main():
    logging.basicConfig()
    logger = logging.getLogger("aio-q3-rcon")
    logger.setLevel(logging.DEBUG)

    async with Client(
        "example.com",
        27960,
        "password",
        timeout=2.0,
        fragment_read_timeout=0.35,
        retries=2,
        logger=logger,
    ) as client:
        while True:
            command = input("> ")
            print(await client.send_command(command, interpret=True))


asyncio.run(main())
