from collections import OrderedDict
import unittest

from evalrescallers import utils

class TestUtils(unittest.TestCase):
    def test_comma_sep_string_to_ordered_dict(self):
        '''test comma_sep_string_to_ordered_dict'''
        test_string = 'key1,val1,key2,val2'
        expect = OrderedDict([('key1', 'val1'), ('key2', 'val2')])
        got = utils.comma_sep_string_to_ordered_dict(test_string)
        self.assertEqual(expect, got)

        # Can't have odd number of elements in the list
        with self.assertRaises(Exception):
            utils.comma_sep_string_to_ordered_dict('one,two,three')

