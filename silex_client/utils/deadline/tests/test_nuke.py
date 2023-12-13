import fileseq
from silex_client.utils.deadline.job import NukeJob
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

######### NUKE JOB
    rez_requires = "nuke testpipe"

    frames = fileseq.FrameSet("1-5")

    job = NukeJob(
        job_title="write1",
        user_name="angele.sionneau",
        frame_range=frames,
        rez_requires=rez_requires,
        file_path="M:/testpipe/shots/s01/p010/compositing_main/publish/v000/nk/v000/main/testpipe_s01_p010_comp_main_publish_v000_main.nk",
        output_path="",
        write_node="Write_test",
        use_gpu=True,
        nuke_x=True,
        batch_name="test_nuke_angele"
    )

    job.set_group("angele")
    job.set_chunk_size(5)
    job.set_priority(10)

    done = dr.run(job)