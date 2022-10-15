import asyncio

from aioq3rcon import Client


async def main():
    async with Client("example.com", 27960, "password") as client:
        while True:
            command = input("> ")
            print(await client.send_command(command))


asyncio.run(main())
