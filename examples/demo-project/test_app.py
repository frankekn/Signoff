import unittest

import app


class GreetingTest(unittest.TestCase):
    def test_greeting(self) -> None:
        self.assertEqual(app.greet(), "hello world")


if __name__ == "__main__":
    unittest.main()
