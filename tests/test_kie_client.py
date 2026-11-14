import unittest
from scripts.kie_client import dig, find_urls


class KieClientTests(unittest.TestCase):
    def test_dig_nested_fields(self):
        self.assertEqual(dig({"data": {"taskId": "test-id"}}, "data.taskId"), "test-id")
        self.assertIsNone(dig({"data": {}}, "data.taskId"))

    def test_collect_unique_urls_from_nested_json(self):
        result = {"data": {"assets": '["https://example.org/one.mp4", "https://example.org/one.mp4", "https://example.org/two.png"]'}}
        self.assertEqual(find_urls(result), ["https://example.org/one.mp4", "https://example.org/two.png"])

    def test_no_urls_for_invalid_json(self):
        self.assertEqual(find_urls("not a JSON result"), [])


if __name__ == "__main__":
    unittest.main()
