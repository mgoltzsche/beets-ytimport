import os
import re
import json
import pathlib
import ytmusicapi
import yt_dlp
from beetsplug.ytimport.split import chapters2tracks
from beetsplug.ytimport.safename import safe_name

uploader_as_artist_rule = r'uploader:^(?P<artist>.+?)( +- +Topic)?$'
title_extraction_rule = r'title:^(\[[^\]]+\])? *((?P<track_number>0[1-9])\.? +)?(?P<artist>[^(]+?) +(-+|–|\||~|) +(?P<title>.+?) *((\(|\[)(HD|HQ|Official|FREE).+)?$|'

def login(headers=None):
    if headers:
        return ytmusicapi.setup(headers_raw=headers)
    else:
        a = ytmusicapi.setup_oauth()
        return json.dumps(a)

def likes(auth, max_tracks):
    yt = ytmusicapi.YTMusic(auth)
    likes = yt.get_liked_songs(max_tracks)
    return [t['videoId'] for t in likes['tracks'] if t['likeStatus'] == 'LIKE']

class RenamePP(yt_dlp.postprocessor.PostProcessor):
    def run(self, info):
        oldname = info['filepath']
        dir = os.path.dirname(oldname)
        artist = info['artist']
        artist = safe_name(artist)
        title = safe_name(info['title'])
        newname = '{} - {} [{}].{}'.format(artist, title, info['id'], info['ext'])
        newname = os.path.join(dir, newname)
        if newname != oldname:
            self.to_screen("Renaming '{}' to '{}'".format(oldname, newname))
            os.rename(oldname, newname)
            info['filename'] = newname
        return [], info

class SplitChaptersToTracksPP(yt_dlp.postprocessor.PostProcessor):

    def __init__(self, max_length_nochapter):
        super(SplitChaptersToTracksPP, self).__init__()
        self.max_length_nochapter = max_length_nochapter

    def run(self, info):
        fname = info['filename']
        self.to_screen('Splitting ' + fname)
        dir = os.path.join(os.path.dirname(fname), '..', 'albums')
        pathlib.Path(dir).mkdir(parents=True, exist_ok=True)
        dest_dir = os.path.join(dir, os.path.basename(os.path.splitext(fname)[0]))
        if chapters2tracks(fname, dest_dir):
            os.remove(fname)
        return [], info

def download(urls, target_dir, format='bestaudio/best', min_len=60, max_len=7200, max_len_nochapter=900, split=False, like=False, reimport=False, auth_headers={}):

    def download_filter(info):
        duration = info.get('duration')
        chapters = info.get('chapters')
        if duration and duration < min_len:
            return 'Track is too short'
        if duration and duration > max_len:
            return 'Track is too long'
        if duration and duration > max_len_nochapter and (not chapters or len(chapters) < 2):
            return 'Track is too long and has no chapters'

    transform_rules = [
        # Add Youtube URL and original title to comment field.
        # This is to preserve the information when importing it into beets where it could be useful for disambiguation later.
        '%(webpage_url)s %(title)s:%(meta_comment)s',
        # Use uploader name without suffix as artist tag.
        uploader_as_artist_rule,
        # Trim ' Official' suffix from artist
        r'artist:^(?P<artist>.+) Official$|',
        # Extract track number and artist from title tag.
        title_extraction_rule,
        # Use artist as album_artist
        r'artist:^(?P<album_artist>.+?)$',
        # Trim quotes from title
        r'title:^(“|")(?P<title>[^“”"]+)(“|”|")$|',
        # Trim trailing dot from title
        r'title:^(?P<title>.+[^0-9])\.$|',
        # Add additional Youtube fields to the file's metadata.
        '%(id)s:%(meta_yt_id)s',
        '%(webpage_url_domain)s:%(meta_yt_source)s',
        r'webpage_url_domain:^(?P<meta_yt_source>[^\.]+?)\.[^\.]+$|',
        '%(like_count)s:%(meta_yt_likes)s',
        '%(dislike_count)s:%(meta_yt_dislikes)s',
        '%(view_count)s:%(meta_yt_views)s',
        '%(average_rating)s:%(meta_yt_rating)s',
        '%(release_date>%Y-%m-%d,upload_date>%Y-%m-%d)s:%(meta_publish_date)s',
    ]
    if like:
        transform_rules += ['1:%(meta_like)s']
    ytdl_opts = {
        'outtmpl': target_dir+'/singles/%(artist|)s%(artist& - |)s%(title)s [%(id)s].%(ext)s',
        'format': format,
        'continuedl': True,
        'restrictfilenames': True,
        'windowsfilenames': True,
        'trim_file_name': 120,
        'writethumbnail': True,
        'keepvideo': False,
        'ignoreerrors': True,
        'nooverwrites': True,
        'retries': 10,
        'match_filter': download_filter,
        'process': True,
        'force_generic_extractor': False,
        'postprocessors': [
            { # Corresponds to the -x CLI option.
                'key': 'FFmpegExtractAudio',
                'nopostoverwrites': True
                # Don't specify preferredcodec to prevent transcoding lossy audio
            },
            { # Corresponds to the --parse-metadata CLI option.
                'key': 'MetadataFromField',
                'formats': transform_rules,
            },
            { # Corresponds to the --add-metadata CLI option.
                'key': 'FFmpegMetadata',
            },
            { # Corresponds to the --embed-thumbnail CLI option.
                'key': 'EmbedThumbnail',
            },
            { # Corresponds to --xattrs CLI option.
                'key': 'XAttrMetadata',
            },
        ],
        # TODO: maybe enable for premium quality: 'cookiefile': 'path/to/cookies.txt',
    }
    if not reimport:
        ytdl_opts['download_archive'] = target_dir+'/ytdownloads.txt'
    if len(auth_headers) > 0:
        ytdl_opts['http_headers'] = auth_headers
    pathlib.Path(target_dir).mkdir(parents=True, exist_ok=True)
    ydl = yt_dlp.YoutubeDL(ytdl_opts)
    if split:
        ydl.add_post_processor(RenamePP(), when='post_process')
        ydl.add_post_processor(SplitChaptersToTracksPP(max_len_nochapter), when='post_process')
    ydl.download(urls)

#yt-dlp --batch-file=/data/youtube-likes.urls --download-archive=youtube/.youtube-download.log \
#  -ciwx --audio-format=m4a \
#  -o '/data/youtube/%(title)s.%(ext)s' \
#  --parse-metadata '%(original_url)s %(title)s:%(meta_comment)s' \
#  --parse-metadata 'title:^(\[[^\]]+\] *)?((?P<track_number>0[1-9])\.? +)?(?P<artist>.+?) +(-+|–|:|\||~|) +(?P<title>.+?)(\((HD|HQ|Official)([^\)]+)?\)|( +\[(HD|Official)([^\]]+)?\]))? *$|' \
#  --parse-metadata '%(like_count)s:%(meta_likes)s' \
#  --parse-metadata '%(dislike_count)s:%(meta_dislikes)s' \
#  --parse-metadata '%(view_count)s:%(meta_views)s' \
#  --parse-metadata '%(average_rating)s:%(meta_rating)s' \
#  --parse-metadata '%(release_date>%Y-%m-%d,upload_date>%Y-%m-%d)s:%(meta_publish_date)s' \
#  --add-metadata \
#  --embed-metadata \
#  --embed-thumbnail \
#  --xattrs --no-overwrites \
#  --restrict-filenames --windows-filenames \
#  --progress
