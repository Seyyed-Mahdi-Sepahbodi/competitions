from django.test import SimpleTestCase
from django.utils.safestring import SafeString
from forms.templatetags import form_tags


class FormTagsFilterTestSample(SimpleTestCase):
    def test_tags_1(self):
        html = form_tags.render_markdown("**bold**\n\n```\ncode\n```\n\n|a|b|\n|-|-|\n|1|2|\n")
        self.assertIsInstance(html, SafeString)
        self.assertIn("<strong>", html)          # bold
        self.assertIn("<code>", html)            # fenced code
        self.assertIn("<table>", html)           # tables

    def test_tags_2(self):
        html = form_tags.render_markdown("")
        self.assertEqual(html, "")

    def test_tags_3(self):
        field_id = form_tags.extract_field_id("field_123")
        self.assertEqual(field_id, "123")
