import unittest

from app.config import config


class ConfigTests(unittest.TestCase):
    def test_llm_strict_mode_falls_back_gracefully(self):
        self.assertFalse(config.llm_strict_mode)


if __name__ == "__main__":
    unittest.main()
