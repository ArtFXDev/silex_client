"""
Test for the Houdini Submitter
with arnold scene

Passed on the base plugin on md8-2017-046, 15/2/2023
Passed on the rez plugin on md8-2017-046, 15/2/2023
Failed on md9-2018-05 "FailRenderException : Error: No module named 'vfh_py'"

"""
import getpass

import fileseq

from silex_client.utils.deadline.job import HoudiniJob
from silex_client.utils.deadline.runner import DeadlineRunner


def get_houdini_arnold_job():
    job = HoudiniJob(
        job_title="silex_test_job_rez_houdini_arnold",
        user_name=getpass.getuser().lower(),
        frame_range=fileseq.FrameSet("1-5"),
        file_path="M:/testpipe/shots/s01/p010/lighting_hou_arnold/publish/v000/hip/main/testpipe_s01_p010_lighting_hou_arnold_publish_v000_main.hipnc",
        output_path="M:/testpipe/shots/s01/p010/lighting_hou_arnold/publish/v000/exr/render/arnold1/testpipe_s01_p010_lighting_hou_arnold_publish_v000_render_arnold1.$F4.exr",
        rop_node="/out/arnold1",
        resolution=None,
        sim_job=False,
        rez_requires="houdini testpipe arnold",
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
    # job.job_info["Plugin"] = "Houdini"
    # job.job_info["Name"] = "silex_test_job_houdini_arnold"

    return job


if __name__ == "__main__":
    print("Test houdini_arnold Start")

    # Submit to Deadline Runner
    dr = DeadlineRunner()

    job = get_houdini_arnold_job()
    # job.job_info["Allowlist"] = "md8-2017-046"
    print(job)
    done = dr.run(job)
    print(f"Result: {done}")
