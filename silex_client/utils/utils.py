def chunks(to_split_list, chunk_size):
    """
    Yield successive n-sized chunks from lst.
    to_split_list : list[Any] -> list that needs to be chunked
    chunk_size : int -> chunk size
    """
    for i in range(0, len(to_split_list), chunk_size):
        yield to_split_list[i : i + chunk_size]
