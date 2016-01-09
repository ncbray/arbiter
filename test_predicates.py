import arbiter
import unittest

class TestStringMethods(unittest.TestCase):
    def setUp(self):
        self.d = arbiter.Device("test")
        self.f = self.d.cache.const(False)
        self.t = self.d.cache.const(True)

    def testSimpleSanity(self):
        f = self.f
        t = self.t
        self.assertIsNot(f, t)
        self.assertIs(f.value, False)
        self.assertIs(t.value, True)

    def testSimpleEquality(self):
        f = self.f
        t = self.t
        self.assertEqual(f, f)
        self.assertNotEqual(t, f)
        self.assertNotEqual(f, t)
        self.assertEqual(t, t)

    def testSimpleHash(self):
        f = self.f
        t = self.t
        self.assertEqual(hash(f), hash(False))
        self.assertEqual(hash(t), hash(True))

    def testSimpleAnd(self):
        f = self.f
        t = self.t
        self.assertIs(t & t, t)
        self.assertIs(t & f, f)
        self.assertIs(f & t, f)
        self.assertIs(f & f, f)

    def testSimpleOr(self):
        f = self.f
        t = self.t
        self.assertIs(t | t, t)
        self.assertIs(t | f, t)
        self.assertIs(f | t, t)
        self.assertIs(f | f, f)

if __name__ == "__main__":
    unittest.main()
