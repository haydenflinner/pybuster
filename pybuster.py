#!/usr/bin/env python3
""" Module for dirbusting a URL. """

import sys
from datetime import timedelta
from tornado import httpclient, gen, ioloop, queues

WORD_LIST = open('wordlist.txt').read().splitlines()
HITS = [200, 204, 301, 302, 307, 403] # 403 not in gobuster

@gen.coroutine
def decide_url(url, override=None):
    """Try fetching the page at `url` and report whether we believe it was there or not.

    Returns True if response code was in `HITS`. False otherwise."""

    returning = False
    try:
        response = yield httpclient.AsyncHTTPClient().fetch(url, raise_error=False, validate_cert=False)
        returning = response.code in HITS
    except Exception as e:
        print('Exception: %s %s' % (e, url))
        returning = False

    if returning and __name__ == '__main__':
        print("{} | {}".format(url, response.code))

    # Support custom handling of edge cases, like handling proxies that always return a 200 if the host is dead.
    returning = override(response=response, url=url, returning=returning) if override else returning

    raise gen.Return(returning)


@gen.coroutine
def bust_url(url, threads=10):
    """ Runs a dirbuster operation on a root URL. Wordlist is pulled from global `WORD_LIST`."""

    q = queues.Queue()
    _ = [q.put(u) for u in buster_list(url)]

    # Wildcard check
    response = yield httpclient.AsyncHTTPClient().fetch(url + '/392392392lol', raise_error=False, validate_cert=False)
    if response.code in HITS:
        if __name__ == '__main__':
            print('Wildcard response found. Exiting...')
            sys.exit(2)
        return


    # Used to be sure we don't hit the same URL twice
    fetching, fetched, results = set(), set(), []

    # Set up our async workers...
    @gen.coroutine
    def process_url():
        """ Fetches a URL, does book-keeping to be sure the URL doesn't get attempted again. """
        current_url = yield q.get()
        try:
            if current_url in fetching:
                return

            fetching.add(current_url)
            decision = yield decide_url(current_url)
            fetched.add(current_url)

            if decision:
                results.append(current_url)

        finally:
            q.task_done()

    @gen.coroutine
    def worker():
        while True:
            yield process_url()


    # Start workers, then wait for the work queue to be empty.
    _ = [worker() for _ in range(threads)]
    yield q.join(timeout=timedelta(seconds=300))

    assert fetching == fetched
    return results


def buster_list(root):
    """ From root url `root`, creates a list of URLs to dirbust. """
    root += '/' if not root.endswith('/') else ''
    return [root + x for x in WORD_LIST]


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Root URL (http://example.com) required as argument.')
        sys.exit(1)
    ioloop.IOLoop.current().run_sync(lambda: bust_url(sys.argv[1]))
