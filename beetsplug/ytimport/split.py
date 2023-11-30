import os
import subprocess
import json
import pathlib
import glob
import re
from functools import reduce
from beetsplug.ytimport.safename import safe_name

trackNumRegex = re.compile(r'^[A-Z][0-9](\.+| ) *(-+ +)?')
artistTitleRegex = re.compile(r'(?P<artist>.+?) +(-+|–|:|\|) +(?P<title>.+)')
albumTrailRegex = re.compile(r'(\(|\[)?Full Album([^\w]|$)', re.IGNORECASE)
yearRegex = re.compile(r'[^\w]((19|20)[0-9]{2})([^\w]|$)')
quotedRegex = re.compile(r'^(“|")([^“”"]+)(“|”|")$')
timeOffsetRegex = re.compile(r'^([0-9]{1,2}:)?[0-9]{2}:[0-9]{2} +')

def chapters2tracks(file, dest_dir):
    info = get_info(file)
    tags = get_tags(info)
    chapters = info['chapters']
    if len(chapters) < 2:
        return False

    print('Extracting tracks from '+file)
    extend_chapter_tags(chapters, tags)
    append_title_to_comment(chapters)
    fix_track_numbers(chapters)
    fix_album_artists(chapters, tags)

    pathlib.Path(dest_dir).mkdir(parents=True, exist_ok=True)

    for i in range(0, len(chapters)):
        chapter2track(file, chapters[i], i, len(chapters), dest_dir)
    return True

def get_info(file):
    cmd = ['ffprobe', '-show_chapters', '-show_format', '-show_streams', '-print_format', 'json', '-i', file, '-v', 'quiet']
    proc = subprocess.Popen(cmd,stdout=subprocess.PIPE)
    out = proc.stdout.read()
    return json.loads(out)

def get_tags(info):
    fmt = info['format']
    if 'tags' in fmt: # e.g. m4a
        return fmt['tags']
    else: # e.g. opus
        return info['streams'][0]['tags']

def extend_chapter_tags(chapters, tags):
    for c in chapters:
        c['tags'] = tags | c['tags']
        c['tags']['yt_split'] = '1'

def append_title_to_comment(chapters):
    for c in chapters:
        tags = c['tags']
        tags['comment'] += ' / '+tags['title']

def fix_track_numbers(chapters):
    '''Set track tag and remove track number from title tag.'''
    matched = 0
    padding = str(len(str(len(chapters))))
    for i in range(len(chapters)): # strip e.g. '01.'
        c = chapters[i]
        track = i + 1
        tags = c['tags']
        # Set track number based on chapter index
        tags['track'] = '{:d}/{:d}'.format(track, len(chapters))
        # Strip time offset from title
        tags['title'] = timeOffsetRegex.sub('', tags['title'])
        # Strip track number from title
        tags['title'] = re.sub('^'+str(track)+r'((\)|:) *|-+ +)|^0*'+str(track)+r'(\.+| *-| ) *(-+ +)?', '', tags['title'])
        # Strip quotation marks
        tags['title'] = quotedRegex.sub(r'\2', tags['title'])
        if trackNumRegex.match(tags['title']):
            matched += 1
    if matched >= 2:
        for c in chapters: # strip e.g. 'A1.' from title
            tags = c['tags']
            tags['title'] = trackNumRegex.sub('', tags['title'])

def fix_album_artists(chapters, album_tags):
    '''Extract artist from title.'''
    year = ''
    album = album_tags['title']
    m = albumTrailRegex.search(album_tags['title'])
    if m:
        info = album[m.start():]
        album = album[:m.start()].strip(' -')
        m = yearRegex.search(info)
        if m:
            year = m.group(1)
    for c in chapters:
        tags = c['tags']
        m = artistTitleRegex.match(tags['title'])
        if m:
            tags |= m.groupdict()
        tags['album_artist'] = album_tags['artist']
        tags['album'] = album
        if year:
            tags['year'] = year
            tags['date'] = year
            tags['origyear'] = year

def chapter2track(file, chapter, i, chapterCount, dest_dir):
    tags = chapter['tags']
    padding = str(len(str(chapterCount)))
    track = ('{:0'+padding+'d}').format(i+1)
    title = safe_name(tags['title'])
    ext = os.path.splitext(file)[1]
    if tags['artist'] == tags['album_artist']:
        dest = '{:s}/{:s} - {:s}{:s}'.format(dest_dir, track, title, ext)
    else:
        artist = safe_name(tags['artist'])
        dest = '{:s}/{:s} - {:s} - {:s}{:s}'.format(dest_dir, track, artist, title, ext)
    tmp_dest = dest+'.part'
    if os.path.isfile(dest):
        return
    if chapter['time_base'] != '1/1000':
        print("[ytimport] WARNING: chapter2track: skipping track due to unsupported time_base '%s'".format(chapter['time_base']))
        return
    start = chapter['start']
    end = chapter['end']
    if start > end:
        print('[ytimport] WARNING: chapter2track: skipping track due invalid timing')
        return
    if start != 0:
        start /= 1000
    if end != 0:
        end /= 1000
    print('  Extracting track {:s}: {:s}'.format(tags['track'], tags['title']))
    format_opt = ext == '.opus' and ['-f', 'opus'] or ['-f', 'mp4']
    subprocess.run(['ffmpeg', '-y', '-hide_banner', '-loglevel', 'error', \
        '-ss', str(start), '-to', str(end), \
        '-i', file, '-t', str(end-start), '-map_chapters', '-1'] + \
        format_opt + \
        ['-map', '0:a', '-c', 'copy'] + \
        reduce(lambda r,k: r+['-metadata:s:a:0', '{:s}={:s}'.format(k, tags[k])], tags.keys(), []) + \
        [tmp_dest])
    os.rename(tmp_dest, dest)
