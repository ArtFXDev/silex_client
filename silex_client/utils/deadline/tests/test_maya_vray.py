"""
Test for the Maya Submitter
with vray scene

Passed on the rez plugin on machine md8-2017-046, 15/2/2023
Passed on the base plugin on machine md8-2017-046, 15/2/2023

"""

import getpass

import fileseq

from silex_client.utils.deadline.job import MayaBatchJob
from silex_client.utils.deadline.runner import DeadlineRunner


def get_maya_vray_job():
    job = MayaBatchJob(
        job_title="silex_test_job_rez_maya_vray",
        user_name=getpass.getuser().lower(),
        frame_range=fileseq.FrameSet("1-5"),
        file_path="M:/testpipe/shots/s01/p010/lighting_maya_vray/publish/v000/ma/main/testpipe_s01_p010_lighting_maya_vray_publish_v000_main.ma",
        output_path="M:/testpipe/shots/s01/p010/lighting_maya_vray/publish/v000/exr/render/vray/testpipe_s01_p010_lighting_maya_vray_publish_v000_render_vray",
        renderer="vray",
        rez_requires="maya vray testpipe",
        batch_name="silex_test_jobs",
    )

    # optionals
    job.set_group("pipeline")
    # job.set_pool(parameters["pools"])
    # job.set_chunk_size(5)
    # job.set_priority(60)

    # extras
    # job.job_info["InitialStatus"] = "Suspended"

    # Uncomment to test the base plugin
    # job.job_info["Plugin"] = "MayaBatch"
    # job.job_info["Name"] = "silex_test_job_maya_vray"

    return job


if __name__ == "__main__":
    print("Test maya_vray Start")

    # Submit to Deadline Runner
    dr = DeadlineRunner()

    job = get_maya_vray_job()
    # job.job_info["Allowlist"] = "md8-2017-046"
    print(job)
    done = dr.run(job)
    print(f"Result: {done}")
