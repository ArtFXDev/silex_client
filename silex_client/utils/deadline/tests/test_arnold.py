"""
Test for the Arnold Kick Submitter

Passed on the rez plugin on machine md8-2017-046, 15/2/2023
Failed on the base plugin on machine md8-2017-046, 15/2/2023 "FailRenderException : 00:00:00   148MB ERROR   | [color_manager_ocio] could not read 'C:/Program Files/Autodesk/Maya2022/resources/OCIO-configs/Maya2022-default/config.ocio' OCIO profile."

"""

import getpass

import fileseq

from silex_client.utils.deadline.job import ArnoldJob
from silex_client.utils.deadline.runner import DeadlineRunner


def get_arnold_job():
    job = ArnoldJob(
        job_title="silex_test_job_rez_arnold",
        user_name=getpass.getuser().lower(),
        frame_range=fileseq.FrameSet("1-5"),
        file_path="M:/testpipe/shots/s01/p010/lighting_main/publish/v000/ass/main/renderSetupLayer1/testpipe_s01_p010_lighting_main_publish_v000_main_renderSetupLayer1.0001.ass",
        output_path="M:/testpipe/shots/s01/p010/lighting_main/publish/v000/exr/rendertestpipe_s01_p010_lighting_main_publish_v000_render_renderSetupLayer1.exr",
        rez_requires="arnold testpipe",
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
    # job.job_info["Plugin"] = "Arnold"
    # job.job_info["Name"] = "silex_test_job_arnold"

    return job


if __name__ == "__main__":
    print("Test arnold Start")

    # Submit to Deadline Runner
    dr = DeadlineRunner()

    job = get_arnold_job()
    job.job_info["Allowlist"] = "md8-2017-046"
    print(job)
    done = dr.run(job)
    print(f"Result: {done}")
