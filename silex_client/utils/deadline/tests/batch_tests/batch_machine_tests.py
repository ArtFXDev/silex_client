from functools import lru_cache

from silex_client.utils.deadline.runner import init_deadline, DeadlineRunner
from silex_client.utils.deadline.tests.test_arnold import get_arnold_job
from silex_client.utils.deadline.tests.test_husk import get_husk_job
from silex_client.utils.deadline.tests.test_vray import get_vray_job

dl = init_deadline()
dr = DeadlineRunner()

group = "classrooms"
# group = "pfe"
job_getters = [get_vray_job]  # , get_arnold_job, get_husk_job]


@lru_cache()
def get_completed_job_names():
    print('Calling DL')
    jobs = dl.Jobs.GetJobsInState('Completed')
    return [job.get('Props').get('Name') for job in jobs]

@lru_cache()
def get_active_job_names():
    print('Calling DL')
    jobs = dl.Jobs.GetJobsInState('Active')
    return [job.get('Props').get('Name') for job in jobs]


for job_getter in job_getters:

    name = f"test__{str(job_getter).split('_')[1]}"

    workers = dl.Slaves.GetSlaveNamesInGroup(group)
    job = job_getter()
    job.job_info["BatchName"] = f"TEST_workers__{group}"
    job.job_info["Group"] = group
    # job.job_info["InitialStatus"] = "Suspended"

    for worker in workers:

        job_name = f"{name}__{worker}"

        if job_name in get_completed_job_names() or job_name in get_active_job_names():
            print(f"Job {job_name} exists. Skipped.")
            continue

        job.job_info["Name"] = job_name
        job.job_info["Allowlist"] = worker
        # print(job)
        done = dr.run(job)
        print(f"Result: {done}")


