import fileseq
from silex_client.utils.deadline.job import (DeadlineCommandLineJob,
                                            DeadlineNukeJob)
from silex_client.utils.deadline.runner import DeadlineRunner

from silex_client.utils.log import flog

"""
Notes:
- make a test for each plugin
- make a test for each machine
- make a test for each plugin for each machine
- rez_requires can be optional for most plugins
- allow string frame_range ?
"""

if __name__ == "__main__":
    # Submit to Deadline Runner
    dr = DeadlineRunner()

    ###### COMMAND LINE
    """
    full_cmd = "rez env houdini arnold testpipe -- hython -m hrender //tars.artfx.fr/testpipe/testpipe/shots/s01/p010/lighting_hou_arnold/publish/v000/hip/main/testpipe_s01_p010_lighting_hou_arnold_publish_v000_main.hipnc -e -v -S -w 480 -h 270 -f 1 2 -d /out/arnold1 -o //tars.artfx.fr/testpipe/testpipe/shots/s01/p010/lighting_hou_arnold/publish/v000/exr/render/arnold/testpipe_s01_p010_lighting_hou_arnold_publish_v000_render_arnold.$F4.exr"

    rez_requires = "houdini arnold testpipe"
    argument_cmd = "hython -m hrender //tars.artfx.fr/testpipe/testpipe/shots/s01/p010/lighting_hou_arnold/publish/v000/hip/main/testpipe_s01_p010_lighting_hou_arnold_publish_v000_main.hipnc -e -v -S -w 480 -h 270 -f 1 2 -d /out/arnold1 -o //tars.artfx.fr/testpipe/testpipe/shots/s01/p010/lighting_hou_arnold/publish/v000/exr/render/arnold/testpipe_s01_p010_lighting_hou_arnold_publish_v000_render_arnold.$F4.exr"

    frames = fileseq.FrameSet("1-5")

    job = DeadlineCommandLineJob(
        job_title="silex_test_job",
        user_name="michael.haussmann",
        frame_range=frames,
        command=full_cmd,
        rez_requires=rez_requires,
    )

    job.set_group("pipeline")
    # job.set_pool(parameters["pools"])
    job.set_chunk_size(5)
    job.set_priority(60)
    

    done = dr.run(job)
    print(f"Result: {done}")
    """

    ######### NUKE JOB
    rez_requires = "nuke testpipe"

    frames = fileseq.FrameSet("1-5")

    job = DeadlineNukeJob(
        job_title="write1",
        user_name="angele.sionneau",
        frame_range=frames,
        rez_requires=rez_requires,
        scenefile_name="M:\\testpipe\\shots\\s01\\p010\\compositing_main\\publish\\v000\\nk\\v000\main\\testpipe_s01_p010_comp_main_publish_v000_main.nk",
        outputfile_name="",
        write_node="Write1",
        use_gpu=True,
        batch_name="test_nuke_angele"
    )

    job.set_group("angele")
    job.set_chunk_size(5)
    job.set_priority(10)

    flog.info(job)
    done = dr.run(job)
