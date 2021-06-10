"""
  YamlWithInclude entry file
"""

import os
import logging
import yaml

class YamlWithInclude(yaml.SafeLoader):
    """
      Class YamlWithInclude
    """

    @staticmethod
    def load(file_to_open):
        """
        load a .yaml with taking care of !include
        """
        buffer = "" # to return complete file
        try:
            with open(file_to_open) as file:
                for line in file.readlines():
                    if "#" in line:
                        line = line.split("#")[0] # exclude all comment things
                    if "!include" in line:
                        path_to_include = line.rstrip().replace("!include ", '')
                        try:

                            # clean and get current path
                            current_path = file_to_open.replace('/', os.sep).replace('\\', os.sep).replace("\\", os.sep)
                            current_path = current_path.replace(current_path.split(os.path.sep)[-1], '')
                            # clean include path
                            clean_include_path = path_to_include.replace('/', os.sep).replace('\\', os.sep).replace("\\", os.sep)

                            # open include file
                            include_path = os.path.join(current_path, clean_include_path)
                            with open(include_path) as include_file:
                                #read content of the include file and add it to the main buffer
                                buffer += include_file.read()
                                buffer += "\r"
                        except Exception as err:
                            logging.error(f"Error on include parsing :{err}")
                    else:
                        buffer += line # add line to complete file
        except Exception as err:
            logging.error(f"error on load .yaml file: {err}")
        return yaml.load(buffer, YamlWithInclude)
