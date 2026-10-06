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

import feedparser
from pelican.generators import ArticlesGenerator, PagesGenerator

from pelican_planet import generate


def make_generator(cls, context: dict):
    # creating a real generator would require a full Pelican set-up,
    # while all the plugin needs is the generator class and its context
    generator = cls.__new__(cls)
    generator.context = context

    return generator


def test_generate_is_a_noop_for_other_generators(datadir):

    generator = make_generator(ArticlesGenerator, {})
    assert generate(generator) is None


def test_generate(datadir, tmpdir):

    page = Path(tmpdir.join("planet.md").strpath)
    rss = Path(tmpdir.join("output", "planet.rss.xml").strpath)

    generator = make_generator(
        PagesGenerator,
        {
            "PLANET_FEEDS": {
                "Le blog à Perceval": "file://%s/perceval.atom.xml" % datadir,
            },
            "PLANET_TEMPLATE": datadir.join("planet.md.tmpl").strpath,
            "PLANET_PAGE": str(page),
            "PLANET_RSS_FILE": str(rss),
            "PLANET_MAX_ARTICLES": 2,
            "SITENAME": "Kaamelott planet",
            "SITESUBTITLE": "Blogs of the Round Table",
            "SITEURL": "https://example.org",
        },
    )

    generate(generator)

    assert "# Sloubi 325 !" in page.open().read()

    # the parent directory of the feed file is created if needed
    generated = feedparser.parse(rss.open().read())

    assert generated["feed"]["title"] == "Kaamelott planet"
    assert generated["feed"]["link"] == "https://example.org"
    assert generated["feed"]["subtitle"] == "Blogs of the Round Table"

    assert [entry["title"] for entry in generated["entries"]] == [
        "Sloubi 325 !",
        "Sloubi 324 !",
    ]


def test_generate_without_rss_file(datadir, tmpdir):

    page = Path(tmpdir.join("planet.md").strpath)

    generator = make_generator(
        PagesGenerator,
        {
            "PLANET_FEEDS": {
                "Le blog à Perceval": "file://%s/perceval.atom.xml" % datadir,
            },
            "PLANET_TEMPLATE": datadir.join("planet.md.tmpl").strpath,
            "PLANET_PAGE": str(page),
        },
    )

    generate(generator)

    assert "# Sloubi 325 !" in page.open().read()
    assert not Path(tmpdir.join("planet.rss.xml").strpath).exists()
