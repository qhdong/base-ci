import unittest

class TestFileFail(unittest):
    def test_fail(self):
        self.fail('I will fail.')
