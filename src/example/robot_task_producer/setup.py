import pathlib
import tomllib

from setuptools import setup

CURRENT_DIR = pathlib.Path(__file__).resolve(True).parent.resolve()
pyproject = tomllib.loads((CURRENT_DIR / "pyproject.toml").read_text())

share_relative_dir = pathlib.Path("share")

package_name = pyproject["project"]["name"]

setup(
    name=package_name,
    version=pyproject["project"]["version"],
    packages=[package_name],
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
    ],
    zip_safe=True,
    author=pyproject["project"]["authors"],
    description=pyproject["project"]["description"],
    install_requires=pyproject["build-system"]["requires"],
    entry_points={
        "console_scripts": [
            "robot_task_producer = robot_task_producer.producer:main",
        ]
    },
)
