#!/usr/bin/env python3
import re
import copy
import datetime
import urllib.parse
import socket

import lxml.html

from calibre.ebooks.metadata.book.base import Metadata
from calibre.utils.date import utc_tz
from calibre_plugins.wbibliotece.network import Network
from calibre_plugins.wbibliotece.utils import Utils
from calibre_plugins.wbibliotece.metamover import Metamover
from calibre_plugins.wbibliotece.config import URL_SCHEME_TITLE, URL_SCHEME_TITLE_AUTHORS, URL_SCHEME_ISBN, AUTHORS_JOIN_DELIMETER, AUTHORS_SPLIT_DELIMETER, SKIP_AUTHORS


class Parser():
    def __init__(self, plugin, log, timeout):
        self.plugin = plugin
        self.log = log
        self.timeout = timeout
        self.network = Network(timeout, log)
        self.utils = Utils
        self.metamover = Metamover

    @property
    def prefs(self):
        return self.plugin.prefs

    def get_authors(self, authors, name_reversed=False):
        authors_list = []

        for author in authors.split(AUTHORS_SPLIT_DELIMETER):
            if name_reversed:
                tokens = author.split(' ')
                tokens = tokens[1:] + tokens[:1]
                authors_list.append(' '.join(tokens))
            else:
                authors_list.append(author)

        return authors_list

    def get_authors_tokens(self, authors, only_first_author=False):
        authors_tokens = []

        for author in authors:
            for token in author.lower().split(' '):
                if len(token) > 1 and not token.endswith('.'):
                    authors_tokens.append(token)

            if only_first_author:
                break

        return authors_tokens

    def create_authors_string(self, authors, only_first_author=False):
        if only_first_author:
            authors_string = AUTHORS_JOIN_DELIMETER.join(authors[:1])
        else:
            authors_string = AUTHORS_JOIN_DELIMETER.join(authors)

        return authors_string

    def create_search_page_url(self, title, authors_string, with_authors=False):
        if not title:
            return ('', with_authors)

        if authors_string and with_authors:
            url = URL_SCHEME_TITLE_AUTHORS.format(title=urllib.parse.quote(title.encode('utf-8')), authors=urllib.parse.quote(authors_string.encode('utf-8')))
        else:
            with_authors = False
            url = URL_SCHEME_TITLE.format(
                title=urllib.parse.quote(title.encode('utf-8')))

        return (url, with_authors)

    def parse_book_page_t(self, urls, result_queue, lock):
        while True:
            url = ''
            with lock:
                if urls:
                    url = urls.pop()
            if not url:
                return
            mi = self.parse_book_page(url)
            if mi:
                result_queue.put(mi)
            if abort.is_set():
                return

    def parse_book_page(self, url):
        self.log.info('INFO: Downloading book page: ' + url)
        resp = self.network.download_page(url)
        if not resp:
            return

        self.log.info('INFO: Parsing book page')

        tree = lxml.html.parse(resp)
        root = tree.getroot()
        book_tag = root.find('.//*[@id="work"]')
        seriesTag = root.xpath('.//*[@id="work"]//div//div//div//table//th[starts-with(text(),"Wydane w seriach:")]//following-sibling::td//span')

        # Different publisher sources
        publishersTag = root.xpath('.//*[@id="work"]//div//div//div//table//th[starts-with(text(), "Wydawc")]//following-sibling::td//div')
        if not publishersTag:
            publishersTag = root.xpath('.//table[@id="details"]//tr//th[starts-with(text(),"Wydawc")]//following-sibling::td/span[normalize-space(text())]')

        if self.prefs['title']:
            book_title = root.find('.//*[@id="work"]//div//div//div//div//div/h1/span[@class="main-title"]').text_content().strip()
            self.log.info('book_title', book_title)
        else:
            book_title = self.title
        if self.prefs['authors']:
            book_authors = root.xpath('.//*[@id="work"]//div//div//div//table//div[@itemprop="creator"]')
            if book_authors:
                book_authors = book_authors[0].text_content().partition('(')[0].strip()
                book_authors = self.get_authors(book_authors, name_reversed=True)
        else:
            book_authors = self.authors
        mi = Metadata(book_title, book_authors)

        if self.prefs['publisher']:
            tag = publishersTag
            if tag:
                tag = tag[-1].text_content().strip()
                tag = re.sub(r'\(.*?\)', '', tag)
                mi.publisher = tag

        if self.prefs['pubdate']:
            tag = root.xpath('.//*[@id="work"]//div//div//div//table//th[starts-with(text(),"Wyd. w latach:")]//following-sibling::td')
            if tag:
                tag = tag[0].text_content().strip()
                tag = re.search(r"\b\d{4}\b", tag).group()
                mi.pubdate = datetime.datetime(int(tag), 1, 1, tzinfo=utc_tz)
            # If no pubdate in main summary check publishers list for first edition and extract year
            elif publishersTag:
                tag = self.utils.find_earliest_year(publishersTag)
                if tag is not None:
                    mi.pubdate = datetime.datetime(int(tag), 1, 1, tzinfo=utc_tz)

        if self.prefs['comments']:
            tagComments = root.xpath('.//*[@id="work"]//div//div//div//table//tr[@class="summary"]//div[contains(@class, "summary-preview")]')
            if tagComments:
                tagComments = tagComments[0].text_content()
                #METAMOVER
                if self.prefs['metamoverenabled']:
                    tagComments = tagComments + self.metamover.formatMetaMoverComment(root);
                mi.comments = tagComments

        if self.prefs['languages']:
            mi.languages = ['pl']

        if self.prefs['rating']:
            tag = root.xpath('.//*[@id="work"]//div//div//div//table//span[@itemprop="ratingValue"]')
            if tag:
                tag = tag[0].text_content().strip()
                tag = float(tag)
                tag = round(tag, 0)
                mi.rating = tag

        if self.prefs['tags']:
            tag = root.xpath('//a[@class="tag"]/text()')

            # Series as tag
            ser = seriesTag
            ser = [s.text_content().strip() for s in ser]

            # Genre as tag
            gen = root.xpath('.//*[@class="spreadme-product"]/span[starts-with(text(),"Gatunek:")]/following-sibling::span')
            gen = [s.text_content().strip() for s in gen]

            if tag:
                mi.tags = tag
            if ser:
                mi.tags = mi.tags + ser
            if gen:
                mi.tags = mi.tags + gen[0].split("/")

        if self.prefs['series']:
            tag = seriesTag
            if tag:
                tag = tag[0].text_content().strip()
                mi.series = tag

        if self.prefs['isbn']:
            tag = root.xpath('.//*[@id="work"]//div//div//div//table//span[@data-ipub-search="isbn"]')
            if tag:
                tag = tag[0].text_content().strip()
                self.log.info('ISBN: ', tag)
                mi.isbn = tag

        if self.prefs['identifier']:
            identifier_id = re.search(r"\b\d+\b", url).group()
            mi.set_identifier(self.plugin.IDENTIFIER, identifier_id)

        if self.prefs['covers']:
            tag = root.xpath('.//*[@id="work"]//div//div[@id="covers"]//following-sibling::div[@class="box"]//a//@href')
            self.log.info('tag', tag[0])
            for coverImage in tag:
                cover_url = "https:" + coverImage
                if cover_url:
                    mi.has_cover = True
                    self.log.info('INFO: Cover found: ' + cover_url)
                    urls = self.plugin.cached_identifier_to_cover_url('urls')
                    urls.append(cover_url)
                else:
                    mi.has_cover = False
                    self.log.warn('WARN: Cover is not available')
                    self.plugin.cache_identifier_to_cover_url('nocover', True)

        self.log.info('INFO: Parsing book page completed')
        return mi

    def parse_search_page(self, title, authors, with_authors=False, only_first_author=False):
        results = []
        authors = authors or []
        self.authors = copy.copy(authors)
        self.title = title
        authors = [a for a in authors if not a in SKIP_AUTHORS]
        authors_string = self.create_authors_string(authors, only_first_author)
        url, with_authors = self.create_search_page_url(title, authors_string, with_authors)

        self.log.info('INFO: Downloading search page: ' + url)
        resp = self.network.download_page(url)
        if not resp:
            return results

        self.log.info('INFO: Parsing search page')

        tree = lxml.html.parse(resp)
        root = tree.getroot()

        title_tokens = [token for token in title.lower().split(' ') if len(token) > 1]
        authors_tokens = self.get_authors_tokens(authors)
        for book_record in root.xpath('//*[@id="results"]/div'):
            title_match = False
            author_match = not bool(authors_tokens) or not with_authors
            title_tag = root.find('.//div/a[@class="result-title"]')

            book_title = root.find('.//div/a[@class="result-title"]')
            book_authors = root.find('.//*[@id="results"]/div/div/div[@class="result-row result-creators"]/div[@class="content"]')

            if book_authors:
                book_authors = book_authors.text_content().strip().lower()
            if book_title:
                book_title = book_title.text_content().strip().lower()

            for token in title_tokens:
                if token in book_title:
                    title_match = True
                    break
            if not author_match:
                for token in authors_tokens:
                    if token in book_authors:
                        author_match = True
            if title_match and author_match:
                self.log.info('INFO: Match found: title: {}, author(s): {}'.format(
                    book_title, book_authors))
                results.append('https://w.bibliotece.pl' + title_tag.attrib['href'])
            else:
                self.log.warn('WARN: No match: title: {}, author(s): {}'.format(
                    book_title, book_authors))

        if not results and with_authors:
            return self.parse_search_page(title, authors, False)

        self.log.info('INFO: Parsing search page completed')
        return results
