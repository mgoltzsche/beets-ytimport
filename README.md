# beets-ytimport

A [Beets](https://github.com/beetbox/beets) plugin to download audio from [Youtube](https://www.youtube.com/) and import it into your library.

Differences compared to the [ydl plugin](https://github.com/vmassuchetto/beets-ydl):
* Supports downloading liked songs into your Beets library (using [ytmusicapi](https://github.com/sigma67/ytmusicapi)).
* Stores m4a files instead of mp3 to avoid re-encoding lossy audio (which would decrease quality).
* Uses [yt-dlp](https://github.com/yt-dlp/yt-dlp) instead of [ytdl](https://github.com/ytdl-org/youtube-dl) to download the audio files.

## Installation

```sh
python3 -m pip install beets-ytimport ytmusicapi yt-dlp slugify
```

## Configuration

Enable the plugin and add a `ytimport` section to your Beets `config.yaml` as follows:
```yaml
plugins:
  - ytimport

ytimport:
  directory: /path/to/youtube/cache # required
  import: true
  likes: false
  max_likes: 50
  set: 'mykey=myvalue'
  auth_headers: /path/to/your/http/headers
  min_length: 60 # min track length in seconds
  max_length: 7200 # max track length in seconds
  split_tracks: false
  group_albums: false
```

For more information, see [CLI](#cli).

## Usage

Once you enabled the `ytimport` plugin within your Beets configuration, you can download your liked songs from Youtube and import them into your Beets library as follows:
```sh
beet ytimport --likes --max-likes 1500
```

Please note that the command prompts you for Google authentication, unless you specified the `auth_headers` option within your Beets configuration file pointing to a file containing HTTP headers (to get the HTTP headers, see [here](https://ytmusicapi.readthedocs.io/en/stable/setup/browser.html#copy-authentication-headers)).
Import auto-tagger prompts can be disabled by specifying the `-q` option.
You can interrupt and continue or repeat the command to synchronize likes from your Youtube account(s) into your Beets library incrementally.

To download a particular track, run:
```sh
beet ytimport --no-likes https://www.youtube.com/watch?v=hC8CH0Z3L54
```

### CLI

```
Usage: beet ytimport [options]

Options:
  -h, --help            show this help message and exit
  --directory=DIR       directory to download Youtube files to
  --auth-headers=FILE   path to a file containing the HTTP headers of an
                        authenticated POST request to music.youtube.com,
                        copied from your browser's development tool
  --likes               download liked songs
  --no-likes            don't download liked songs
  --max-likes=LIKES     maximum number of likes to obtain
  --split-tracks        split tracks by chapter
  --no-split-tracks     don't split tracks
  --group-albums        import split tracks as albums
  --no-group-albums     don't import split tracks as albums
  --import              import downloaded songs into beets
  --no-import           don't import downloaded songs into beets
  --set=KEY=VALUE       set a field on import, using KEY=VALUE format
  --min-length=SECONDS  minimum track length in seconds
  --max-length=SECONDS  maximum track length in seconds
  -q, --quiet           don't prompt for input when importing
  --pretend             don't import but print the files when importing
```

## Development

Run the unit tests (containerized):
```sh
make test
```

Run the e2e tests (containerized):
```sh
make test-e2e
```

To test your plugin changes manually, you can run a shell within a Beets docker container as follows:
```sh
make beets-sh
```

For testing purposes the Beets library is written to `./data`.
