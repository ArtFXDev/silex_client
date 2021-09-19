import shutil
import contextlib
import sys
import os


def build(source_path, build_path, install_path, targets):
    """
    Build the rez package and install it if requested
    """
    src = os.path.join(source_path, "silex_client")
    config = os.path.join(source_path, "config")
    package = os.path.join(source_path, "package.py")

    # TODO: Handle these files in the pre_test_command function
    lint = os.path.join(source_path, ".pylintrc")
    unit = os.path.join(source_path, "pytest.ini")

    # Clear the build folder, if a previous build were made
    if os.path.exists(build_path):
        with contextlib.suppress(FileNotFoundError):
            shutil.rmtree(os.path.join(build_path, "silex_client"))
            shutil.rmtree(os.path.join(build_path, "config"))
            os.remove(os.path.join(build_path, "package.py"))
            os.remove(os.path.join(build_path, ".pylintrc"))
            os.remove(os.path.join(build_path, "pytest.ini"))

    # Copy the source to the build location
    shutil.copytree(src, os.path.join(build_path, "silex_client"))
    shutil.copytree(config, os.path.join(build_path, "config"))
    shutil.copy(package, build_path)
    shutil.copy(lint, build_path)
    shutil.copy(unit, build_path)

    if "install" in (targets or []):
        # Clear the install folder if a previous install where already here
        if os.path.exists(install_path):
            with contextlib.suppress(FileNotFoundError):
                shutil.rmtree(install_path)

        # Copy the source to the install location
        shutil.copytree(src, os.path.join(install_path, "silex_client"))
        shutil.copytree(config, os.path.join(install_path, "config"))
        shutil.copy(package, install_path)
        shutil.copy(lint, install_path)
        shutil.copy(unit, install_path)


if __name__ == '__main__':
    build(source_path=os.environ['REZ_BUILD_SOURCE_PATH'],
          build_path=os.environ['REZ_BUILD_PATH'],
          install_path=os.environ['REZ_BUILD_INSTALL_PATH'],
          targets=sys.argv[1:])
