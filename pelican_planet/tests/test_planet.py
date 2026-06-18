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


from collections import OrderedDict
from pathlib import Path
from ssl import CertificateError

import feedparser

from pelican_planet.planet import Planet


def test_get_feeds(datadir):
    feeds = {
        "Le blog à Perceval": "file://%s/perceval.atom.xml" % datadir,
    }
    p = Planet(feeds)
    p.get_feeds()

    assert p._feeds == feeds
    assert len(p._articles) == 7

    titles = [a["title"] for a in p._articles]
    titles.reverse()
    assert titles == [
        "Sloubi 1 !",
        "Sloubi 2 !",
        "Sloubi 3 !",
        "Sloubi 4 !",
        "Sloubi 5 !",
        "Sloubi 324 !",
        "Sloubi 325 !",
    ]


def test_get_multiple_feeds(datadir):

    feeds = OrderedDict(
        [  # Need to guarantee ordering for this test
            ("Le blog à Perceval", "file://%s/perceval.atom.xml" % datadir),
            ("L'auberge à Karadoc", "file://%s/karadoc.atom.xml" % datadir),
        ]
    )
    p = Planet(feeds)
    p.get_feeds()

    assert p._feeds == feeds
    assert len(p._articles) == 10

    titles = [a["title"] for a in p._articles]
    titles.reverse()
    assert titles == [
        "Le gras, c'est la vie",
        "Unagi",
        "Sept cent quarante-quatre",
        "Sloubi 1 !",
        "Sloubi 2 !",
        "Sloubi 3 !",
        "Sloubi 4 !",
        "Sloubi 5 !",
        "Sloubi 324 !",
        "Sloubi 325 !",
    ]


def test_get_multiple_feeds_with_limit(datadir):

    feeds = OrderedDict(
        [  # Need to guarantee ordering for this test
            ("Le blog à Perceval", "file://%s/perceval.atom.xml" % datadir),
            ("L'auberge à Karadoc", "file://%s/karadoc.atom.xml" % datadir),
        ]
    )
    p = Planet(feeds, max_articles_per_feed=2)
    p.get_feeds()

    assert p._feeds == feeds
    assert len(p._articles) == 4

    titles = [a["title"] for a in p._articles]
    titles.reverse()
    assert titles == [
        "Unagi",
        "Sept cent quarante-quatre",
        "Sloubi 324 !",
        "Sloubi 325 !",
    ]


def test_get_no_feeds():

    p = Planet({})
    p.get_feeds()

    assert p._feeds == {}
    assert p._articles == []


def test_get_feeds_404(monkeypatch, datadir):

    def mock_parse(**kwargs):
        return {"status": 404}

    monkeypatch.setattr(feedparser, "parse", mock_parse)

    feeds = {
        "Le blog à Perceval": "file://%s/perceval.atom.xml" % datadir,
    }
    p = Planet(feeds)
    p.get_feeds()

    assert p._articles == []


def test_get_feeds_500(monkeypatch, datadir):

    def mock_parse(**kwargs):
        return {"status": 500}

    monkeypatch.setattr(feedparser, "parse", mock_parse)

    feeds = {
        "Le blog à Perceval": "file://%s/perceval.atom.xml" % datadir,
    }
    p = Planet(feeds)
    p.get_feeds()

    assert p._articles == []


def test_get_feeds_ssl_error(monkeypatch, datadir):

    def mock_parse(**kwargs):
        return {
            "bozo": 1,
            "bozo_exception": CertificateError(
                "hostname 'fedoraplanet.org' doesn't match either of "
                "'*.fedorapeople.org', 'fedorapeople.org'"
            ),
        }

    monkeypatch.setattr(feedparser, "parse", mock_parse)

    feeds = {
        "Le blog à Perceval": "file://%s/perceval.atom.xml" % datadir,
    }
    p = Planet(feeds)
    p.get_feeds()

    assert p._articles == []


def test_write_page(datadir, tmpdir):

    templatepath = Path(datadir.join("planet.md.tmpl").strpath)
    destinationpath = Path(tmpdir.join("planet.md").strpath)
    assert not destinationpath.exists()

    expected = "\n\n\n".join(
        [
            "Some blogs aggregated here.",
            "# Sloubi 325 !",
            "# Sloubi 324 !",
            "# Sloubi 5 !",
            "# Sloubi 4 !",
            "# Sloubi 3 !",
            "# Sloubi 2 !",
            "# Sloubi 1 !",
        ]
    )

    feeds = {
        "Le blog à Perceval": "file://%s/perceval.atom.xml" % datadir,
    }
    p = Planet(feeds)
    p.get_feeds()
    p.write_page(templatepath, destinationpath)

    assert destinationpath.open().read().strip() == expected


