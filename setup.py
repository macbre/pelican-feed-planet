# Copyright (c) 2016 - Mathieu Bridon <bochecha@daitauha.fr>
#
# This file is part of pelican-planet
#
# pelican-planet is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# pelican-planet is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with pelican-planet.  If not, see <http://www.gnu.org/licenses/>.


from pathlib import Path

from setuptools import setup, find_packages


def get_requirements(path):
    lines = Path(path).open("r")
    lines = map(lambda l: l.strip(), lines)
    lines = filter(lambda l: bool(l), lines)
    lines = filter(lambda l: not l.startswith("#"), lines)

    return list(lines)


README = Path("README.rst").open().read()
CHANGES = Path("CHANGES.rst").open().read()
REQUIREMENTS = get_requirements("requirements.txt")


setup(
    name="pelican-planet",
    description="Blog aggregator plugin for Pelican",
    long_description="%s\n\n%s" % (README, CHANGES),
    long_description_content_type="text/x-rst",
    version="0.24.0",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
    ],
    python_requires=">=3.9",
    author="Mathieu Bridon",
    author_email="bochecha@daitauha.fr",
    url="https://github.com/macbre/pelican-planet",
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=REQUIREMENTS,
)
