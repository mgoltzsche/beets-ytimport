import os
import re
import pathlib
import mediafile
import requests
from beets.plugins import BeetsPlugin
from beets.dbcore import types
from beets.ui import Subcommand
from beets.ui import _store_dict
from beets.ui.commands import import_files
from beets import config
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
                add_urls = []
                if re.match(r'^https?://', opts.url_file):
                    add_urls = requests.get(opts.url_file).text.strip('\n').split('\n')
                else:
                    f = open(opts.url_file, 'r')
                    add_urls = f.readlines()
                    f.close()
                urls += add_urls
                self._log.info('Found {:n} URLs within URL file', len(add_urls))
            singles_dir = os.path.join(ytdir, 'singles')
            albums_dir = os.path.join(ytdir, 'albums')
            pathlib.Path(singles_dir).mkdir(parents=True, exist_ok=True)
            pathlib.Path(albums_dir).mkdir(parents=False, exist_ok=True)
            if opts.likes:
                if opts.url_file or len(args) > 0:
                    raise Exception('Using --likes option in conjunction with --url-file or URL args is not supported!')
                # TODO: mark like as tag within downloaded file already (to be able to distinguish likes also on local reimport)
                self._log.info('Obtaining your liked songs from Youtube...')
                if not headers:
                    self._log.info('Using interactive authentication. To enable non-interactive authentication, set --auth-headers')
                auth = youtube.login(headers)
                likedIds = youtube.likes(auth, opts.max_likes)
                if len(likedIds) > opts.max_likes:
                    likedIds = likedIds[:opts.max_likes]
                self._log.info('Found {:n} liked songs', len(likedIds))
                urls += ['https://www.youtube.com/watch?v='+id for id in likedIds]
            if not opts.reimport:
                unknown_urls = [u for u in urls if not lib.items('comments:'+u)]
                self._log.info('Ignoring {:n} known URLs', len(urls)-len(unknown_urls))
                urls = unknown_urls
            if urls:
                self._log.info('Downloading {:n} song(s) to {:s}', len(urls), ytdir)
                h = {}
                # TODO: authenticate download requests.
                # The following makes download requests return a 400 reponse.
                # Maybe a cookiefile with some picked cookies from the headers can be generated?
                #if opts.auth and headers:
                #    h = dict([l.split(': ', 1) for l in headers.strip().split('\n')[1:]])
                youtube.download(urls, ytdir, format=opts.format, min_len=opts.min_length, max_len=opts.max_length, max_len_nochapter=opts.max_length_nochapter, split=opts.split_tracks, like=opts.likes, reimport=opts.reimport, auth_headers=h)
            else:
                self._log.info('Nothing to download')
            if opts.do_import:
                self._log.info('Importing downloaded songs into beets library')
                if opts.group_albums:
                    self._import_files(lib, opts, albums_dir, False)
                    self._import_files(lib, opts, singles_dir, True)
                else:
                    self._import_files(lib, opts, ytdir, True)
            else:
                self._log.info('Skipping import')

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
            default={k: str(v.get()) for k,v in self.config['set'].items()},
            action="callback",
            callback=_store_dict,
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
        p.add_option('--quiet-fallback', type='string', metavar='skip|asis',
            default=('quiet_fallback' in self.config and self.config['quiet_fallback'].get() or None),
            dest='quiet_fallback', help='decision in quiet mode when there is no strong match')
        p.add_option('--pretend', action='store_true',
            default=False,
            dest='pretend', help="don't import but print the files when importing")

        c = Subcommand('ytimport', parser=p, help='import songs from Youtube')
        c.func = run_import_cmd
        return [c]

    def _import_files(self, lib, opts, src_dir, singletons):
        user_incremental = config['import']['incremental'].get()
        user_resume = config['import']['resume'].get()
        user_move = config['import']['move'].get()
        user_quiet = config['import']['quiet'].get()
        user_quiet_fallback = config['import']['quiet_fallback'].get()
        user_group_albums = config['import']['group_albums'].get()
        user_singletons = config['import']['singletons'].get()
        user_pretend = config['import']['pretend'].get()
        user_set_fields = {k: v.get() for k,v in config['import']['set_fields'].items()}
        try:
            config['import']['incremental'] = not opts.reimport
            config['import']['resume'] = True
            config['import']['move'] = True
            config['import']['pretend'] = opts.pretend
            config['import']['group_albums'] = False
            config['import']['singletons'] = singletons
            config['import']['set_fields'] = opts.set
            config['import']['quiet'] = opts.quiet
            if opts.quiet_fallback:
                config['import']['quiet_fallback'] = opts.quiet_fallback
            import_files(lib, [src_dir], None)
        finally: # revert global import configuration changes
            config['import']['incremental'] = user_incremental
            config['import']['resume'] = user_resume
            config['import']['move'] = user_move
            config['import']['pretend'] = user_pretend
            config['import']['group_albums'] = user_group_albums
            config['import']['singletons'] = user_singletons
            config['import']['set_fields'] = user_set_fields
            config['import']['quiet'] = user_quiet
            config['import']['quiet_fallback'] = user_quiet_fallback
