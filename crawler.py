from bs4 import BeautifulSoup
from html import parser
import requests
from urllib import request
import time
import os

from selenium import webdriver
from selenium.webdriver.firefox.options import Options

import mysql.connector as mysql
from mysql import errorcode

ERR_SHORT = 1
ERR_LONG = 3
MAX_ERRORS = 3


class Album:
    def __init__(self, data):
        for key in data:
            setattr(self, key, data[key].strip() if isinstance(data[key], str) else data[key])


def get_http_headers():
    version_info = (1, 0, 25)
    __version__ = ".".join(map(str, version_info))
    browser_user_agent = 'superscraper/%s' % __version__
    headers = {'User-Agent': 'Chrome/44.0.2403.157'}
    return headers


def connect(url, max_errors=3, retry_time=10):
    error_counter = 0
    while error_counter < max_errors:
        try:
            req = request.Request(url,
                                  headers=get_http_headers())
            res = request.urlopen(req, timeout=60)
            if res is not None:
                print('  connected to', res.geturl())
                return res
            else:
                raise ValueError('Result is not a web page')
        except Exception as err:
            error_counter += 1
            print('URL ERROR', url, err)
            time.sleep(retry_time)


def get_browser():
    options = Options()
    options.headless = True
    return webdriver.Firefox(options=options, executable_path='geckodriver')
    

def get_sitemaps():
    return [
        'https://www.allmusic.com/sitemaps/sitemap-'+str(i)+'.xml' for i in range(80, 141)
    ]


def parse_sitemaps(sitemap):
    res = connect(sitemap)
    tree = BeautifulSoup(res, 'lxml')
    return [loc.get_text() for loc in tree.find_all('loc')]


def get_html(browser, url):
    try:
        browser.get(url)
        html = browser.page_source
    except Exception as err:
        print('BROWSER ERROR', err)
    else:
        print('  connected to', url)
        return html


def parse(html):
    try:
        tree = BeautifulSoup(html, 'lxml')
        album = Album({
            'album_artist': tree.select('.album-artist')[0].get_text(),
            'album_cover': tree.select('.album-cover img')[0]['src'],
            'album_artist_url': tree.select('.album-artist a')[0]['href'],
            'album_title': tree.select('.album-title')[0].get_text(),
            'critic_rating': tree.select('.allmusic-rating')[0].get_text(),
            'user_rating_count': tree.select('.average-user-rating-count')[0].get_text(),
            'user_rating': tree.select('.average-user-rating')[0]['class'][1].split('-')[-1],
            'release_date': tree.select('.release-date span')[0].get_text(),
            'duration': tree.select('.duration span')[0].get_text(),
            'genre': tree.select('.genre div')[0].get_text(),
            'styles': [a.get_text() for a in tree.select('.styles a')]
        })
    except Exception as err:
        print('PARSE ERROR:', err)
    else:
        print('  parsed album', album.album_title)
        return album


def store(db, album):
    try:
        
        print(album.album_artist)
        print(album.album_cover)
        print(album.album_title)
        print(album.critic_rating)
        print(album.user_rating)
        print(album.user_rating_count)

    except Exception as err:
        print('STORE ERROR', err)
    else:
        print('  stored album', album.album_title)


def run():
    browser = get_browser()
    db = mysql(hostname='localhost', user='user', passwd='password')
    sitemaps = get_sitemaps()
    for sitemap in sitemaps:
        urls = parse_sitemaps(sitemap)
        for url in urls:
            # TODO remove this fake url
            url = 'https://www.allmusic.com/album/going-places-mw0001958198'
            html = get_html(browser, url)
            album = parse(html)
            store(db, album)
            break
        break


run()
