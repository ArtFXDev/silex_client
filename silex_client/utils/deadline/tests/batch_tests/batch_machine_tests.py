from functools import lru_cache

from silex_client.utils.deadline.runner import init_deadline, DeadlineRunner
from silex_client.utils.deadline.tests.test_arnold import get_arnold_job
from silex_client.utils.deadline.tests.test_husk import get_husk_job
from silex_client.utils.deadline.tests.test_vray import get_vray_job

dl = init_deadline()
dr = DeadlineRunner()

job_getters = {'vray': get_vray_job,
               'arnold': get_arnold_job,
               'husk': get_husk_job,
               }

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


def launch_worker_test_jobs(group, plugins, skip_completed=True, skip_active=True, start_suspended=True, machines_only=None):

    print(f"Submitting batch jobs for {group} & Plugins: {plugins}. {machines_only or ''}")

    submitted = []

    for job_getter in [job_getters.get(plugin) for plugin in plugins]:

        name = f"test__{str(job_getter).split('_')[1]}"

        workers = dl.Slaves.GetSlaveNamesInGroup(group)
        job = job_getter()
        job.job_info["BatchName"] = f"TEST_workers__{group}"
        job.job_info["Group"] = group
        if start_suspended:
            job.job_info["InitialStatus"] = "Suspended"

        for worker in workers:

            if machines_only and worker not in machines_only:
                print(f"Worker {worker} is not in {machines_only}. Skipped.")
                continue

            job_name = f"{name}__{worker}"

            if skip_completed and job_name in get_completed_job_names():
                print(f"Job {job_name} is completed. Skipped.")
                continue

            if skip_active and job_name in get_active_job_names():
                print(f"Job {job_name} is active. Skipped.")
                continue

            job.job_info["Name"] = job_name
            job.job_info["Allowlist"] = worker
            # print(job)
            done = dr.run(job)
            print(f"Submitted : {done}")
            submitted.append(done)

    if not submitted:
        print("Nothing was submitted. Check params.")
        return

    print(f"Submitted {len(submitted)} jobs.")


if __name__ == "__main__":

    print("Test launch_worker_test_jobs Start")
    group = "classrooms"
    # group = "pfe"
    # launch_worker_test_jobs(group, plugins=['vray', 'arnold', 'husk], start_suspended=False)
    launch_worker_test_jobs(group, plugins=['arnold'], start_suspended=False)

