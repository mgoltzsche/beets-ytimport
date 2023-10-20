import setuptools

with open('README.md', 'r') as fh:
    long_description = fh.read()

setuptools.setup(
    name='beets-ytimport',
    version='0.1.1',
    author='Max Goltzsche',
    description='Download Youtube audio and import it into your beets library',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/mgoltzsche/beets-ytimport',
    packages=setuptools.find_packages(),
    include_package_data=True,
    classifiers=[
        'Programming Language :: Python :: 3.6',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
    ],
    install_requires=[
        'beets',
        'ytmusicapi',
        'yt-dlp',
    ]
)
