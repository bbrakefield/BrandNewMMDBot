import asyncio
import logging
from contextlib import closing
import aiohttp # $ pip install aiohttp
import string
import random
import os
import posixpath
from urllib.parse import urlsplit, unquote

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')

current_dir = os.path.dirname(os.path.abspath(__file__))
download_cache = os.path.join(current_dir,'download_cache')


def url2filename(url):
    """Return basename corresponding to url.
    >>> print(url2filename('http://example.com/path/to/file%C3%80?opt=1'))
    fileÀ
    >>> print(url2filename('http://example.com/slash%2fname')) # '/' in name
    Traceback (most recent call last):
    ...
    ValueError
    """
    urlpath = urlsplit(url).path
    basename = posixpath.basename(unquote(urlpath))
    if (os.path.basename(basename) != basename or
                unquote(posixpath.basename(urlpath)) != basename):
        raise ValueError  # reject '%2f' or 'dir%5Cbasename.ext' on Windows
    return basename


def exists_in_cache(filename):
    abs_path = os.path.join(download_cache,url2filename(filename))
    exists =  os.path.isfile(abs_path)
    if not exists:
        logging.info("Doesnt exist in cache {}".format(filename))
    else:
        logging.info("Found in cache {}".format(abs_path))
    return exists

# Only call if exists
def get_cache_path_from_url(filename):
    return os.path.join(download_cache, url2filename(filename))

class DownloadItem:
    def __init__(self,original_url,target_path):
        self.original_url = original_url
        self.target_path = target_path

class ParallelDownloader:
    def __init__(self,urls,target_path,custom_data_on_callback,done_callback):
        self.urls = urls
        self.done_callback = done_callback
        self.downloaded_items = []
        self.target_path = target_path
        self.custom_data_on_callback = custom_data_on_callback

        self.start_downloading()

    @asyncio.coroutine
    def download(self,url, session, semaphore, chunk_size=1 << 15):
        with (yield from semaphore):  # limit number of concurrent downloads
            try:
                filename = url2filename(url)
            except:
                filename = self.random_string()
            filename = os.path.join(self.target_path, filename)
            logging.info('Downloading {} to {}'.format(url,filename))
            response = yield from session.get(url)
            with closing(response), open(filename, 'wb') as file:
                while True:  # save file
                    chunk = yield from response.content.read(chunk_size)
                    if not chunk:
                        break
                    file.write(chunk)
            logging.info('Finished downloading {}'.format(filename))
            self.downloaded_items.append(DownloadItem(url, filename))

        return filename, (response.status, tuple(response.headers.items()))

    def start_downloading(self):
        #self.session = aiohttp.ClientSession()
        #semaphore = asyncio.Semaphore(10)
        #download_tasks = (self.download(url, self.session, semaphore) for url in self.urls)
        #tasks = asyncio.gather(*download_tasks)
        #tasks.add_done_callback(self.on_downloads_complete())
        logging.info("Starting download. {} items in queue".format(len(self.urls)))
        #asyncio.ensure_future(asyncio.gather(*download_tasks))
        with closing(asyncio.get_event_loop()) as loop, \
                closing(aiohttp.ClientSession()) as session:
            semaphore = asyncio.Semaphore(5)
            download_tasks = (self.download(url, session, semaphore) for url in self.urls)
            tasks = asyncio.gather(*download_tasks)
            tasks.add_done_callback(self.on_downloads_complete)
            result = loop.run_until_complete(tasks)

    def on_downloads_complete(self,param):
        print("Downloads complete")

        for item in self.downloaded_items:
            print("Item {} - {}".format(item.original_url, item.target_path))

        self.done_callback(self.urls,self.custom_data_on_callback)

    def random_string(self,size=6, chars=string.ascii_uppercase + string.digits):
        return ''.join(random.choice(chars) for _ in range(size))

#urls = ["http://i.imgur.com/08iFB2K.png", "http://i.imgur.com/td8tJZA.jpg", "http://i.imgur.com/k6NPuYL.jpg", "http://i.imgur.com/rlOqLHj.jpg", "http://i.imgur.com/u1zovcb.jpg"]
#ParallelDownloader(urls, os.path.join(current_dir,'download_cache'), done_callback)