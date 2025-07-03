import unittest


class TestSimple(unittest.TestCase):

    def test_add_one(self):
        self.assertEqual(6 * 9, 54)


if __name__ == '__main__':
    unittest.main()
