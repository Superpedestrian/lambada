"""
Tests for the :mod::`lambada` module.
"""
from __future__ import print_function
from unittest import TestCase

from mock import MagicMock, patch
from six import assertRaisesRegex, StringIO
import yaml

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

    @patch('lambada.get_config_from_env')
    @patch('lambada.get_config_from_file')
    def test_bouncer(self, config_file, config_env):
        """Validate bouncer class."""
        config_env.return_value = dict(foo='bar')
        config_file.return_value = dict(foo='baz', bar='foo')
        bouncer = lambada.Bouncer()
        self.assertTrue(config_file.called)
        self.assertTrue(config_env.called)
        # Assert that env wins over file
        self.assertEqual(bouncer.foo, 'bar')
        # But that it isn't fully replaced by env
        self.assertEqual(bouncer.bar, 'foo')

        # Still raise error when key doesn't exist.
        with self.assertRaises(KeyError):
            print(bouncer.fhqwhgads)

        # And that we can't change attributes easily
        with self.assertRaises(TypeError):
            bouncer.bar = 'blah'

        # And shouldn't be able to add them.
        with self.assertRaises(TypeError):
            bouncer.gooble = 'asdf'

        # Write out yaml and validate
        yaml_output = StringIO()
        bouncer.export(yaml_output)
        self.assertIn('foo: bar', yaml_output.getvalue())
        self.assertIn('bar: foo', yaml_output.getvalue())
        # Make sure we don't have our private attribute
        self.assertNotIn('_frozen', yaml_output.getvalue())

    def test_bouncer_env(self):
        """
        Validate the environment variable loader works as expected.
        """
        # Test it doesn't leak
        with patch.dict('lambada.os.environ', dict(BLAH='asdf'), clear=True):
            config = lambada.get_config_from_env()
            self.assertFalse(config)

        # Test it works with default
        with patch.dict(
            'lambada.os.environ', dict(BOUNCER_BLAH='asdf'), clear=True
        ):
            config = lambada.get_config_from_env()
            self.assertDictEqual(config, dict(blah='asdf'))

        # Test that we can override the prefix
        with patch.dict(
            'lambada.os.environ',
            dict(STUFF_BLAH='asdf', STUFFS_BLAH='jkl;'),
            clear=True
        ):
            config = lambada.get_config_from_env('STUFF_')
            self.assertDictEqual(config, dict(blah='asdf'))

    def test_bouncer_file(self):
        """
        Verify that we find and load configuration files as expected.
        """
        # Make sure we return None when there is no file.
        config = lambada.get_config_from_file()
        self.assertFalse(config)

        # Load up a well known config that works
        config = lambada.get_config_from_file(
            make_fixture_path('config', 'basic.yml')
        )
        self.assertDictEqual(
            dict(fluff=['marshmellow', 'pillow'], foo='bar', baz='things'),
            config
        )

        # Load config from loop over  CONFIG_PATHS
        with patch(
            'lambada.CONFIG_PATHS',
            [make_fixture_path('config', 'basic.yml')]
        ):
            config = lambada.get_config_from_file()
            self.assertTrue('fluff' in config)

        # Load a broken yaml file
        with patch(
            'lambada.CONFIG_PATHS',
            [make_fixture_path('config', 'bad.yml')]
        ):
            with self.assertRaises(yaml.YAMLError):
                config = lambada.get_config_from_file()

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
