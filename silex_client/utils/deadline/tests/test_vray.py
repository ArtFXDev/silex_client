"""
Test for the vray Submitter

Passed on the rez plugin on machine md8-2017-046, 15/2/2023
Passed on the base plugin on machine md8-2017-046, 15/2/2023

"""

import getpass

import fileseq

from silex_client.utils.deadline.job import VrayJob
from silex_client.utils.deadline.runner import DeadlineRunner

# Recursion test (render is black)
# file_path = "M:/testpipe/shots/s01/p040/finallayout_main/publish/v000/vrecusiontest/Test_Renderer.vrscene",
# output_path = "M:/testpipe/shots/s01/p040/finallayout_main/publish/v000/exr/render/vrecusiontest/testpipe_s01_p040_finallayout_main_publish_v000_render_vrecusiontest.exr",

def get_vray_job():
    job = VrayJob(
        job_title="silex_test_job_rez_vray",
        user_name=getpass.getuser().lower(),
        frame_range=fileseq.FrameSet("1-2"),
        file_path="M:/testpipe/shots/s01/p010/lighting_maya_vray/publish/v000/vrscene/texture_test/test_no_layers.vrscene",
        output_path="M:/testpipe/shots/s01/p010/lighting_maya_vray/publish/v000/exr/render/test_no_layers/testpipe_s01_p010_lighting_maya_vray_publish_v000_render_test_no_layers.exr",
        rez_requires="vray testpipe",
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
    # job.job_info["Plugin"] = "Vray"
    # job.job_info["Name"] = "silex_test_job_vray"

    return job


if __name__ == "__main__":
    print("Test vray Start")

    # Submit to Deadline Runner
    dr = DeadlineRunner()

    job = get_vray_job()
    # job.job_info["Allowlist"] = "md8-2017-046"
    print(job)
    done = dr.run(job)
    print(f"Result: {done}")
