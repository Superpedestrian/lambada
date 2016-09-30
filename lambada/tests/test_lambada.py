"""
Tests for the :mod::`lambada` module.
"""
from unittest import TestCase

from mock import MagicMock
from six import assertRaisesRegex

import lambada
from lambada.common import LambdaContext, get_lambada_class
from lambada.tests.common import make_fixture_path


class TestLambada(TestCase):
    """
    Test class for :mod::`lambada` module.
    """
    @staticmethod
    def sample_dancer(event, context):
        """Function to use as wrapper."""
        return event, context

    def test_dancer_class(self):
        """
        Verify the dancer class constructor, props, and call.
        """

        dancer = lambada.Dancer(self.sample_dancer, 'foo', 'bar', memory=128)
        # Confirm __init__
        self.assertEqual(dancer.name, 'foo')
        self.assertEqual(dancer.description, 'bar')
        self.assertDictEqual(dancer.override_config, dict(memory=128))
        # Validate config merge property
        self.assertDictEqual(
            dancer.config,
            dict(name='foo', description='bar', memory=128)
        )
        self.assertEqual((1, 2), dancer(1, 2))

    def test_lambada_class(self):
        """Validate the base lambada class."""
        tune = lambada.Lambada()
        # Make sure we make the attributes we need
        self.assertIsNotNone(getattr(tune, 'dancers'))
        self.assertIsNotNone(getattr(tune, 'config'))

        # Create a dancer and call it
        tune.dancers['test'] = MagicMock()
        context = LambdaContext('test')
        tune('hi', context)
        tune.dancers['test'].assert_called()
        tune.dancers['test'].assert_called_with('hi', context)

        # Try a dancer that doesn't exist
        context = LambdaContext('nope')
        with assertRaisesRegex(self, Exception, 'No matching dancer'):
            tune('bye', context)

    def test_decorator(self):
        """
        Test out decorators using a test fixture.
        """
        path = make_fixture_path('basic')
        tune = get_lambada_class(path)
        self.assertEqual(
            set(('test_lambada', 'hi', 'test_argless', 'test_multiarg')),
            set(tune.dancers.keys())
        )
        # verify that test_multiarg is properly getting it's config
        self.assertEqual(4242, tune.dancers['test_multiarg'].config['memory'])
        self.assertEqual(
            'us-west-2',
            tune.dancers['test_multiarg'].config['region']
        )

        # Call all of them to verify everything is working as expected.
        for dancer in tune.dancers.keys():
            context = LambdaContext(dancer)
            self.assertEqual('Event: fhqwhgads', tune('fhqwhgads', context))
