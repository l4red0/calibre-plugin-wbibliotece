#!/usr/bin/env python3
# vim:fileencoding=UTF-8:ts=4:sw=4:sta:et:sts=4:ai
import re
import copy
import datetime
import urllib.request
import urllib.parse
import urllib.error
import urllib.request
import urllib.error
import urllib.parse
import http.cookiejar
import socket

import lxml.html

from calibre.ebooks.metadata.book.base import Metadata
from calibre.utils.date import utc_tz

URL_SCHEME_TITLE = 'https://w.bibliotece.pl/search/?q=t%3A{title}'
URL_SCHEME_TITLE_AUTHORS = 'https://w.bibliotece.pl/search/?q=o%3A{authors}+t%3A{title}'
URL_SCHEME_ISBN = 'https://w.bibliotece.pl/search/?q=isbn%3A+{isbn}'

AUTHORS_JOIN_DELIMETER = '+'
AUTHORS_SPLIT_DELIMETER = '+'
SKIP_AUTHORS = ('Unknown', 'Nieznany')


class Parser():
    def __init__(self, plugin, log, timeout):
        self.plugin = plugin
        self.log = log
        self.timeout = timeout
        self.cj = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.cj))
        urllib.request.install_opener(self.opener)
        self.login()

    @property
    def prefs(self):
        return self.plugin.prefs

    def download_page(self, url):
        try:
            resp = urllib.request.urlopen(url, timeout=self.timeout)
            self.log.info('INFO: Download complete: ' + url)
            return resp
        except urllib.error.URLError as e:
            self.log.error('ERROR: Download failded: ' + url)
            self.log.exception(e)
            return
        except socket.timeout as e:
            self.log.exception(e)
            self.log.error(
                'ERROR: Download failded, request timed out: ' + url)
            return

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

    def login(self):
        pass

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
        resp = self.download_page(url)
        if not resp:
            return

        self.log.info('INFO: Parsing book page')

        tree = lxml.html.parse(resp)
        root = tree.getroot()
        book_tag = root.find('.//*[@id="work"]')
        if self.prefs['title']:
            book_title = root.find('.//*[@id="work"]//div//div//div//div//div/h1/span[@class="main-title"]').text_content().strip()
            self.log.info('book_title', book_title)
        else:
            book_title = self.title
        if self.prefs['authors']:
            book_authors = root.xpath( './/*[@id="work"]//div//div//div//table//div[@itemprop="creator"]')
            if book_authors:
                book_authors = book_authors[0].text_content().partition('(')[0].strip()
                book_authors = self.get_authors(book_authors, name_reversed=True)
        else:
            book_authors = self.authors
        mi = Metadata(book_title, book_authors)
        if self.prefs['pubdate']:
            tag = root.xpath(
                './/*[@id="work"]//div//div//div//table//th[starts-with(text(),"Wyd. w latach:")]//following-sibling::td')
            if tag:
                tag = tag[0].text_content().strip()
                tag = re.search(r"\b\d{4}\b", tag).group()
                mi.pubdate = datetime.datetime(int(tag), 1, 1, tzinfo=utc_tz)
                self.log.info('mi.pubdate', mi.pubdate)
        if self.prefs['comments']:
            tagComments = root.xpath('.//*[@id="work"]//div//div//div//table//tr[@class="summary"]//div[contains(@class, "summary-preview")]')
            if tagComments:
                tagComments = tagComments[0].text_content()
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

            # Category as tag
            cat = root.xpath(
                './/*[@class="spreadme-product"]/span[starts-with(text(),"Kategoria:")]/following-sibling::span')
            cat = [s.text_content().strip() for s in cat]

            # Genre as tag
            gen = root.xpath(
                './/*[@class="spreadme-product"]/span[starts-with(text(),"Gatunek:")]/following-sibling::span')
            gen = [s.text_content().strip() for s in gen]

            if tag:
                mi.tags = tag
            if cat:
                mi.tags = mi.tags + cat
            if gen:
                mi.tags = mi.tags + gen[0].split("/")
        if self.prefs['series']:
            tag = root.xpath('.//*[@id="work"]//div//div//div//table//th[starts-with(text(),"Wydane w seriach:")]//following-sibling::td//span')
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
        resp = self.download_page(url)
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
