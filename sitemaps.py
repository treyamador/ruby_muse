from bs4 import BeautifulSoup
from pprint import PrettyPrinter
import os

sitemap_hash = {}
sitemap_hash[None] = []
if not os.path.exists('urls/'):
    os.makedirs('urls/')

for sitemap_num in range(80, 141):
    inpath = 'sitemaps/sitemap-{}.xml'.format(sitemap_num)
    with open(inpath, 'rt') as fobj:
        tree = BeautifulSoup(fobj.read(), 'lxml')

    urls = [x.get_text().strip() for x in tree.find_all('loc')]
    outpath = 'urls/sitemap-{}.txt'.format(sitemap_num)
    with open(outpath, 'wt') as fobj:
        fobj.write('\n'.join(urls).strip())

    if len(urls) == 0:
        sitemap_hash[None].append(inpath)
    elif urls[0] in sitemap_hash.keys():
        sitemap_hash[urls[0]].append(inpath)
    else:
        sitemap_hash[urls[0]] = [inpath]

    print('Sitemap', inpath, 'written')

printer = PrettyPrinter()
printer.pprint(sitemap_hash)
for key, value in sitemap_hash.items():
    if key is None:
        print('These sitemaps are empty:', ', '.join(value))
    elif len(value) > 1:
        print('These sitemaps are repeats:', ', '.join(value))
