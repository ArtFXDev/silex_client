from pprint import pprint
from silex_client.utils.deadline.runner import init_deadline, DeadlineRunner
from silex_client.utils.deadline.tests.test_vray import get_vray_job

dl = init_deadline()
dr = DeadlineRunner()

group = "pipeline"
submitter = "vray"
job_getter = get_vray_job
name = f"test__{submitter}"

workers = dl.Slaves.GetSlaveNamesInGroup(group)
job = job_getter()
job.job_info["BatchName"] = f"TEST_workers__{group}"
job.job_info["Group"] = group

for worker in workers:

    job.job_info["Name"] = f"{name}__{worker}"
    job.job_info["Allowlist"] = worker
    print(job)
    done = dr.run(job)
    print(f"Result: {done}")


