import unittest
import re
from beetsplug.ytimport.youtube import title_extraction_rule
from beetsplug.ytimport.youtube import uploader_as_artist_rule

class TestRegex(unittest.TestCase):

    def test_uploader_as_artist_rule(self):
        r = uploader_as_artist_rule
        self.assertRegex(r, '^uploader:')
        p = re.compile(r[9:])
        testcases = [
            {
                'name': 'strip suffix',
                'input': 'Colyn - Topic',
                'expected': {
                    'artist': 'Colyn',
                },
            },
            {
                'name': 'preserve suffix',
                'input': 'Some-Name',
                'expected': {
                    'artist': 'Some-Name',
                },
            },
            {
                'name': 'strip " Official" suffix',
                'input': 'Some-Name X Official',
                'expected': {
                    'artist': 'Some-Name X',
                },
            },
            {
                'name': 'strip " Oficial" suffix',
                'input': 'Ska-P Oficial',
                'expected': {
                    'artist': 'Ska-P',
                },
            },
        ]
        for c in testcases:
            m = p.match(c['input'])
            info = "\ntest case '{}' input: {}".format(c['name'], c['input'])
            self.assertIsNotNone(m, info)
            self.assertEqual(m.groupdict(), c['expected'], info)

    def test_title_extraction_rule(self):
        r = title_extraction_rule
        self.assertRegex(r, '^title:')
        p = re.compile(r[6:])
        # Test case origin:
        #  https://www.youtube.com/watch?v=7VwubS2kBYU "Cabal" von "Marcus Intalex (Thema)"
        #  https://www.youtube.com/watch?v=Q89OdbX7A8E "Pendulum - Slam [HD - 320kbps]" von "Shadowrend68"
        #  https://www.youtube.com/watch?v=_3pzM2GoSvU "07. Lemon D - Deep Space" von "DNBStylez"
        #  https://www.youtube.com/watch?v=NGBnYonnSms "Bassnectar – Loco Ono (Bassnectar & Stylust Beats Remix)" von "Bassnectar"
        #  https://www.youtube.com/watch?v=5MQjNIHaj4g "Oura  - Folded - DNB" von "Savory Audio"
        #  https://www.youtube.com/watch?v=Usqwy2-E4SE "Goldie - Timeless" von "Naci E."
        #  https://www.youtube.com/watch?v=ruc0TnSSi9Y "Squarepusher - The Exploding Psychology (HD)"
        #  https://www.youtube.com/watch?v=5tJPMBB7MgE "[Dubstep ] Occult -- Cauldron [HD. HQ, 1920px] 30 MINUTES + FREE DOWNLOAD"
        testcases = [
            {
                'name': 'minus separated',
                'input': 'fake artist - fake title',
                'expected': {
                    'artist': 'fake artist',
                    'title': 'fake title',
                    'track_number': None,
                },
            },
            {
                'name': 'minus separated',
                'input': 'Goldie - Timeless',
                'expected': {
                    'artist': 'Goldie',
                    'title': 'Timeless',
                    'track_number': None,
                },
            },
            {
                'name': 'minus separated with ampersand in artist',
                'input': 'Amadou & Mariam - Boufou Safou',
                'expected': {
                    'artist': 'Amadou & Mariam',
                    'title': 'Boufou Safou',
                    'track_number': None,
                },
            },
            {
                'name': 'double minus',
                'input': 'fake artist -- fake title',
                'expected': {
                    'artist': 'fake artist',
                    'title': 'fake title',
                    'track_number': None,
                },
            },
            {
                'name': 'match artist in title non-greedy',
                'input': 'Oura - Folded - DNB',
                'expected': {
                    'artist': 'Oura',
                    'title': 'Folded - DNB',
                    'track_number': None,
                },
            },
            {
                'name': 'preserve title with minus 1',
                'input': 'Sonnenauf- und Untergang',
                'expected': {
                    'artist': None,
                    'title': None,
                    'track_number': None,
                },
            },
            {
                'name': 'preserve title with minus 2',
                'input': 'STEPART & PUPAJIM : "Non Stop" (Playground LP - Stand High Records)',
                'expected': {
                    'artist': None,
                    'title': None,
                    'track_number': None,
                },
            },
            {
                'name': 'strip whitespace',
                'input': ' fake artist  -  fake title ',
                'expected': {
                    'artist': 'fake artist',
                    'title': 'fake title',
                    'track_number': None,
                },
            },
            {
                'name': 'track number',
                'input': '07.  Lemon D - Deep Space',
                'expected': {
                    'artist': 'Lemon D',
                    'title': 'Deep Space',
                    'track_number': '07',
                },
            },
            {
                'name': 'dash separated',
                'input': 'fake artist – fake title',
                'expected': {
                    'artist': 'fake artist',
                    'title': 'fake title',
                    'track_number': None,
                },
            },
            {
                'name': 'strip suffix 1',
                'input': 'fake artist - fake title [HQ]',
                'expected': {
                    'artist': 'fake artist',
                    'title': 'fake title',
                    'track_number': None,
                },
            },
            {
                'name': 'strip suffix 2',
                'input': 'fake artist - fake title (HQ)',
                'expected': {
                    'artist': 'fake artist',
                    'title': 'fake title',
                    'track_number': None,
                },
            },
            {
                'name': 'strip suffix 3',
                'input': 'fake artist - fake title [HD - 320kbps]',
                'expected': {
                    'artist': 'fake artist',
                    'title': 'fake title',
                    'track_number': None,
                },
            },
            {
                'name': 'strip suffix 4',
                'input': 'fake artist - fake title [Official]',
                'expected': {
                    'artist': 'fake artist',
                    'title': 'fake title',
                    'track_number': None,
                },
            },
            {
                'name': 'strip suffix 5',
                'input': 'fake artist - fake title [HD - 320kbps] FREE DOWNLOAD',
                'expected': {
                    'artist': 'fake artist',
                    'title': 'fake title',
                    'track_number': None,
                },
            },
            {
                'name': 'strip prefix',
                'input': '[HQ] fake artist - fake title',
                'expected': {
                    'artist': 'fake artist',
                    'title': 'fake title',
                    'track_number': None,
                },
            },
            {
                'name': 'strip prefix and suffix',
                'input': '[Dubstep ] Occult -- Cauldron [HD. HQ, 1920px] 30 MINUTES + FREE DOWNLOAD',
                'expected': {
                    'artist': 'Occult',
                    'title': 'Cauldron',
                    'track_number': None,
                },
            },
            {
                'name': 'preserve suffix 1',
                'input': 'fake artist - fake title (some remix)',
                'expected': {
                    'artist': 'fake artist',
                    'title': 'fake title (some remix)',
                    'track_number': None,
                },
            },
            {
                'name': 'preserve suffix 2',
                'input': 'fake artist - fake title [some remix]',
                'expected': {
                    'artist': 'fake artist',
                    'title': 'fake title [some remix]',
                    'track_number': None,
                },
            },
        ]
        for c in testcases:
            m = p.match(c['input'])
            info = "\ntest case '{}' input: {}".format(c['name'], c['input'])
            self.assertIsNotNone(m, info)
            self.assertEqual(m.groupdict(), c['expected'], info)

if __name__ == '__main__':
    unittest.main()
