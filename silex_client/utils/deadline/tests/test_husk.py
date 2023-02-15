"""
Test for the Husk Submitter

Passed on the rez plugin on machine md8-2017-046, 15/2/2023

"""
import getpass
import logging

import fileseq

from silex_client.utils.deadline.job import HuskJob
from silex_client.utils.deadline.runner import DeadlineRunner


if __name__ == "__main__":
    # Submit to Deadline Runner
    dr = DeadlineRunner()

    job = HuskJob(
        job_title="silex_test_job_rez_husk",
        user_name=getpass.getuser().lower(),
        frame_range=fileseq.FrameSet("1-5"),
        file_path="M:/testpipe/shots/s02/p010/lighting_main_husk/publish/v000/usd/main/testpipe_s02_p010_lighting_main_husk_publish_v000_main.usd",
        output_path="M:/testpipe/shots/s02/p010/lighting_main_husk/publish/v000/exr/render/testpipe_s02_p010_lighting_main_husk_publish_v000_render.$F4.exr",
        log_level=logging.DEBUG,
        rez_requires="houdini testpipe",
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
    # job.job_info["Plugin"] = "Husk_Dev"
    # job.job_info["Name"] = "silex_test_job_husk"
    # job.plugin_info["HuskRenderExecutable"] = "C:/Houdini19/bin/husk.exe"

    print(job)
    done = dr.run(job)["_id"]
    print(f"Result: {done}")
