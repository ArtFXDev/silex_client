import asyncio
import os

import gazu


def authentificate_gazu():
    gazu.set_host(os.getenv("SILEX_ZOU_HOST"))
    asyncio.run(gazu.log_in("admin@example.com", "mysecretpassword"))
