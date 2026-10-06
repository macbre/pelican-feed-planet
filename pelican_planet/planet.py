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
import logging
import mimetypes
import re
from http.client import HTTPException

from pathlib import Path

from time import mktime

from urllib.error import URLError

from operator import attrgetter

import feedparser
from feedgenerator import Enclosure, Rss201rev2Feed
from jinja2 import Template

from .utils import make_date, make_summary


class FeedError(Exception):
    pass


class Planet:
    def __init__(self, feeds, max_articles_per_feed=None, max_summary_length=None):
        self._feeds = feeds
        self._max_articles_per_feed = max_articles_per_feed
        self._max_summary_length = max_summary_length

        self._articles = []

        self.logger = logging.getLogger(self.__class__.__name__)

    def _get_feed(self, name: str, url: str):
        self.logger.info('Parsing "%s" feed from <%s> ...', name, url)

        try:
            parsed = feedparser.parse(
                url_file_stream_or_string=url,
                agent=self.get_user_agent(),
            )
        except URLError as ex:
            # handle broken SSL certificates
            raise FeedError(f"Could not download {name}'s feed: {str(ex)}")
        except HTTPException as ex:
            # handle HTTP exceptions, e.g. RemoteDisconnected: Remote end closed connection without response
            raise FeedError(
                f"Could not download {name}'s feed: HTTP request to <{url}> failed with {str(ex)}"
            )

        status = parsed.get("status")

        if status is None:
            if parsed["bozo"]:
                raise FeedError(
                    f'Could not download {name}\'s feed: {parsed["bozo_exception"]}'
                )

            if url.startswith("file://"):
                return parsed

        elif status == 404:
            raise FeedError(f"Could not download {name}'s feed: not found")

        elif status < 200 or status > 399:
            raise FeedError(f"Error with {name}'s feed (HTTP status {status})")

        self.logger.info("GET %s HTTP %d", url, status)

        return parsed

    def _get_articles(self, feed: dict, feed_name: str):
        def _get_articles():
            for article in feed.get("entries", []):  # type: dict
                try:
                    updated = make_date(article["updated"])

                    article["updated"] = updated
                    article["timestamp"] = int(mktime(updated.timetuple()))
                    article["summary"] = make_summary(
                        article["summary"], max_words=self._max_summary_length
                    )
                    article["feed_name"] = feed_name

                    # https://docs.python.org/3/library/datetime.html
                    article["date_iso"] = article["date"].strftime(
                        "%Y-%m-%d"
                    )  # e.g. 2002-12-04

                    article["image"] = next(
                        (
                            m["url"]
                            for m in article.get("media_content") or []
                            if m.get("medium") == "image"
                            or (m.get("type") or "").startswith("image/")
                        ),
                        None,
                    )

                    yield article

                # e.g. KeyError - updated
                except KeyError as ex:
                    logging.warning(
                        f"Missing an expected {str(ex)} entry in the artile: {repr(article)}"
                    )

                # e.g. dateutil.parser._parser.ParserError: Unknown string format: Z
                except ValueError as ex:
                    logging.error(
                        f"Error parsing the date: {repr(article['updated'])} - {str(ex)}"
                    )

                except Exception as ex:
                    logging.error(
                        f"Unknown error when parsing {repr(article)} - {str(ex)}",
                        exc_info=True,
                    )
                    raise ex

        articles = sorted(_get_articles(), key=attrgetter("timestamp"), reverse=True)
        articles = articles[: self._max_articles_per_feed]

        return articles

    def get_feeds(self):
        for name, url in self._feeds.items():
            try:
                feed = self._get_feed(name, url)
                articles = self._get_articles(feed, name)
                self._articles.extend(articles)

            except FeedError as ex:
                logging.error(f"Error parsing <{url}> - {str(ex)}", exc_info=True)

    def _get_sorted_articles(self, max_articles=None):
        """
        Returns the aggregated articles, the most recent ones first
        """
        articles = sorted(self._articles, key=attrgetter("timestamp"), reverse=True)
        logging.info(
            f"Fetched {len(articles)} articles (will render up to {max_articles})"
        )

        return articles[:max_articles]

    def write_page(self, template, destination, max_articles=None):
        articles = self._get_sorted_articles(max_articles)

        feeds = [
            # feed name, feed URL, blog URL (protocol + domain)
            (name, url, re.match(r"(file:///|https?://)[^/]+/", url)[0])
            for name, url in self._feeds.items()
        ]
        logging.info(f"Feeds parsed: {len(feeds)}")

        template = Template(template.open().read())
        destination.open(mode="w").write(
            template.render(articles=articles, feeds=feeds)
        )

        # render some information when run in GitHub Actions
        # https://docs.github.com/en/actions/using-workflows/workflow-commands-for-github-actions#setting-a-notice-message
        print(f"::notice::Fetched {len(articles)} articles from {len(feeds)} feeds")

    def write_feed(
        self,
        destination: Path,
        title: str,
        link: str,
        description: str = "",
        max_articles=None,
        feed_url: str = None,
    ):
        """
        Writes the aggregated articles as an RSS 2.0 feed file
        """
        articles = self._get_sorted_articles(max_articles)

        feed = Rss201rev2Feed(
            title=title,
            link=link,
            description=description,
            feed_url=feed_url,
        )

        for article in articles:
            # an RSS item makes no sense without these two
            if not article.get("title") or not article.get("link"):
                logging.warning(
                    f"Skipping an article with no title or link: {repr(article)}"
                )
                continue

            feed.add_item(
                title=article["title"],
                link=article["link"],
                description=article["summary"],
                author_name=article.get("author") or article["feed_name"],
                pubdate=article["updated"],
                # the link to the original article is its permalink
                unique_id=article["link"],
                categories=(article["feed_name"],),
                enclosures=self._get_enclosures(article),
            )

        # the feed is typically written next to the generated website
        destination.parent.mkdir(parents=True, exist_ok=True)

        with destination.open(mode="w", encoding="utf-8") as fp:
            feed.write(fp, "utf-8")

        logging.info(f"Wrote {len(feed.items)} articles to the {destination} RSS feed")

    @staticmethod
    def _get_enclosures(article: dict) -> list:
        """
        Returns the article's image (if any) as a list of RSS enclosures
        """
        image = article.get("image")

        if not image:
            return []

        mime_type, _ = mimetypes.guess_type(image)

        if mime_type is None or not mime_type.startswith("image/"):
            return []

        # we do not know the size of the image without fetching it
        return [Enclosure(url=image, length="0", mime_type=mime_type)]

    @staticmethod
    def get_user_agent() -> str:
        return f"pelican-planet +https://github.com/macbre/pelican-planet"
