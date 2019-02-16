import json
import unittest

def make_foo(s):
    f = Foo_v1(None, None)
    f.__dict__.update(json.loads(s))
    return f

class Foo_v1(object):
    def __init__(self, a, b):
        self.a = a
        self.b = b
        self.c = None

    def __eq__(self, other):
        return self.a == other.a and self.b == other.b and self.c == other.c

    def set_c(self, x):
        self.c = x

    def serialize(self):
        return json.dumps(self.__dict__, sort_keys=True)

class TestFooSerialize(unittest.TestCase):
    def testSerialize(self):
        f = Foo_v1(1, 2)
        f.set_c(3)
        self.assertEqual([f.a, f.b, f.c], [1, 2, 3])

        self.assertEqual(f.serialize(), '{"a": 1, "b": 2, "c": 3}')

class TestFooDeserialize(unittest.TestCase):
    def testDeserialize(self):
        f = Foo_v1(1, 2)
        f.set_c(3)
        self.assertEqual([f.a, f.b, f.c], [1, 2, 3])

        self.assertEqual(make_foo('{"a": 1, "b": 2, "c": 3}'), f)
        
