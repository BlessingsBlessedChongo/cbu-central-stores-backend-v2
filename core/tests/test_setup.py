import pytest
from django.test import TestCase

class TestProjectSetup(TestCase):
    def test_django_working(self):
        """Test that Django is properly configured"""
        self.assertTrue(True)
    
    def test_settings_loaded(self):
        """Test that settings are loaded correctly"""
        from django.conf import settings
        self.assertIsNotNone(settings.SECRET_KEY)
        self.assertTrue(settings.DEBUG)