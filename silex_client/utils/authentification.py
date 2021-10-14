import asyncio
import os

from aiohttp.client_exceptions import ClientConnectionError
import gazu

from silex_client.utils.log import logger


def authentificate_gazu():
    gazu.set_host(os.getenv("SILEX_ZOU_HOST"))
    try:
        asyncio.run(
            asyncio.wait_for(gazu.log_in("admin@example.com", "mysecretpassword"), 2)
        )
    except (asyncio.TimeoutError, ClientConnectionError):
        logger.error("Connection with the zou api could not be established")
