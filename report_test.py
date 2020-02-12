import unittest
import report

class TestTextFromSlack(unittest.TestCase):
    def test_parse_simple_text(self):
        message = [
            {'type': 'rich_text', 'elements': [
                {'type': 'rich_text_section', 'elements': [
                    {'type': 'text', 'text': 'hello'}]}]}]
        self.assertEqual(report.textFromSlack(message), "hello")

    def test_parse_rich_text(self):
        message = [
            {'type': 'rich_text', 'elements': [
                {'type': 'rich_text_section', 'elements': [
                    {'type': 'link', 'url': 'https://app', 'text': 'Google Drive', 'style': {'bold': True}}, 
                    {'type': 'text', 'text': 'APP', 'style': {'bold': True}}, 
                    {'type': 'text', 'text': '\xa0\xa0'}, 
                    {'type': 'text', 'text': '.\n\nMessage Google Drive'},
                    ]}
                ]}
                ]
        self.assertEqual(report.textFromSlack(message), 
                         'Google Drive APP \xa0\xa0 .\n\nMessage Google Drive')