#!/usr/bin/env python3

from distutils.core import setup

MAJOR_VERSION='0'
MINOR_VERSION='0'
PATCH_VERSION='1'

VERSION = '{}.{}.{}'.format(MAJOR_VERSION, MINOR_VERSION, PATCH_VERSION)

packages = ['sunstone']
package_dir = {p: 'src/' + p for p in packages}

def main():
    setup(
        name = 'sunstone',
        packages = packages,
        package_dir = package_dir,
        version = VERSION,
        description = 'Basic tools to help with location-based code.',
        author = 'Steve Norum',
        author_email = 'sn@drunkenrobotlabs.org',
        url = 'https://github.com/stevenorum/sunstone',
        download_url = 'https://github.com/stevenorum/sunstone/archive/{}.tar.gz'.format(VERSION),
        keywords = ['python','google','gmaps'],
        classifiers = [],
    )

if __name__ == "__main__":
    main()
