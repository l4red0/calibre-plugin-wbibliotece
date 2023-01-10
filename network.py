#!/usr/bin/env python3
import http.cookiejar
import urllib.request
import urllib.error

class Network:
    def __init__(self, timeout, log):
        self.timeout = timeout
        self.log = log
        self.cj = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cj))
        urllib.request.install_opener(self.opener)


    def download_page(self, url: str):
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
