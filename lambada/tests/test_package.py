# -*- coding: utf-8 -*-
"""
Tests related to package/API and versioning.
"""
from unittest import TestCase

from semantic_version import Version


class TestPackage(TestCase):
    """
    Test common and core components to the package.
    """
    # pylint: disable=too-few-public-methods

    @staticmethod
    def test_version():
        """Validate version matches proper format"""
        import lambada
        Version(lambada.__version__)
