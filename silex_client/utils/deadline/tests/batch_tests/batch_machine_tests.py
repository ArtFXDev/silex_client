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
    """ Currently unused """
    jobs = dl.Jobs.GetJobsInState('Completed')
    return [job.get('Props').get('Name') for job in jobs]

@lru_cache()
def get_active_job_names():
    """ Currently unused """
    jobs = dl.Jobs.GetJobsInState('Active')
    return [job.get('Props').get('Name') for job in jobs]

@lru_cache()
def get_all_job_names():
    print('Calling Deadline')
    jobs = dl.Jobs.GetJobs()
    return [job.get('Props').get('Name') for job in jobs]


def launch_worker_test_jobs(group, plugins, skip_existing=True, start_suspended=True, machines_only=None):

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

            if skip_existing and job_name in get_all_job_names():
                print(f"Job {job_name} exists. Skipped.")
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

    groups = ['pfe', 'classrooms']

    import argparse
    parser = argparse.ArgumentParser(
        prog="Deadline Submitter Tests",
        description="Launches test jobs on workers, per region and renderer",
        epilog="Thanks for using %(prog)s! :)",
    )

    parser.add_argument(
        "group", help=f"Group to launch on. Available: {', '.join(groups)}"
    )

    parser.add_argument("-ar", "--arnold", action="store_true", help="Launch Arnold Jobs")
    parser.add_argument("-vr", "--vray", action="store_true", help="Launch Vray Jobs")
    parser.add_argument("-hu", "--husk", action="store_true", help="Launch Husk Jobs")

    parser.add_argument("-s", "--suspend", action="store_true", help="Start suspended")

    args = parser.parse_args()

    print("Test launch_worker_test_jobs Start")
    # group = "classrooms"
    # group = "pfe"

    plugins = []
    if args.arnold:
        plugins.append('arnold')
    if args.vray:
        plugins.append('vray')
    if args.husk:
        plugins.append('husk')

    if not plugins:
        plugins = ['vray', 'arnold', 'husk']

    # launch_worker_test_jobs(group, plugins=['vray', 'arnold', 'husk], start_suspended=False)
    launch_worker_test_jobs(args.group, plugins=['vray', 'arnold', 'husk'], start_suspended=args.suspend)

