# -*- encoding: utf-8 -*-

import datetime
import unittest

from Nutrition.serialize import JsonDecoder, JsonEncoder


DECODED_DATA = [
    0.85, 16, u'1', datetime.datetime(1976, 11, 1), None, True
]

ENCODED_DATA = \
    '[0.85, 16, "1", {"type": "epoch", "value": 215654400}, null, true]'


class TestSrJson(unittest.TestCase):
    def testEncode(self):
        self.assertEqual(ENCODED_DATA, JsonEncoder().encode(DECODED_DATA))

    def testDecode(self):
        self.assertEqual(DECODED_DATA, JsonDecoder().decode(ENCODED_DATA))

    def testEncodeDecodeSymmetry(self):
        self.assertEqual(
            DECODED_DATA,
            JsonDecoder().decode(
                JsonEncoder().encode(
                    DECODED_DATA
                )
            )
        )
