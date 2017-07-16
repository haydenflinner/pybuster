#!/usr/bin/env python3
""" Module for dirbusting a URL. """

__author__ = 'Hayden Flinner <hayden@flinner.me>'
__version__ = '0.1.0'

import sys
import logging
from datetime import timedelta
from collections import namedtuple
import click
from tornado import httpclient, gen, ioloop, queues

SUCCESS_CODES = [200, 204, 301, 302, 307, 403] # 403 not in gobuster


@gen.coroutine
def _decide_url(url, success_codes, override=None):
    """Try fetching the page at `url` and report whether we believe it was there or not.

    Returns True if response code was in `SUCCESS_CODES`. False otherwise.
    Pass in an `override` function to override default decision making here."""

    returning = None
    try:
        response = yield httpclient.AsyncHTTPClient().fetch(url, raise_error=False, validate_cert=False)
        returning = Result(url, response.code in success_codes, response.code)
    except Exception as exc:
        logging.exception("%s %s", exc, url)

    if returning and __name__ == '__main__':
        print("{} | {}".format(url, response.code))

    # Support custom handling of edge cases, like handling proxies that always return a 200 if the host is dead.
    returning = override(response=response, url=url, returning=returning) if override else returning

    raise gen.Return(returning)


@gen.coroutine
def bust_url(url, word_list, threads=10, success_codes=SUCCESS_CODES):
    """ Gen.coroutine: Runs a dirbuster operation on a root URL."""

    q = queues.Queue()
    _ = [q.put(u) for u in _buster_list(url, word_list)]

    # Wildcard check
    response = yield httpclient.AsyncHTTPClient().fetch(url + '/l392392392lol', raise_error=False, validate_cert=False)
    if response.code in success_codes:
        logging.error('Wildcard response found. Aborting...')
        if __name__ == '__main__':
            sys.exit(2)
        raise RuntimeError('Wildcard response found.')


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
            result = yield _decide_url(current_url, success_codes)
            fetched.add(current_url)

            if result.hit:
                results.append(result)

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
    raise gen.Return(results)


def _buster_list(root_url, word_list):
    """Creates a list of URLs to dirbust from `root_url`."""
    root_url += '/' if not root_url.endswith('/') else ''
    return [root_url + x for x in word_list]


@click.command()
@click.argument('url')
@click.argument('word-list-file', type=click.File('r'))
@click.option('--threads', default=10)
def _main(url, word_list_file, threads):
    """Main CLI entrypoint for pybuster."""
    print(run(url, word_list_file.read().splitlines()))

def run(url, word_list, threads=10):
    """Runs pybuster with specified arguments and number of threads."""
    return (ioloop.IOLoop.current().run_sync(lambda: bust_url(url, word_list, threads)))

Result = namedtuple('Result', ['url', 'hit', 'response_code'])
class Result:
    """Simple data holder for result information."""
    def __init__(self, url, hit, response_code):
        self.url = url
        self.hit = hit
        self.response_code = response_code

    # Wish I could use a namedtuple for these, but didn't like the page full of un-necessary functions
    # added to the help() page for the module that way.
    __eq__ = lambda self, other: self.url == other.url
    __str__ = lambda self: self.url + " | " + self.response_code
    __repr__ = lambda self: "Result(url={}, hit={}, response_code={}".format(self.url, self.hit, self.response_code)
    __hash__ = lambda self: self.url
