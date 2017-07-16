from setuptools import setup

setup(name='pybuster',
        version='0.1',
        description='Basic multithreaded directory buster.',
        url='http://github.com/haydenflinner/pybuster',
        author='Hayden Flinner',
        author_email='hayden@flinner.me',
        license='MIT',
        packages=['pybuster'],
        install_requires=[
            'tornado',
            'click',
            ],
        entry_points='''
        [console_scripts]
        pybuster=pybuster:_main
        ''',
        zip_safe=False)
