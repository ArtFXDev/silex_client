"""
Farm Handling.

JobTree -> holds the tree of jobs to be submitted

Job -> holds a single job with params, inside a jobtype hierarchy

Submitter -> holds the connection, wraps the deadline API and submits a job



"""
import getpass

from Deadline.DeadlineConnect import DeadlineCon

import logging

log = logging.getLogger('deadline')


def init_deadline():
    """
    Init and returns the deadline connection, or None if problem
    """

    # deadline connection
    log.info('Opening Deadline connection...')

    deadline = DeadlineCon(conf.DEADLINE_IP, conf.DEADLINE_PORT)

    print(deadline.connectionProperties)
    if not deadline:
        raise Exception('Unable to Connect to Deadline.')

    user = getpass.getuser().lower()
    if user not in deadline.Users.GetUserNames():
        print('User "{}" doesnt exist in Deadline'.format(user))
        return

    # deadline.EnableAuthentication(True)
    # deadline.SetAuthenticationCredentials(user, "")
    log.info('Connected to Deadline.')

    return deadline


class DeadlineRunner(object):

    dl = None

    def __init__(self):

        if not self.dl:
            self.dl = init_deadline()

    def run(self, job):
        try:
            log.debug('About to submit "{}"'.format(job))
            done = self.dl.Jobs.SubmitJob(job.job_info, job.plugin_info, idOnly=True)
            if isinstance(done, str):
                raise Exception(done)
            print(done)
            job_id = done
            # job_id = self.dl.Jobs.SubmitJob(job.job_info, job.plugin_info, idOnly=True).values()[0]
            log.info('Submitted "{}" under ID "{}"'.format(job, job_id))
            return job_id
        except Exception as e:
            raise Exception(str(e))


if __name__ == '__main__':

    # usage:
    from silex_client.utils.deadline.job import DeadlineMayaBatchJob
    job = DeadlineMayaBatchJob()
    # dl = init_deadline()
    dr = DeadlineRunner()
    dr.run(job)
    """
    job = Job()
    jobid = dl.Jobs.SubmitJob(job.jobInfo, job.pluginInfo, idOnly=True).values()[0]
    """
    # import os
    # print(os.environ["REZ_USED_REQUEST"])
    # for k, v in six.iteritems(os.environ):
    #     print('{} : {}'.format(k, v))
    #     pass
