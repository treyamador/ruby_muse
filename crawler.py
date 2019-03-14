from bs4 import BeautifulSoup
from html import parser
import requests
from urllib import request
import time
import os

from selenium import webdriver
from selenium.webdriver.firefox.options import Options

import mysql.connector
from mysql.connector import errorcode

ERR_SHORT = 1
ERR_LONG = 3
MAX_ERRORS = 3


class Album:
    def __init__(self, data):
        for key in data:
            setattr(self, key, data[key].strip() if isinstance(data[key], str) else data[key])


def writelog(*msg):
    out = ' '.join(str(i) for i in msg)+'\n'
    print(out)
    with open('log.txt', 'at') as fobj:
        fobj.write(out)


def get_db():
    db = mysql.connector.connect(user='root', passwd='root', database='Muse_development')
    return db, db.cursor()


def close_db(db, cursor):
    db.close()
    cursor.close()


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
                writelog('  connected to', res.geturl())
                return res
            else:
                raise ValueError('Result is not a web page')
        except Exception as err:
            error_counter += 1
            writelog('URL ERROR', url, err)
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
        writelog('BROWSER ERROR', err)
    else:
        writelog('  connected to', url)
        return html


def select(tree, element):
    try:
        text = tree.select(element)[0].get_text()
    except Exception as err:
        text = ''
        writelog('PARSE ERROR:', err)
    return text


def select_attrib(tree, element, attrib):
    try:
        text = tree.select(element)[0][attrib]
    except Exception as err:
        text = ''
        writelog('PARSE ERROR:', err)
    return text


def select_list(tree, element):
    try:
        tags = [a.get_text() for a in tree.select(element)]
    except Exception as err:
        tags = []
        writelog('PARSE ERROR:', err)
    return tags


def parse(url, html):
    try:
        tree = BeautifulSoup(html, 'lxml')
        album = Album({
            'album_artist': select(tree, '.album-artist'),
            'album_title': select(tree, '.album-title'),
            'album_url': url,
            'album_cover': select_attrib(tree, '.album-cover img', 'src'),
            'album_artist_url': select_attrib(tree, '.album-artist a', 'href'),
            'critic_rating': select(tree, '.allmusic-rating'),
            'user_rating_count': select(tree, '.average-user-rating-count').replace(',', ''),
            'user_rating': select_attrib(tree, '.average-user-rating', 'class')[-1].split('-')[-1],
            'release_date': select(tree, '.release-date span'),
            'duration': select(tree, '.duration span'),
            'genre': select(tree, '.genre div'),
            'styles': select_list(tree, '.styles a')
        })
    except Exception as err:
        writelog('PARSE ERROR:', err)
    else:
        return album


def store(db, cursor, album):
    try:
        # INSERT INTO `albums` (`album_artist`, `album_title`, `album_url`, `created_at`, `updated_at`) VALUES ('Yellow Swans', 'Going Places', 'goingplaces.com', '2019-03-14 03:37:45', '2019-03-14 03:37:45')
        dml = "INSERT INTO `albums` "\
                "(`album_artist`, `album_title`, `album_url`, `album_cover`, `album_artist_url`, "\
                "`critic_rating`, `user_rating_count`, `user_rating`, "\
                "`release_date`, `duration`, `genre`) VALUES "\
                "('{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}')"
        query = dml.format(
            album.album_artist,
            album.album_title,
            album.album_url,
            album.album_cover,
            album.album_artist_url,
            album.critic_rating,
            album.user_rating_count,
            album.user_rating,
            album.release_date,
            album.duration,
            album.genre
        )
        cursor.execute(query)
        db.commit()
    except Exception as err:
        writelog('STORE ERROR', err)


def run():
    browser = get_browser()
    db, cursor = get_db()
    sitemaps = get_sitemaps()
    for sitemap in sitemaps:
        urls = parse_sitemaps(sitemap)
        for url in urls:
            # TODO remove this fake url
            # url = 'https://www.allmusic.com/album/going-places-mw0001958198'
            # url = 'https://www.allmusic.com/album/psychic-mw0002579381'
            url = 'https://www.allmusic.com/album/reign-in-blood-mw0000191741'
            html = get_html(browser, url)
            album = parse(url, html)
            store(db, cursor, album)
            break
        break
    close_db(db, cursor)


run()
