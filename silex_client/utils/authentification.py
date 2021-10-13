import asyncio

import gazu


def authentificate_gazu():
    gazu.set_host("http://172.16.2.52:8080/api")
    asyncio.run(gazu.log_in("admin@example.com", "mysecretpassword"))
