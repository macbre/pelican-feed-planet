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

from pelican import signals
from pelican.generators import PagesGenerator

from .planet import Planet

# set up logging
import os
import logging

log_level = os.environ.get("PELICAN_LOGLEVEL", "INFO").upper()
logging.basicConfig(level=log_level)


def generate(generator):
    if not isinstance(generator, PagesGenerator):
        return

    config = generator.context

    feeds = config["PLANET_FEEDS"]
    max_articles_per_feed = config.get("PLANET_MAX_ARTICLES_PER_FEED", None)
    max_articles = config.get("PLANET_MAX_ARTICLES", 20)
    max_summary_length = config.get("PLANET_MAX_SUMMARY_LENGTH", None)
    template = Path(config["PLANET_TEMPLATE"])
    destination = Path(config["PLANET_PAGE"])
    rss_destination = config.get("PLANET_RSS_FILE", None)

    logging.info("Will fetch %d feeds and store in %s", len(feeds), destination)

    _planet = Planet(
        feeds,
        max_articles_per_feed=max_articles_per_feed,
        max_summary_length=max_summary_length,
    )
    _planet.get_feeds()
    _planet.write_page(template, destination, max_articles=max_articles)

    logging.info("Planet files saved in %s", destination)

    if rss_destination:
        rss_destination = Path(rss_destination)
        title = config.get("PLANET_RSS_TITLE") or config.get("SITENAME", "Planet")

        _planet.write_feed(
            rss_destination,
            title=title,
            link=config.get("PLANET_RSS_LINK") or config.get("SITEURL", ""),
            description=config.get("PLANET_RSS_DESCRIPTION")
            or config.get("SITESUBTITLE")
            or title,
            max_articles=max_articles,
            feed_url=config.get("PLANET_RSS_URL", None),
        )

        logging.info("Planet RSS feed saved in %s", rss_destination)


def register():
    signals.generator_init.connect(generate)
