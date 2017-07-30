from selenium import webdriver
import unittest


class NewVisitorTest(unittest.TestCase):
    def setUp(self):
        self.browser = webdriver.Firefox()

    def tearDown(self):
        self.browser.quit()

    def test_retrieve_browser_title(self):
        self.browser.get('http://localhost:8000')
        self.assertIn("To-Do", self.browser.title)


if __name__ == "__main__":
    unittest.main()
