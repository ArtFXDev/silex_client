"""
https://docs.thinkboxsoftware.com/products/deadline/10.2/3_Python%20Reference/class_jobs_1_1_jobs.html#ab0dfa113ef7f70fb0f85398dfaf29f43

States : Active, Suspended, Completed, Failed, and Pending. Note that Active covers both Queued and Rendering jobs.
"""
from pprint import pprint
from functools import lru_cache

from silex_client.utils.deadline.runner import init_deadline

dl = init_deadline()


@lru_cache()
def get_failed_jobs():
    print('Calling DL')
    jobs = dl.Jobs.GetJobsInState('Failed')
    return [job.get('Props').get('Name') for job in jobs]


@lru_cache()
def get_failed_job_names():
    print('Calling DL')
    jobs = dl.Jobs.GetJobsInState('Failed')
    return [job.get('Props').get('Name') for job in jobs]

@lru_cache()
def get_completed_job_names():
    print('Calling DL')
    jobs = dl.Jobs.GetJobsInState('Completed')
    return [job.get('Props').get('Name') for job in jobs]


jobs = dl.Jobs.GetJobsInState('Failed')
for job in jobs:
    job_name = job.get('Props').get('Name')
    job_user = job.get('Props').get('User')
    job_id = job.get('_id')
    tasks = dl.Tasks.GetJobTasks(job_id)
    if not tasks:
        continue
    task_id = tasks.get('Tasks')[-1].get('TaskID')  # last task
    task_worker = tasks.get('Tasks')[-1].get('Slave')
    reports = dl.TaskReports.GetTaskErrorReports(job_id, task_id)
    if not reports:
        # print(f"No report on last task (task_id)")
        continue
    print("*" * 100)
    print(f"{job_name} -- {job_user} -- {task_worker} -- ({job_id})")
    print("Error:")
    error_msg = reports[-1].get("Title").replace('\n', ' ')
    print(error_msg[0:240])
    print("")