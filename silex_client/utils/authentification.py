import asyncio
import os

import aiohttp
import gazu
import gazu.client
from aiohttp.client_exceptions import (ClientConnectionError, ContentTypeError,
                                       InvalidURL)

from silex_client.utils.log import logger


def is_authentificated() -> bool:
    """
    Test if the gazu client has already valid authentification tokens
    """

    async def test_authentification():
        headers = gazu.client.default_client.headers
        async with aiohttp.ClientSession(headers=headers) as session:
            silex_service_host = os.getenv("SILEX_ZOU_HOST", "")
            query_url = f"{silex_service_host}/auth/authenticated"
            async with session.get(query_url) as response:
                return await response.json()

    try:
        return asyncio.run(test_authentification()).get("authenticated", False)
    except (ClientConnectionError, ContentTypeError, InvalidURL):
        logger.warning("Authentification failed, could not reach the ZOU API")
        return False


def authentificate_gazu() -> bool:
    """
    Get the zou authentification token from the socket service
    """
    gazu.set_host(os.getenv("SILEX_ZOU_HOST"))

    async def get_authentification_token():
        async with aiohttp.ClientSession() as session:
            silex_service_host = os.getenv("SILEX_SERVICE_HOST", "")
            async with session.get(f"{silex_service_host}/auth/token") as response:
                return await response.json()

    # Get the authentification token
    if not is_authentificated():
        try:
            authentification_token = asyncio.run(get_authentification_token())
        except (ClientConnectionError, ContentTypeError, InvalidURL):
            logger.warning(
                "Could not get the cgwire authentification token from the silex socket service"
            )
            return False

        # Set the authentification token
        gazu.client.set_tokens(authentification_token)

    # Make sure the authentification worked
    try:
        asyncio.run(gazu.client.host_is_valid())
    except (ClientConnectionError):
        logger.warning("Connection with the zou api could not be established")
        return False

    return True
