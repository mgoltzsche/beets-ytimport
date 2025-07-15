# beets-ytimport

A [beets](https://github.com/beetbox/beets) plugin to download audio from [Youtube](https://www.youtube.com/) and import it into your library.

Differences compared to the [ydl plugin](https://github.com/vmassuchetto/beets-ydl):
* Supports downloading liked songs into your beets library (using [ytmusicapi](https://github.com/sigma67/ytmusicapi)).
* Uses [yt-dlp](https://github.com/yt-dlp/yt-dlp) instead of [ytdl](https://github.com/ytdl-org/youtube-dl) to download the audio files.
* Prefers to download Opus files, avoiding re-encoding lossy audio (which would decrease quality).

## Installation

```sh
python3 -m pip install beets-ytimport ytmusicapi yt-dlp
```

## Configuration

Enable the plugin and add a `ytimport` section to your beets `config.yaml` as follows:
```yaml
plugins:
  - ytimport

import:
  move: true
# Alternatively, you can declare left-over cover art within the import source dir as clutter:
#clutter:
#  - cover.jpg

ytimport:
  directory: /path/to/youtube/cache # required
  import: true
  reimport: false
  # Prefers opus over m4a due to higher quality and support for custom tags.
  # (You can get opus or m4a from Youtube and mp3 from SoundCloud.)
  # To prefer m4a instead, set 'm4a/bestaudio/best'.
  format: bestaudio/best
  url_file: ''
  likes: false
  max_likes: 15
  set:
    loved: true
  oauth_client_id: ''
  oauth_client_secret: ''
  auth_headers: ''
  cookiefile: path/to/your/cookies
  min_length: 60 # 1m; min track length in seconds
  max_length: 7200 # 2h; max track length in seconds
  max_length_nochapter: 900 # 15m; max track length when no chapters defined
  split_tracks: true
  group_albums: true
  quiet_fallback: skip # optional; alternatively, to import as is, set 'asis'.
```

### Authentication

In case the `likes` option is enabled and no `auth_headers` configured, ytimport prompts for Google authentication which requires OAuth client credentials (`oauth_client_id`, `oauth_client_secret`) to be configured (requres a Google Cloud Console account, see [here](https://ytmusicapi.readthedocs.io/en/stable/setup/oauth.html)).

To configure `auth_headers` specify a path to a file containing HTTP headers (to get the HTTP headers, see [here](https://ytmusicapi.readthedocs.io/en/stable/setup/browser.html#copy-authentication-headers)).

To download premium quality audio, let `cookiefile` point to a file that holds the HTTP cookies for a logged in premium user on music.youtube.com in Netscape format. To create the cookies file, you can use a browser extension, e.g. [cookies.txt](https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/) for Firefox.

For more information, see [CLI](#cli).

## Usage

Once you enabled the `ytimport` plugin within your beets configuration, you can download your liked songs from Youtube and import them into your beets library as follows:
```sh
beet ytimport --likes --max-likes 3
```
Please note that the command prompts you for Google authentication which requires you to have OAuth client credentials configured, unless you specified the `auth_headers` option within your beets configuration file, see [authentication](#authentication).

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
  --url-file=URL        URL/path to a file containing a download URL per line
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
  --quiet-fallback=skip|asis
                        decision in quiet mode when there is no strong match
  --pretend             don't import but print the files when importing
  --cookiefile          path to a file containing the cookies for a logged in
                        user on music.youtube.com in Netscape format
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
