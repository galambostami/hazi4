import unittest

import common
import solution


class TestSolution(unittest.TestCase):
    def __init__(self, method_name):
        super().__init__(method_name)

    def test_call(self):
        common.call(solution)

    def test_run(self):
        common.run()


if __name__ == "__main__":
    unittest.main()
