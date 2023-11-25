# beets-ytimport

A [beets](https://github.com/beetbox/beets) plugin to download audio from [Youtube](https://www.youtube.com/) and import it into your library.

Differences compared to the [ydl plugin](https://github.com/vmassuchetto/beets-ydl):
* Supports downloading liked songs into your beets library (using [ytmusicapi](https://github.com/sigma67/ytmusicapi)).
* Stores m4a files instead of mp3 to avoid re-encoding lossy audio (which would decrease quality).
* Uses [yt-dlp](https://github.com/yt-dlp/yt-dlp) instead of [ytdl](https://github.com/ytdl-org/youtube-dl) to download the audio files.

## Installation

```sh
python3 -m pip install beets-ytimport ytmusicapi yt-dlp
```

## Configuration

Enable the plugin and add a `ytimport` section to your beets `config.yaml` as follows:
```yaml
plugins:
  - ytimport

ytimport:
  directory: /path/to/youtube/cache # required
  import: true
  reimport: false
  # Favour opus over m4a due to higher quality and support for custom tags.
  # (You can get opus or m4a from Youtube and mp3 from SoundCloud.)
  # If your player does not support opus, set 'm4a/bestaudio/best' instead.
  format: bestaudio/best
  likes: false
  max_likes: 15
  set: ''
  auth_headers: /path/to/your/http/headers
  min_length: 60 # 1m; min track length in seconds
  max_length: 7200 # 2h; max track length in seconds
  max_length_nochapter: 600 # 10m; max track length when no chapters defined
  split_tracks: true
  group_albums: true
```

For more information, see [CLI](#cli).

## Usage

Once you enabled the `ytimport` plugin within your beets configuration, you can download your liked songs from Youtube and import them into your beets library as follows:
```sh
beet ytimport --likes --max-likes 3
```

Please note that the command prompts you for Google authentication, unless you specified the `auth_headers` option within your beets configuration file pointing to a file containing HTTP headers (to get the HTTP headers, see [here](https://ytmusicapi.readthedocs.io/en/stable/setup/browser.html#copy-authentication-headers)).
Import auto-tagger prompts can be disabled by specifying the `-q` option.
You can interrupt and continue or repeat the command to synchronize likes from your Youtube account(s) into your beets library incrementally.

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
  --format=FORMAT       preferred file format
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
  --reimport            re-download and re-import tracks
  --no-reimport         don't re-download and re-import tracks
  --set=KEY=VALUE       set a field on import, using KEY=VALUE format
  --min-length=SECONDS  minimum track length in seconds
  --max-length=SECONDS  maximum track length in seconds
  --max-length-nochapter=SECONDS
                        max track length in seconds when no chapters defined
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

To test your plugin changes manually, you can run a shell within a beets docker container as follows:
```sh
make beets-sh
```

A temporary beets library is written to `./data`.
It can be removed by calling `make clean-data`.
