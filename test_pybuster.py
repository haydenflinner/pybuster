from .pybuster import run, Result

def test_run():
    url = 'http://www.google.com/'
    good = 'robots.txt'
    bad = 'fail.txt'
    results = run(url=url, word_list=[good] + [bad])
    assert Result(url + good, True, 200) in results
    assert len(results) == 1
    for result in results:
        assert url + bad not in result.url
