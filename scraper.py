#!/usr/bin/python3

import argparse
import urllib3
import logging
from time import sleep
from sys import exit
from bs4 import BeautifulSoup as bs

DEFAULT_URL = "https://www.azlyrics.com"
DEFAULT_ARTIST = "abba"
DEFAULT_SONG = "mammamia"
DEFAULT_FORMAT = "{}/{}"
URL_FORMAT_1 = "{}/lyrics/{}/{}.html"
URL_FORMAT_2 = "{}/{}/{}.html"

# Songs available by artist: URL/{First letter of artist/group}/{name of artist/group}.html
# Song lyrics: URL/lyrics/{name of artist/group}/{name of song}.html

def init_argparse():
    global ARGS
    parser = argparse.ArgumentParser(description='Scrape supplied web pages.')
    parser.add_argument(
            '-u',
            dest='url',
            type=str,
            default=DEFAULT_URL,
            help='url for web page to be scraped.',
    )
    parser.add_argument(
            '-q',
            dest='quiet',
            action='store_true',
            help='supress output',
    )
    parser.add_argument(
            '-a',
            dest='artist',
            type=str,
            default=DEFAULT_ARTIST,
            help='Artist that made the song(s).',
    )
    parser.add_argument('-s',
            dest='songs',
            type=str,
            nargs='+',
            default=[DEFAULT_SONG],
            help='Songs which lyrics are desired.',
    )
    parser.add_argument('-o',
            dest='output',
            type=str,
            help='Specify output file.',
    )

    ARGS = parser.parse_args()

def init_logger():
    logging.basicConfig(filename='scrape.log')
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger(__name__).setLevel(logging.INFO)

def init_urls():
    ret = []
    for song in ARGS.songs:
        ret.append(URL_FORMAT_1.format(ARGS.url, ARGS.artist, song))
    return ret

def scrape(urls):
    for (i, url) in enumerate(urls):
        logging.getLogger(__name__).info('Attempting to scrape {}'.format(url))
        try:
            http = urllib3.PoolManager(retries=False)
            response = http.request('GET', url)
        except Exception as e:
            logging.getLogger('urllib3').error(e)
            exit(-1)

        if response.status != 200:
            logging.getLogger(__name__).warning('Exited with status code: {}'.format(response.status))
            logging.getLogger(__name__).warning(response.headers)
            exit(1)

        handle_data(response.data, url)

        if i < (len(urls) - 1):
            sleep(10) # could possibly be smaller but don't want ip ban.

# TODO Ensure that only ascii words are in the result.
def handle_data(data, url):
    d = data.decode('utf-8')    # TODO make more general. Look for encoding in document.
    soup = bs(d, 'html.parser')
    lyrics = soup.body.find(bs_filter)

    ret = ''.join(lyrics.strings).strip()

    try:
        with open(ARGS.output, 'a') as f:
            f.write(url + '\n')
            f.write(ret)
    except Exception as e:
        logging.getLogger(__name__).error(e)

    if not ARGS.quiet:
        print(ret)

# Lyrics are held by an anonymous div tag. (azlyrics)
def bs_filter(tag):
    return not (tag.has_attr('class') or tag.has_attr('id')) and tag.name == 'div'

if __name__ == "__main__":
    init_argparse()
    init_logger()
    urls = init_urls()
    scrape(urls)
