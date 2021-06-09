import os
from silex_client.libs.yaml_with_include import YamlWithInclude


def main():
    buffer = ""
    current_file = __file__.split(os.path.sep)[-1]
    root = __file__.replace(current_file,'')
    file_to_open = f"{root}yaml{os.path.sep}child{os.path.sep}child.yml"
    print(file_to_open)
    data = YamlWithInclude.load(file_to_open)
    print(data)