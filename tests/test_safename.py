import unittest
from beetsplug.ytimport.safename import safe_name

class TestSafeName(unittest.TestCase):

    def test_safe_name(self):
        testcases = [
            {
                'name': 'drop accent marks',
                'input': u'Tour De Manège',
                'expected': 'Tour De Manege',
            },
            {
                'name': 'drop slash',
                'input': r'A /\ B',
                'expected': 'A B',
            },
            {
                'name': 'preserve ampersand',
                'input': 'Amadou & Mariam',
                'expected': 'Amadou & Mariam',
            },
            {
                'name': 'turn colon into minus',
                'input': 'Compilation Vol 4 : Album Name',
                'expected': 'Compilation Vol 4 - Album Name',
            },
            {
                'name': 'turn double quote into underscore',
                'input': '"Non Stop"',
                'expected': '_Non Stop_',
            },
            {
                'name': 'turn single quote into underscore',
                'input': "d'or",
                'expected': 'd or',
            },
            {
                'name': 'turn : to -',
                'input': 'XYZ LP : XYZ Records',
                'expected': 'XYZ LP - XYZ Records',
            },
            {
                'name': 'trim space',
                'input': 'Jeff The F... - Le Monstre du Lockdown',
                'expected': 'Jeff The F - Le Monstre du Lockdown',
            },
            {
                'name': 'truncate long name',
                'input': 'a' * 102,
                'expected': 'a' * 100,
            },
        ]
        for c in testcases:
            a = safe_name(c['input'])
            self.assertEqual(a, c['expected'], "testcase '{}' input: {}".format(c['name'], c['input']))

if __name__ == '__main__':
    unittest.main()
