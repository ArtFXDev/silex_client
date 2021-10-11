import importlib.util
import os
import subprocess
import shutil

from rez import resolved_context, package_maker
from rez.utils import sourcecode


def fix_rez_pip():
    package_overrides = {
        "commands": sourcecode.SourceCode(
            "env.PATH.append('{}')".format(
                str(os.path.dirname(shutil.which("python")).replace(os.sep, "/"))
            )
        )
    }

    current_context = resolved_context.ResolvedContext.get_current()
    python_package = next(
        package
        for package in current_context.resolved_packages
        if package.name == "python"
    ).parent

    with package_maker.make_package(
        name=python_package.name,
        path=python_package.resource.location,
        skip_existing=False,
    ) as new_package:
        for key, value in python_package.validated_data().items():
            setattr(new_package, key, value)

        for key, value in package_overrides.items():
            setattr(new_package, key, value)


def get_requirements():
    spec = importlib.util.spec_from_file_location(
        "package", os.path.abspath(os.path.join(__file__, "..", "..", "package.py"))
    )
    package = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(package)
    requirements = package.requires

    for _, value in package.tests.items():
        requirements += value.get("requires", [])

    requirements.remove("python-3.7")
    return requirements


def main(fix_on_error=True):
    for requirement in get_requirements():
        try:
            return_value = subprocess.call(
                ["rez", "pip", "-i", requirement, "--python-version", "3.7"]
            )
        except FileNotFoundError:
            print("REZ could not be found on you system")
            return

        if return_value == 1 and fix_on_error:
            fix_rez_pip()
            main(False)
            return


if __name__ == "__main__":
    main()
