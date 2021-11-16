import asyncio
import os

from aiohttp.client_exceptions import ClientConnectionError, ContentTypeError
import gazu
import gazu.client
import aiohttp

from silex_client.utils.log import logger


def authentificate_gazu():
    gazu.set_host(os.getenv("SILEX_ZOU_HOST"))

    async def get_authentification_token():
        async with aiohttp.ClientSession() as session:
            silex_service_host = os.getenv("SILEX_SERVICE_HOST", "")
            async with session.get(f"{silex_service_host}/auth/token") as response:
                return await response.json()

    try:
        authentification_token = asyncio.run(get_authentification_token())
    except (ClientConnectionError, ContentTypeError):
        logger.error("Connection with the silex service could not be established")
        return False

    gazu.client.set_tokens(authentification_token)
    try:
        asyncio.run(gazu.client.host_is_valid())
        return True
    except (ClientConnectionError):
        logger.error("Connection with the zou api could not be established")
        return False
