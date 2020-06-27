from bs4 import BeautifulSoup
from html import parser

from datetime import datetime
from dateutil import parser
import time
import os

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import urllib.request

import mysql.connector
from mysql.connector import errorcode

ERR_SHORT = 1
ERR_LONG = 3
MAX_ERRORS = 3
NULL_VALUE = 'NULL'

class Album:
    def __init__(self, data):
        for key in data:
            val = data[key]
            if isinstance(val, str):
                val = val.strip()
            setattr(self, key, val)

def writelog(*msg):
    try:
        out = ' '.join(str(i) for i in msg)+'\n'
        print(out, end='')
    except Exception:
        print('    ERROR Unexpected error, unable to log.')

def get_db():
    db = mysql.connector.connect(user='root', passwd='rootuser', database='test_collection')
    return db, db.cursor()

def close_db(db, cursor):
    db.close()
    cursor.close()

def get_http_headers():
    return {'User-Agent': 'Chrome/44.0.2403.157'}

def get_browser():
    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Chrome(
        options=options,
        executable_path=os.path.abspath('chromedriver')
    )
    driver.set_page_load_timeout(30)
    return driver

def restart_browser(err=''):
    writelog('    BROWSER ERROR', err)
    time.sleep(1)

def get_sitemaps():
    return ['urls/sitemap-{}.txt'.format(i) for i in range(80, 141)]

def without_visited_urls(cursor, sitemap, urls):
    entry_query = "SELECT url FROM logs WHERE sitemap = \"{}\"".format(sitemap)
    cursor.execute(entry_query)
    prev_urls = [e[0] for e in cursor.fetchall()]
    return [e for e in urls if e not in prev_urls]

def parse_sitemaps(cursor, sitemap):
    with open(sitemap, 'rt') as fobj:
        urls = []
        for line in fobj:
            urls.append(line.strip())
        return without_visited_urls(cursor, sitemap, urls)

def get_html(browser, url):
    errors = 0
    while errors < 3:
        with urllib.request.urlopen(url) as response:
            try:
                html = response.read().decode('utf-8')

                print(html)

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

def to_int(text):
    return int(text) if text.strip() else 0

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
        year = parser.parse(text).year
    except Exception as err:
        year = ''
        writelog('    PARSE ERROR', element, err)
    return year

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
            'year': select_date(tree, '.release-date span'),
            'duration': select(tree, '.duration span'),
            'genre': select_list(tree, '.genre a'),
            'styles': select_list(tree, '.styles a')
        })
    except Exception as err:
        writelog('    PARSE ERROR', url, err)
    else:
        return album

def store_format(query, *args):
    vals = []
    for arg in args:
        if not arg:
            val = NULL_VALUE
        else:
            val = '"{}"'.format(arg)
        vals.append(val)
    vals = tuple(vals)
    return query.format(*vals)

def store(db, cursor, album, sitemap):
    try:
        dml = "INSERT INTO `albums` "\
                "(`artist`, `title`, `url`, `cover`, `artist_url`, "\
                "`critic_rating`, `user_rating_count`, `user_rating`, "\
                "`year`, `duration`) VALUES "\
                "({}, {}, {}, {}, {}, {}, {}, {}, {}, {})"
        query = store_format(
            dml,
            album.artist,
            album.title,
            album.url,
            album.cover,
            album.artist_url,
            album.critic_rating,
            album.user_rating_count,
            album.user_rating,
            album.year,
            album.duration
        )
        cursor.execute(query)

        album_id = cursor.lastrowid
        subdml = "INSERT INTO `genres` "\
            "(`genre`, `album_id`) VALUES "\
            "(\"{}\", \"{}\")"
        subqueries = [subdml.format(g, album_id) for g in album.genre]
        for subquery in subqueries:
            cursor.execute(subquery)

        subdml = "INSERT INTO `styles` "\
            "(`style`, `album_id`) VALUES "\
            "(\"{}\", \"{}\")"
        subqueries = [subdml.format(s, album_id) for s in album.styles]
        for subquery in subqueries:
            cursor.execute(subquery)

        logdml = "INSERT INTO `logs` "\
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
    sitemaps = get_sitemaps()[1:2]

    for sitemap in sitemaps:
        urls = parse_sitemaps(cursor, sitemap)
        for url in urls:
            html = get_html(browser, url)
            album = parse(url, html)
            store(db, cursor, album, sitemap)

    close_db(db, cursor)
    browser.quit()
    print('Process complete.  Exiting.')

if __name__ == '__main__':
    run()
