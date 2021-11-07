import pathlib
from typing import List

from setuptools import find_packages, setup

here = pathlib.Path(__file__).parent.resolve()

long_description = (here / "README.rst").read_text(encoding="utf-8")
version = (here / "VERSION").read_text(encoding="utf-8")


def read_reqs(path: str) -> List[str]:
    reqs = (here / path).read_text(encoding="utf-8").split("\n")
    return [req for req in reqs if req]


install_requires = read_reqs(here / "requirements.txt")
test_requires = read_reqs(here / "test_requirements.txt")

print(install_requires)


setup(
    name="justpid",
    version=version,
    description="A simple library for pidfiles support.",
    long_description=long_description,
    long_description_content_type="text/x-rst",
    url="https://github.com",
    author="Szymon Lipiński",
    author_email="mabewlun@gmail.com",
    classifier=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3 :: Only",
        "Topic :: Software Development",
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Utilities",
    ],
    packages=find_packages(),
    python_requires=">=3.6",
    install_requires=install_requires,
    extras_require={"test": test_requires},
    project_urls={
        "Bug Reports": "https://github.com/szymonlipinski/justpid/issues",
        "Source": "https://github.com/szymonlipinski/justpid/",
    },
)
