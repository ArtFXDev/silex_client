from typing import Any, List

from fileseq import FrameSet


def chunks(to_split_list: List[Any], chunk_size: int):
    """
    Yield successive n-sized chunks from lst.
    to_split_list : list[Any] -> list that needs to be chunked
    chunk_size : int -> chunk size
    """
    for i in range(0, len(to_split_list), chunk_size):
        yield to_split_list[i : i + chunk_size]


def split_frameset(frame_set: FrameSet, chunk_size: int) -> List[FrameSet]:
    """
    Split a fileseq.FrameSet into equal frameset chunks
    """
    frames_list: List[int] = list(FrameSet(frame_set))
    frames_split = list(chunks(frames_list, chunk_size))
    return [FrameSet(frames_list) for frames_list in frames_split]
