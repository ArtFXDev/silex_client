from typing import Any


def merge_dict(data_a: dict, data_b: dict) -> dict:
    """
    Merge the dict A into the dict B by merging their values recursively
    """
    # Check if the types are correct
    if not isinstance(data_a, dict) or not isinstance(data_b, dict):
        return data_a

    # Loop over data A and override data B
    for key, value in data_a.items():
        # Append the non existing keys
        if key not in data_b.keys():
            data_b[key] = value
        # Replace the non mergeable corresponding keys
        elif type(value) is not type(data_b[key]):
            data_b[key] = value
        # Merge the mergeable corresponding keys
        else:
            data_b[key] = merge_data(value, data_b[key])
    # Return the overriden data B
    return data_b


def merge_list(data_a: list, data_b: list) -> list:
    """
    Merge the list A into the list B by appending there values and replacing if
    the values matches in a certain way
    """
    # Check if the types are correct
    if not isinstance(data_a, list) or not isinstance(data_b, list):
        return data_a

    for item_a in data_a:
        # Find if some items in data B needs to be replaced
        try:
            match_index = next(index for index, item_b in enumerate(data_b)
                               if item_b["name"] == item_a["name"])
            data_b[match_index] = item_a
            continue
        except (KeyError, TypeError, StopIteration):
            pass

        # Otherwise just append the item into data B
        data_b.append(item_a)

    return data_b


def merge_data(data_a: Any, data_b: Any) -> Any:
    """
    Merge the data A into the data B by chosing the apropriate merge method
    """
    # Mapp the data types to their merge function
    mapping = {dict: merge_dict, list: merge_list}
    for data_type, handler in mapping.items():
        if isinstance(data_a, data_type) and isinstance(data_b, data_type):
            # Execute the apropriate merge function
            return handler(data_a, data_b)

    # Just return the data A if no handler has been found
    return data_a
