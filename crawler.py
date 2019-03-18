from bs4 import BeautifulSoup
from html import parser
import requests
from urllib import request
from random import random
import time
import os

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

import mysql.connector
from mysql.connector import errorcode

ERR_SHORT = 1
ERR_LONG = 3
MAX_ERRORS = 3

BROWSER = None


class Album:
    def __init__(self, data):
        for key in data:
            setattr(self, key, data[key].strip() if isinstance(data[key], str) else data[key])


def writelog(*msg):
    with open('log.txt', 'at') as fobj:
        try:
            out = ' '.join(str(i) for i in msg)+'\n'
            print(out, end='')
            fobj.write(out)
        except Exception as err:
            print('    ERROR Unexpected error, unable to log.')


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
                writelog('Connected to', res.geturl())
                return res
            else:
                raise ValueError('Result is not a web page')
        except Exception as err:
            error_counter += 1
            writelog('    URL ERROR', url, err)
            time.sleep(retry_time)


def get_browser():
    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Chrome(
        chrome_options=options,
        executable_path=os.path.abspath('chromedriver')
    )
    driver.set_page_load_timeout(30)
    return driver


def restart_browser(err=''):
    global BROWSER
    writelog('    BROWSER ERROR', err)
    # BROWSER.quit()
    time.sleep(15)
    # BROWSER = get_browser()


def get_sitemaps():
    return [
        'https://www.allmusic.com/sitemaps/sitemap-'+str(i)+'.xml' for i in range(80, 141)
    ]


def parse_sitemaps(sitemap):
    res = connect(sitemap)
    tree = BeautifulSoup(res, 'lxml')
    return [loc.get_text() for loc in tree.find_all('loc')]


def get_html(url):
    global BROWSER
    errors = 0
    while errors < 3:
        try:
            BROWSER.get(url)
            html = BROWSER.page_source
        except Exception as err:
            errors += 1
            restart_browser(err)
        else:
            writelog('Connected to', url)
            return html


def select(tree, element):
    try:
        text = tree.select(element)[0].get_text().replace('\"', '')
    except Exception as err:
        text = ''
        writelog('    PARSE ERROR', element, err)
    return text


def select_attrib(tree, element, attrib):
    try:
        text = tree.select(element)[0][attrib]
    except Exception as err:
        text = ''
        writelog('    PARSE ERROR', element, err)
    return text


def select_list(tree, element):
    try:
        tags = [a.get_text().replace('\"', '') for a in tree.select(element)]
    except Exception as err:
        tags = []
        writelog('    PARSE ERROR', element, err)
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
        writelog('    PARSE ERROR', url, err)
    else:
        return album


def store(db, cursor, album, i):
    try:
        # INSERT INTO `albums` (`album_artist`, `album_title`, `album_url`, `created_at`, `updated_at`) VALUES ('Yellow Swans', 'Going Places', 'goingplaces.com', '2019-03-14 03:37:45', '2019-03-14 03:37:45')
        dml = "INSERT INTO `albums` "\
                "(`album_artist`, `album_title`, `album_url`, `album_cover`, `album_artist_url`, "\
                "`critic_rating`, `user_rating_count`, `user_rating`, "\
                "`release_date`, `duration`, `genre`) VALUES "\
                "(\"{}\", \"{}\", \"{}\", \"{}\", \"{}\", \"{}\", \"{}\", \"{}\", \"{}\", \"{}\", \"{}\")"
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

        album_id = cursor.lastrowid
        subdml = "INSERT INTO `styles` "\
            "(`style`, `album_id`) VALUES "\
            "(\"{}\", \"{}\")"
        subqueries = [subdml.format(s, album_id) for s in album.styles]
        for subquery in subqueries:
          cursor.execute(subquery)

        db.commit()
        writelog('  Stored item', i, album.album_url)
    except Exception as err:
        writelog('    STORE ERROR item', i, err)


def run():
    global BROWSER
    BROWSER = get_browser()
    db, cursor = get_db()
    sitemaps = get_sitemaps()[2:4]
    for sitemap in sitemaps:
        urls = parse_sitemaps(sitemap)
        for i, url in enumerate(urls):
            # TODO change based on where last left off
            if i >= 0:
                html = get_html(url)
                album = parse(url, html)
                store(db, cursor, album, i)
    close_db(db, cursor)
    BROWSER.quit()


if __name__ == '__main__':
    run()

