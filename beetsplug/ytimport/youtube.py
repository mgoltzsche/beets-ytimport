import os
import json
import ytmusicapi
import yt_dlp

def login(headers=None):
    if headers:
        return ytmusicapi.setup(headers_raw=headers)
    else:
        return ytmusicapi.setup_oauth()

def likes(auth, max_tracks):
    yt = ytmusicapi.YTMusic(json.dumps(auth))
    likes = yt.get_liked_songs(max_tracks)
    return [t['videoId'] for t in likes['tracks']]

def download(urls, target_dir, auth_headers={}):
    # Test data
    #urls = [
    #    'https://www.youtube.com/watch?v=Q89OdbX7A8E', # "Pendulum - Slam [HD - 320kbps]" von "Shadowrend68"
    #    'https://www.youtube.com/watch?v=_3pzM2GoSvU', # "07. Lemon D - Deep Space" von "DNBStylez"
    #    'https://www.youtube.com/watch?v=NGBnYonnSms', # "Bassnectar – Loco Ono (Bassnectar & Stylust Beats Remix)" von "Bassnectar"
    #    'https://www.youtube.com/watch?v=7VwubS2kBYU', # "Cabal" von "Marcus Intalex (Thema)"
    #    'https://www.youtube.com/watch?v=5MQjNIHaj4g', # "Oura  - Folded - DNB" von "Savory Audio"
    #    'https://www.youtube.com/watch?v=Usqwy2-E4SE', # "Goldie - Timeless" von "Naci E."
    #    'https://www.youtube.com/watch?v=ruc0TnSSi9Y', # "Squarepusher - The Exploding Psychology (HD)"
    #    'https://www.youtube.com/watch?v=5tJPMBB7MgE', # "[Dubstep ] Occult -- Cauldron [HD. HQ, 1920px] 30 MINUTES + FREE DOWNLOAD"
    #]
    
    def download_filter(info, *, incomplete):
        duration = info.get('duration')
        if duration and duration < 60:
            return 'Track is too short'
        if duration and duration > 7200:
            return 'Track is too long'

    ytdl_opts = {
        'outtmpl': target_dir+'/%(artist|)s%(artist& - |)s%(title)s [%(id)s].%(ext)s',
        'format': 'm4a/bestaudio/best', # Prefer m4a to avoid conversion within pp.
        'download_archive': target_dir+'/.youtube-download.log',
        'continuedl': True,
        #'restrictfilenames': True,
        'windowsfilenames': True,
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
                # Using m4a avoids the need to convert the audio (which would decrease quality) in most cases - just extract it from webm.
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'm4a',
                'nopostoverwrites': True
            },
            { # Corresponds to the --parse-metadata CLI option.
                'key': 'MetadataFromField',
                'formats': [
                    # Add Youtube URL and original title to comment field.
                    # This is to preserve the information when importing it into beets where it could be useful for disambiguation later.
                    '%(original_url)s %(title)s:%(meta_comment)s',
                    # Extract track number and artist from title.
                    'title:^(\\[[^\\]]+\\] *)?((?P<track_number>0[1-9])\\.? +)?(?P<artist>.+?) +(-+|–|:|\\||~|) +(?P<title>.+?)(\\((HD|HQ|Official)([^\\)]+)?\\)|( +\\[(HD|Official)([^\\]]+)?\\]))? *$|',
                    # Add additional Youtube fields to the file's metadata.
                    '%(like_count)s:%(meta_likes)s',
                    '%(dislike_count)s:%(meta_dislikes)s',
                    '%(view_count)s:%(meta_views)s',
                    '%(average_rating)s:%(meta_rating)s',
                    '%(release_date>%Y-%m-%d,upload_date>%Y-%m-%d)s:%(meta_publish_date)s',
                ],
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
    if len(auth_headers) > 0:
        ytdl_opts['http_headers'] = auth_headers
    ydl = yt_dlp.YoutubeDL(ytdl_opts)
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
