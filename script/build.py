import shutil
import sys
import os


def build(source_path, build_path, install_path, targets):
    src = os.path.join(source_path, "silex_client")
    config = os.path.join(source_path, "package.py")

    # Copy the source to the build location
    if os.path.exists(build_path):
        # Clear the build folder
        try:
            shutil.rmtree(os.path.join(build_path, "silex_client"))
            os.remove(os.path.join(build_path, "package.py"))
        except Exception as ex:
            print("WARNING : Could not clear the build folder")
            print(ex)

    shutil.copytree(src, os.path.join(build_path, "silex_client"))
    shutil.copy(config, build_path)

    # Copy the source to the install location
    if "install" in (targets or []):
        if os.path.exists(install_path):
            # Clear the install folder
            try:
                shutil.rmtree(install_path)
            except Exception as ex:
                print("WARNING : Could not clear the install folder")
                print(ex)

        shutil.copytree(src, install_path)
        shutil.copy(config, install_path)


if __name__ == '__main__':
    build(source_path=os.environ['REZ_BUILD_SOURCE_PATH'],
          build_path=os.environ['REZ_BUILD_PATH'],
          install_path=os.environ['REZ_BUILD_INSTALL_PATH'],
          targets=sys.argv[1:])
