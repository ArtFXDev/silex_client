import logging
import traceback
import os

import aiohttp
from Deadline.DeadlineConnect import DeadlineCon

logger = logging.getLogger("deadline")

# set in rez package
DEADLINE_HOST = os.getenv("DEADLINE_HOST")
DEADLINE_PORT = os.getenv("DEADLINE_PORT")
# DEADLINE_HOST = "localhost"
# DEADLINE_PORT = "8081"


def init_deadline():
    """
    Init and returns the deadline connection, or None if problem
    """

    # deadline connection
    logger.info("Opening Deadline connection...")

    deadline = DeadlineCon(DEADLINE_HOST, DEADLINE_PORT)

    return deadline


class DeadlineRunner:
    dl = None

    def __init__(self):
        if not self.dl:
            self.dl = init_deadline()

    def run(self, job):
        try:
            logger.debug('About to submit "{}"'.format(job))
            job_submission = self.dl.Jobs.SubmitJob(job.job_info, job.plugin_info)
            return job_submission
        except Exception as e:
            raise Exception(str(e))

    @staticmethod
    async def query_repos(query_url: str):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(query_url) as response:
                    query = await response.json()

                    return query

        except Exception as e:
            logger.error(
                "Could not connect to Deadline WebService and query Groups and Pool information: "
                + traceback.format_exc()
            )
            raise Exception(str(e))

    @staticmethod
    async def get_groups():
        groups = await DeadlineRunner.query_repos(
            f"http://{DEADLINE_HOST}:{DEADLINE_PORT}/api/groups"
        )

        return groups

    @staticmethod
    async def get_pools():
        pools = await DeadlineRunner.query_repos(
            f"http://{DEADLINE_HOST}:{DEADLINE_PORT}/api/pools"
        )

        return pools
