import os
import pathlib
import subprocess
import mediafile
from beets.plugins import BeetsPlugin
from beets.dbcore import types
from beets.ui import Subcommand
from optparse import OptionParser
from confuse import ConfigSource, load_yaml
import beetsplug.ytimport.youtube
import beetsplug.ytimport.split

class YtImportPlugin(BeetsPlugin):
    item_types = {
        'like': types.BOOLEAN,
        'yt_id': types.STRING,
        'yt_source': types.STRING,
        'yt_split': types.BOOLEAN,
        'yt_likes': types.INTEGER,
        'yt_dislikes': types.INTEGER,
        'yt_views': types.INTEGER,
        'yt_rating': types.INTEGER,
    }

    @property
    def album_types(self):
        return self.item_types

    def __init__(self):
        super(YtImportPlugin, self).__init__()
        config_file_path = os.path.join(os.path.dirname(__file__), 'config_default.yaml')
        source = ConfigSource(load_yaml(config_file_path) or {}, config_file_path)
        self.config.add(source)
        # Import additional fields from audio file into DB
        for f in self.item_types.keys():
            self.add_media_field(f, mediafile.MediaField(
                mediafile.MP3DescStorageStyle(f),
                mediafile.StorageStyle(f)
            ))

    def commands(self):

        def run_import_cmd(lib, opts, args):
            ytdir = opts.directory
            headers = opts.auth_headers
            if headers:
                f = open(headers, 'r')
                headers = f.read()
                f.close()
            urls = [] + args
            if opts.url_file:
                f = open(opts.url_file, 'r')
                urls += f.readlines()
                f.close()
            singles_dir = os.path.join(ytdir, 'singles')
            albums_dir = os.path.join(ytdir, 'albums')
            pathlib.Path(singles_dir).mkdir(parents=True, exist_ok=True)
            pathlib.Path(albums_dir).mkdir(parents=False, exist_ok=True)
            if opts.likes:
                if opts.url_file or len(args) > 0:
                    raise Exception('Using --likes option in conjunction with --url-file or URL args is not supported!')
                # TODO: mark like as tag within downloaded file already (to be able to distinguish likes also on local reimport)
                print('Obtaining your liked songs from Youtube...')
                if not headers:
                    print('Using interactive authentication. To enable non-interactive authentication, set --auth-headers')
                auth = youtube.login(headers)
                likedIds = youtube.likes(auth, opts.max_likes)
                if len(likedIds) > opts.max_likes:
                    likedIds = likedIds[:opts.max_likes]
                print('Found {:n} liked songs'.format(len(likedIds)))
                urls += ['https://www.youtube.com/watch?v='+id for id in likedIds]
            if not opts.reimport:
                urls = [u for u in urls if not lib.items('comments:'+u)]
            if urls:
                print('Downloading {:n} song(s) to {:s}'.format(len(urls), ytdir))
                h = {}
                # TODO: authenticate download requests.
                # The following makes download requests return a 400 reponse.
                # Maybe a cookiefile with some picked cookies from the headers can be generated?
                #if opts.auth and headers:
                #    h = dict([l.split(': ', 1) for l in headers.strip().split('\n')[1:]])
                youtube.download(urls, ytdir, format=opts.format, min_len=opts.min_length, max_len=opts.max_length, max_len_nochapter=opts.max_length_nochapter, split=opts.split_tracks, like=opts.likes, reimport=opts.reimport, auth_headers=h)
            else:
                print('Nothing to download')
            if opts.do_import:
                print('Importing downloaded songs into beets library')
                cmd = ['beet', 'import', '-pm']
                if opts.reimport:
                    cmd += ['-I']
                else:
                    cmd += ['-i']
                if opts.set:
                    cmd += ['--set', opts.set]
                if opts.quiet:
                    cmd += ['-q']
                if opts.pretend:
                    cmd += ['--pretend']
                if opts.group_albums:
                    subprocess.run(cmd + ['-g', albums_dir])
                    subprocess.run(cmd + ['-s', singles_dir])
                else:
                    subprocess.run(cmd + ['-s', ytdir])
            else:
                print('Skipping import')

        p = OptionParser()
        p.add_option('--directory', type='string', metavar='DIR',
            default=self.config['directory'].get(),
            dest='directory', help='directory to download Youtube files to')
        p.add_option('--format', type='string', metavar='FORMAT',
            default=self.config['format'].get(),
            dest='format', help='preferred file format')
        p.add_option('--auth-headers', type='string', metavar='FILE',
            default=self.config['auth_headers'].get(),
            dest='auth_headers', help="path to a file containing the HTTP headers of an authenticated POST request to music.youtube.com, copied from your browser's development tool")
        p.add_option('--url-file', type='string', metavar='FILE',
            default=self.config['url_file'].get(),
            dest='url_file', help='file containing a download URL per line')
        p.add_option('--likes', action='store_true',
            default=self.config['likes'].get(),
            dest='likes', help='download liked songs')
        p.add_option('--no-likes', action='store_false',
            default=self.config['likes'].get(),
            dest='likes', help="don't download liked songs")
        p.add_option('--max-likes', type='int', metavar='LIKES',
            default=self.config['max_likes'].get(),
            dest='max_likes', help='maximum number of likes to obtain')
        p.add_option('--split-tracks', action='store_true',
            default=self.config['split_tracks'].get(),
            dest='split_tracks', help='split tracks by chapter')
        p.add_option('--no-split-tracks', action='store_false',
            default=self.config['split_tracks'].get(),
            dest='split_tracks', help="don't split tracks")
        p.add_option('--group-albums', action='store_true',
            default=self.config['group_albums'].get(),
            dest='group_albums', help='import split tracks as albums')
        p.add_option('--no-group-albums', action='store_false',
            default=self.config['group_albums'].get(),
            dest='group_albums', help="don't import split tracks as albums")
        p.add_option('--import', action='store_true',
            default=self.config['import'].get(),
            dest='do_import', help='import downloaded songs into beets')
        p.add_option('--no-import', action='store_false',
            default=self.config['import'].get(),
            dest='do_import', help="don't import downloaded songs into beets")
        p.add_option('--reimport', action='store_true',
            default=self.config['reimport'].get(),
            dest='reimport', help="re-download and re-import tracks")
        p.add_option('--no-reimport', action='store_false',
            default=self.config['reimport'].get(),
            dest='reimport', help="don't re-download and re-import tracks")
        p.add_option('--set', type='string', metavar='KEY=VALUE',
            default=self.config['set'].get(),
            dest='set', help='set a field on import, using KEY=VALUE format')
        p.add_option('--min-length', type='int', metavar='SECONDS',
            default=self.config['min_length'].get(),
            dest='min_length', help='minimum track length in seconds')
        p.add_option('--max-length', type='int', metavar='SECONDS',
            default=self.config['max_length'].get(),
            dest='max_length', help='maximum track length in seconds')
        p.add_option('--max-length-nochapter', type='int', metavar='SECONDS',
            default=self.config['max_length_nochapter'].get(),
            dest='max_length_nochapter', help='max track length in seconds when no chapters defined')
        p.add_option('-q', '--quiet', action='store_true',
            default=False,
            dest='quiet', help="don't prompt for input when importing")
        p.add_option('--pretend', action='store_true',
            default=False,
            dest='pretend', help="don't import but print the files when importing")

        c = Subcommand('ytimport', parser=p, help='import songs from Youtube')
        c.func = run_import_cmd
        return [c]
