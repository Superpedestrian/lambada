# -*- coding: utf-8 -*-
"""
Tests for the :mod::`lambada.common` module.
"""
import os
import sys
from unittest import TestCase

import click
from mock import patch
from six import iteritems, assertRaisesRegex

from lambada import common
from lambada.tests.common import make_fixture_path


class TestCommon(TestCase):
    """
    Test running class for :mod::`lambada.common` module.
    """
    @patch('lambada.common.time')
    def test_get_time_millis(self, mock_time):
        """Verify we get the  time in milliseconds since epoch."""
        mock_time.time.return_value = 1475087560.420895
        self.assertEqual(common.get_time_millis(), 1475087560421)
        self.assertTrue(mock_time.time.called)

    def test_get_lambada_class(self):
        """Use fixtures to excercise finding the lambada clas."""
        # Load up our basic lambada module by name
        path = make_fixture_path('basic')
        tune = common.get_lambada_class(path)
        self.assertIsNotNone(tune)
        self.assertTrue('test_lambada' in tune.dancers)

        # Now by folder
        original_sys_path = sys.path[:]
        tune = common.get_lambada_class(os.path.dirname(path))
        self.assertIsNotNone(tune)
        self.assertTrue('test_lambada' in tune.dancers)
        self.assertEqual(original_sys_path, sys.path)

        # Assert exception by specifying location that doesn't exist
        path = make_fixture_path('nodancers', 'nope.py')
        with assertRaisesRegex(
            self, click.ClickException, 'Path does not exist'
        ):
            common.get_lambada_class(path)

        # Handle case with no dancers
        path = make_fixture_path('nodancers')
        self.assertIsNone(common.get_lambada_class(path))

        # Now a file that isn't a python file at all
        path = make_fixture_path('nodancers', 'fantastic.txt')
        tune = common.get_lambada_class(path)
        self.assertIsNone(tune)

        # Now by folder
        tune = common.get_lambada_class(
            make_fixture_path('nodancers', None)
        )
        self.assertIsNone(tune)

        # Load a file that raises on import
        path = make_fixture_path('raises', None) + '/'
        with patch('lambada.common.click.echo') as echo:
            common.get_lambada_class(path)
            self.assertIn("Exception('So unique, wow!')", echo.call_args[0][0])

        # Load a dir with two and assert we only grab the first one
        path = make_fixture_path('two', None)
        with patch('lambada.common.click.echo') as echo:
            tune = common.get_lambada_class(path)
            self.assertTrue('lambda0' in tune.dancers)

    @patch('lambada.common.LambadaConfig._validate')
    @patch('lambada.common.LambadaConfig._validate_vpc')
    def test_lambda_config(self, vpc_validate, validate):
        """
        Verify our configuration class does as expected.
        """
        config = dict(region='hi')
        test_config = common.LambadaConfig('.', config)
        self.assertFalse(vpc_validate.called)
        self.assertTrue(validate.called)
        self.assertDictEqual(test_config.config, config)

        # Double check VPC validation happens
        config['vpc'] = 'bye'
        test_config = common.LambadaConfig('.', config)
        self.assertTrue(vpc_validate.called)
        self.assertDictEqual(test_config.config, config)

    @patch('lambada.common.get_time_millis')
    def test_context(self, get_time):
        """
        Validate the cloned version of the Amazon context object.
        """
        # pylint: disable=protected-access
        context = dict(
            function_version='1.0.0',
            invoked_function_arn='$LATEST',
            memory_limit_in_mb=128,
            aws_request_id='lambda-adefefefef',
            log_group_name='lambada',
            log_stream_name='super-stream',
            identity=None,
            client_context=None,
            timeout=30
        )
        get_time.return_value = 1
        test_context = common.LambdaContext('tester', **context)
        self.assertIsNotNone(getattr(test_context, '_end'))
        self.assertEqual(test_context._end, 30001)

        # Verify the count down functions works as expected
        get_time.return_value = 20001
        self.assertEqual(test_context.get_remaining_time_in_millis(), 10000)

        del context['timeout']
        test_context = common.LambdaContext('tester1', **context)
        self.assertIsNone(test_context.get_remaining_time_in_millis())

        # Validate our string representation method works as expected
        string_repr = str(test_context)
        for _, val in iteritems(context):
            self.assertIn(str(val), string_repr)