def test_write_page_from_multiple_feeds(datadir, tmpdir):

    templatepath = Path(datadir.join("planet.md.tmpl").strpath)
    destinationpath = Path(tmpdir.join("planet.md").strpath)
    assert not destinationpath.exists()

    expected = "\n\n\n".join(
        [
            "Some blogs aggregated here.",
            "# Sloubi 325 !",
            "# Sept cent quarante-quatre",
            "# Sloubi 324 !",
            "# Unagi",
            "# Sloubi 5 !",
            "# Sloubi 4 !",
            "# Sloubi 3 !",
            "# Sloubi 2 !",
            "# Sloubi 1 !",
            "# Le gras, c'est la vie",
        ]
    )

    feeds = {
        "Le blog à Perceval": "file://%s/perceval.atom.xml" % datadir,
        "L'auberge à Karadoc": "file://%s/karadoc.atom.xml" % datadir,
    }
    p = Planet(feeds)
    p.get_feeds()
    p.write_page(templatepath, destinationpath)

    assert destinationpath.open().read().strip() == expected


def test_write_page_from_multiple_feeds_with_total_limit(datadir, tmpdir):

    templatepath = Path(datadir.join("planet.md.tmpl").strpath)
    destinationpath = Path(tmpdir.join("planet.md").strpath)
    assert not destinationpath.exists()

    expected = "\n\n\n".join(
        [
            "Some blogs aggregated here.",
            "# Sloubi 325 !",
            "# Sept cent quarante-quatre",
            "# Sloubi 324 !",
            "# Unagi",
        ]
    )

    feeds = {
        "Le blog à Perceval": "file://%s/perceval.atom.xml" % datadir,
        "L'auberge à Karadoc": "file://%s/karadoc.atom.xml" % datadir,
    }
    p = Planet(feeds)
    p.get_feeds()
    p.write_page(templatepath, destinationpath, max_articles=4)

    assert destinationpath.open().read().strip() == expected


def test_ssl_errors_handling(datadir, tmpdir):

    templatepath = Path(datadir.join("planet.md.tmpl").strpath)
    destinationpath = Path(tmpdir.join("planet.md").strpath)
    assert not destinationpath.exists()

    expected = "\n\n\n".join(
        [
            "Some blogs aggregated here.",
            "# Sept cent quarante-quatre",
            "# Unagi",
            "# Le gras, c'est la vie",
        ]
    )

    feeds = {
        # https://badssl.com/
        # causes: urllib.error.URLError: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED]
        # certificate verify failed: certificate has expired (_ssl.c:1129)>
        "Expired Cert": "https://expired.badssl.com/",
        # broken site should be skipped
        "L'auberge à Karadoc": "file://%s/karadoc.atom.xml" % datadir,
    }

    p = Planet(feeds)
    p.get_feeds()
    p.write_page(templatepath, destinationpath, max_articles=4)

    assert destinationpath.open().read().strip() == expected


def test_media_content_image(datadir):

    feeds = {
        "ForoysktDaily": "file://%s/mastodon.rss.xml" % datadir,
    }
    p = Planet(feeds)
    p.get_feeds()

    assert len(p._articles) == 3

    images = [a["image"] for a in p._articles]
    assert images == [
        "https://files.mastodon.social/media_attachments/files/111/850/122/307/080/898/original/3b8fcb1f07af82f6.png",
        "https://files.mastodon.social/media_attachments/files/111/first.png",
        None,
    ]


def test_channel_image_and_media_content(datadir):

    feeds = {
        "ForoysktDaily": "file://%s/farerskie_kadry.xml" % datadir,
    }
    p = Planet(feeds)
    p.get_feeds()

    assert len(p._articles) == 1

    images = [a["image"] for a in p._articles]
    assert images == [
        "https://farerskiekadry.pl/wp-content/uploads/2026/04/Mjolkarbatur_trap-scaled.jpg",
    ]


def test_http_requests():
    # make sure to run ./test-server.sh before executing this test case

    feeds = {
        "Karadoc": "http://localhost:8088/karadoc.atom.xml",
    }

    p = Planet(feeds)
    p.get_feeds()
    articles = p._articles

    assert (
        len(articles) == 3
    ), "Make sure to run ./test-server.sh before executing this test case"
