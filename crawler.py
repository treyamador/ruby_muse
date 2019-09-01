from bs4 import BeautifulSoup
from html import parser
import requests
from urllib import request
from random import random
from datetime import datetime
import time
import os

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

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
    with open('log.txt', 'at') as fobj:
        try:
            out = ' '.join(str(i) for i in msg)+'\n'
            print(out, end='')
            fobj.write(out)
        except Exception as err:
            print('    ERROR Unexpected error, unable to log.')


def get_db():
    db = mysql.connector.connect(user='root', passwd='root', database='music_collection')
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
    writelog('    BROWSER ERROR', err)
    time.sleep(15)


def get_sitemaps():
    return [
        'https://www.allmusic.com/sitemaps/sitemap-'+str(i)+'.xml' for i in range(80, 141)
    ]


def parse_sitemaps(cursor, sitemap):
    res = connect(sitemap)
    tree = BeautifulSoup(res, 'lxml')
    urls = [loc.get_text() for loc in tree.find_all('loc')]
    return visited_urls(cursor, sitemap, urls)


def get_html(browser, url):
    errors = 0
    while errors < 3:
        try:
            browser.get(url)
            html = browser.page_source
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


def select_date(tree, element):
    try:
        text = tree.select(element)[0].get_text().replace('\"', '')
        if len(text) == 4:
            date = datetime.strptime(text, '%Y')
        else:
            date = datetime.strptime(text, '%B %d, %Y')
    except Exception as err:
        date = ''
        writelog('    PARSE ERROR', element, err)
    return date


def current_sitemaps(cursor):
  entry_query = "SELECT `sitemap` FROM `log` ORDER BY `id` DESC LIMIT 1"
  cursor.execute(entry_query)
  last_sitemap = cursor.fetchone()
  if last_sitemap is None:
    return get_sitemaps()
  last_sitemap = last_sitemap[0]
  return list(filter(lambda e: e >= last_sitemap, get_sitemaps()))


def visited_urls(cursor, sitemap, urls):
  entry_query = "SELECT url FROM log WHERE sitemap = \"{}\"".format(sitemap)
  cursor.execute(entry_query)
  prev_urls = [e[0] for e in cursor.fetchall()]
  return [e for e in urls if e not in prev_urls]


def parse(url, html):
    try:
        tree = BeautifulSoup(html, 'lxml')
        album = Album({
            'artist': select(tree, '.album-artist'),
            'title': select(tree, '.album-title'),
            'url': url,
            'cover': select_attrib(tree, '.album-cover img', 'src'),
            'artist_url': select_attrib(tree, '.album-artist a', 'href'),
            'critic_rating': select(tree, '.allmusic-rating'),
            'user_rating_count': select(tree, '.average-user-rating-count').replace(',', ''),
            'user_rating': select_attrib(tree, '.average-user-rating', 'class')[-1].split('-')[-1],
            'release_date': select_date(tree, '.release-date span'),
            'duration': select(tree, '.duration span'),
            'genre': select_list(tree, '.genre a'),
            'styles': select_list(tree, '.styles a')
        })
    except Exception as err:
        writelog('    PARSE ERROR', url, err)
    else:
        return album


def store(db, cursor, album, sitemap):
    try:
        dml = "INSERT INTO `album` "\
                "(`artist`, `title`, `url`, `cover`, `artist_url`, "\
                "`critic_rating`, `user_rating_count`, `user_rating`, "\
                "`release_date`, `duration`) VALUES "\
                "(\"{}\", \"{}\", \"{}\", \"{}\", \"{}\", \"{}\", \"{}\", \"{}\", \"{}\", \"{}\")"
        query = dml.format(
            album.artist,
            album.title,
            album.url,
            album.cover,
            album.artist_url,
            album.critic_rating,
            album.user_rating_count,
            album.user_rating,
            album.release_date,
            album.duration
        )
        cursor.execute(query)

        album_id = cursor.lastrowid
        subdml = "INSERT INTO `genre` "\
            "(`genre`, `album_id`) VALUES "\
            "(\"{}\", \"{}\")"
        subqueries = [subdml.format(g, album_id) for g in album.genre]
        for subquery in subqueries:
          cursor.execute(subquery)

        subdml = "INSERT INTO `style` "\
            "(`style`, `album_id`) VALUES "\
            "(\"{}\", \"{}\")"
        subqueries = [subdml.format(s, album_id) for s in album.styles]
        for subquery in subqueries:
          cursor.execute(subquery)

        logdml = "INSERT INTO `log` "\
            "(`sitemap`, `url`) VALUES "\
            "(\"{}\", \"{}\")"
        logquery = logdml.format(sitemap, album.url)
        cursor.execute(logquery)

        db.commit()
        writelog('  Stored item', sitemap, album.url)
    except Exception as err:
        writelog('    STORE ERROR item', sitemap, err)


def run():
    browser = get_browser()
    db, cursor = get_db()
    sitemaps = current_sitemaps(cursor)
    for sitemap in sitemaps[:10]:
        urls = parse_sitemaps(cursor, sitemap)
        for i, url in enumerate(urls):
          html = get_html(browser, url)
          album = parse(url, html)
          store(db, cursor, album, sitemap)
    close_db(db, cursor)
    browser.quit()


if __name__ == '__main__':
    run()

