"""
Farm Handling.

JobTree -> holds the tree of jobs to be submitted

Job -> holds a single job with params, inside a jobtype hierarchy

Submitter -> holds the connection, wraps the deadline API and submits a job



"""
import asyncio

from Deadline.DeadlineConnect import DeadlineCon
import logging
import traceback
import aiohttp
from dotenv import load_dotenv
import os

logger = logging.getLogger('deadline')

load_dotenv()


# DEADLINE_HOST = os.getenv("DEADLINE_HOST")
# DEADLINE_PORT = os.getenv("DEADLINE_PORT")


def init_deadline():
    """
    Init and returns the deadline connection, or None if problem
    """

    # TODO replace with var loaded from env and real host name once webservice is running on vm
    DEADLINE_HOST = 'localhost'
    DEADLINE_PORT = 8081

    # deadline connection
    logger.info('Opening Deadline connection...')

    deadline = DeadlineCon(DEADLINE_HOST, DEADLINE_PORT)

    return deadline



class DeadlineRunner(object):
    dl = None

    def __init__(self):

        if not self.dl:
            self.dl = init_deadline()

    def run(self, job):
        try:
            logger.debug('About to submit "{}"'.format(job))
            job_submission = self.dl.Jobs.SubmitJob(job.job_info, job.plugin_info)
            if isinstance(job_submission, str):
                raise Exception(job_submission)
        except Exception as e:
            raise Exception(str(e))
    @staticmethod
    async def query_repos( query_url: str):
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
        groups = await DeadlineRunner.query_repos('http://localhost:8081/api/groups')

        return groups

    @staticmethod
    async def get_pools():
        pools = await DeadlineRunner.query_repos('http://localhost:8081/api/pools')

        return pools


if __name__ == '__main__':
    # # usage:
    # from silex_client.utils.deadline.job import DeadlineMayaBatchJob
    # job = DeadlineMayaBatchJob()
    # # dl = init_deadline()
    # dr = DeadlineRunner()
    # dr.run(job)
    """
    job = Job()
    jobid = dl.Jobs.SubmitJob(job.jobInfo, job.pluginInfo, idOnly=True).values()[0]
    """
    # import os
    # print(os.environ["REZ_USED_REQUEST"])
    # for k, v in six.iteritems(os.environ):
    #     print('{} : {}'.format(k, v))
    #     pass

    print(asyncio.run(get_groups()))
