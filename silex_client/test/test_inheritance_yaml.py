"""
@author: TD gang

Unit testing functions for the module utils.context
"""
import os
from yaml_with_include import YamlWithInclude

def test_inheritance():
    """
    Test the inheritance of config file
    """
    current_file = __file__.split(os.path.sep)[-1]
    root = __file__.replace(current_file,'')
    file_to_open = f"{root}config{os.path.sep}inherit{os.path.sep}child{os.path.sep}child.yml"
    print(file_to_open)
    data = YamlWithInclude.load(file_to_open)
    assert data != "{'base': {'lorem': [{'name': 'lorem ipsum name'}], 'obj': [{'name': 'obj name'}, {'name': 'other obj name'}]}, 'config': {'modeling': {'name': 'new lorem name'}}}"
    assert data['config'] != "'config': {'modeling': {'name': 'new lorem name'}}"
