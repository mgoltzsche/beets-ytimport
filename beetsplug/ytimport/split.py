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

def chapters2tracks(file, dest_dir):
    info = get_info(file)
    chapters = info['chapters']
    if len(chapters) < 2:
        return False

    print('Extracting tracks from '+file)
    extend_chapter_tags(info)
    append_title_to_comment(chapters)
    fix_track_numbers(chapters)
    fix_album_artists(chapters, info['format'])

    pathlib.Path(dest_dir).mkdir(parents=True, exist_ok=True)

    for c in chapters:
        chapter2track(file, c, len(chapters), dest_dir)
    return True

def get_info(file):
    cmd = ['ffprobe', '-show_chapters', '-show_format', '-print_format', 'json', '-i', file, '-v', 'quiet']
    proc = subprocess.Popen(cmd,stdout=subprocess.PIPE)
    out = proc.stdout.read()
    return json.loads(out)

def extend_chapter_tags(info):
    tags = info['format']['tags']
    chapters = info['chapters']
    for c in chapters:
        c['tags'] = tags | c['tags']

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
        tags['track'] = ('{:0'+padding+'d}/{:d}').format(track, len(chapters))
        tags['title'] = re.sub('^0*'+str(track)+r'(\.| ) *(-+ +)?', '', tags['title'])
        if trackNumRegex.match(tags['title']):
            matched += 1
    if matched >= 2:
        for c in chapters: # strip e.g. 'A1.'
            tags = c['tags']
            tags['title'] = trackNumRegex.sub('', tags['title'])

def fix_album_artists(chapters, format):
    '''Extract artist from title.'''
    formatTags = format['tags']
    year = ''
    album = formatTags['title']
    m = albumTrailRegex.search(formatTags['title'])
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
        tags['album_artist'] = formatTags['artist']
        tags['album'] = album
        if year:
            tags['year'] = year
            tags['date'] = year

def chapter2track(file, chapter, chapterCount, dest_dir):
    tags = chapter['tags']
    track = re.sub('/[0-9]+$', '', tags['track'])
    title = safe_name(tags['title'])
    if tags['artist'] == tags['album_artist']:
        dest = '{:s}/{:s} - {:s}.m4a'.format(dest_dir, track, title)
    else:
        artist = safe_name(tags['artist'])
        dest = '{:s}/{:s} - {:s} - {:s}.m4a'.format(dest_dir, track, artist, title)
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
    subprocess.run(['ffmpeg', '-y', '-hide_banner', '-loglevel', 'error', \
        '-ss', str(start), '-to', str(end), \
        '-i', file, '-t', str(end-start), \
        '-map', '0:a', '-map', '0:v', '-c', 'copy', '-f', 'mp4'] + \
        reduce(lambda r,k: r+['-metadata', '{:s}={:s}'.format(k, tags[k])], tags.keys(), []) + \
        [tmp_dest])
    os.rename(tmp_dest, dest)
