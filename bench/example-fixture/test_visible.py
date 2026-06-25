import unittest
from app import greet

class VisibleTest(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(greet("Ada"), "Hello, Ada")
