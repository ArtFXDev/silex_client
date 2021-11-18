import asyncio
import os

from aiohttp.client_exceptions import ClientConnectionError, ContentTypeError
import gazu
import gazu.client
import aiohttp

from silex_client.utils.log import logger


def authentificate_gazu() -> bool:
    gazu.set_host(os.getenv("SILEX_ZOU_HOST"))

    async def get_authentification_token():
        async with aiohttp.ClientSession() as session:
            silex_service_host = os.getenv("SILEX_SERVICE_HOST", "")
            async with session.get(f"{silex_service_host}/auth/refresh-token") as response:
                return await response.json()

    # Get the authentification token
    try:
        authentification_token = asyncio.run(get_authentification_token())
    except (ClientConnectionError, ContentTypeError):
        logger.error("Connection with the silex service could not be established")
        return False

    # Set the authentification token
    gazu.client.set_tokens(authentification_token)

    # Make sure the authentification worked
    try:
        asyncio.run(gazu.client.host_is_valid())
    except (ClientConnectionError):
        logger.error("Connection with the zou api could not be established")
        return False

    return True
