
from silex_client.utils.deadline.runner import init_deadline, DeadlineRunner
from silex_client.utils.deadline.tests.test_arnold import get_arnold_job
from silex_client.utils.deadline.tests.test_husk import get_husk_job
from silex_client.utils.deadline.tests.test_vray import get_vray_job

dl = init_deadline()
dr = DeadlineRunner()

group = "classrooms"
group = "pfe"
job_getters = [get_arnold_job, get_vray_job, get_husk_job]


for job_getter in job_getters:

    name = f"test__{str(job_getter).split('_')[1]}"

    workers = dl.Slaves.GetSlaveNamesInGroup(group)
    job = job_getter()
    job.job_info["BatchName"] = f"TEST_workers__{group}"
    job.job_info["Group"] = group
    job.job_info["InitialStatus"] = "Suspended"

    for worker in workers:

        job.job_info["Name"] = f"{name}__{worker}"
        job.job_info["Allowlist"] = worker
        print(job)
        done = dr.run(job)
        print(f"Result: {done}")


