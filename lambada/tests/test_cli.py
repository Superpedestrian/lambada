"""
Tests for the :mod::`lambada.cli` module.
"""
import os
from unittest import TestCase

import click
from click.testing import CliRunner
from mock import patch, MagicMock

from lambada import cli
from lambada.tests.common import make_fixture_path

BASIC_DANCERS = ('test_lambada', 'hi', 'test_argless', 'test_multiarg')


class TestCLI(TestCase):
    """
    Test class for :mod::`lambada.cli` module.
    """
    runner = CliRunner()

    def test_create_package(self):
        """Validate the packaging wrapper function."""

        tune = MagicMock()
        tune.config = dict(ignore_files=['foo'], extra_files=['bar'])

        # Verify it handles direct paths and changes them to folders
        path = make_fixture_path('basic')
        path_dirname = os.path.dirname(path)
        self.assertTrue(path_dirname, 'basic')

        def assert_build_call(build_package):
            """Validate build_package call."""
            build_package.assert_called_with(
                path_dirname,
                None,
                virtualenv=None,
                ignore=['foo'],
                extra_files=['bar'],
                zipfile_name='lambada.zip'
            )

        with patch('lambada.cli.build_package') as build_package:
            with patch('lambada.cli.io.open') as patched_open:
                with patch('lambada.cli.os.remove') as patched_delete:
                    cli.create_package(path, tune, None)
                    # Make sure we called the underlying module correct
                    assert_build_call(build_package)
                    # Make sure we dumped the config
                    self.assertTrue(tune.bouncer.export.called)
                    # Make sure we opened the write path
                    patched_open.assert_called_with(
                        os.path.join(path_dirname, '_lambada.yml'),
                        'w',
                        encoding='UTF-8'
                    )
                    # Make sure we removed it after packaging
                    self.assertTrue(patched_delete.called)

        # Verify it handles folder paths too
        with patch('lambada.cli.build_package') as build_package:
            cli.create_package(path_dirname, tune, None, 'lambada.zip')
            assert_build_call(build_package)

    def test_cli(self):
        """Test out the tune finder."""
        path = make_fixture_path('basic')

        @cli.cli.command()
        @click.pass_obj
        def clitest(obj):  # pylint: disable=unused-variable
            """Command to test base context."""
            self.assertEqual(obj['path'], path)
            self.assertTrue('hi' in obj['tune'].dancers)
        result = self.runner.invoke(cli.cli, ['--path', path, 'clitest'])
        self.assertEqual(0, result.exit_code)
        result = self.runner.invoke(
            cli.cli,
            ['--path', make_fixture_path('nodancers', None), 'clitest']
        )
        self.assertEqual(1, result.exit_code)
        self.assertIn(
            'Unable to find Lambada class declaration',
            result.output
        )

    def test_list(self):
        """Test out listing our dancers."""
        result = self.runner.invoke(
            cli.cli,
            ['--path', make_fixture_path('basic'), 'list']
        )
        self.assertEqual(0, result.exit_code)
        for dancer in BASIC_DANCERS:
            self.assertIn(dancer, result.output)
        self.assertIn('us-west-2', result.output)

    def test_run(self):
        """Test out listing our dancers."""
        result = self.runner.invoke(
            cli.cli,
            [
                '--path', make_fixture_path('basic'),
                'run', 'hi',
                '--event', 'Everyone is the best!'
            ]
        )
        self.assertEqual(0, result.exit_code)
        self.assertIn('Event: Everyone is the best!', result.output)

    @patch('lambada.cli.get_lambada_class')
    @patch('lambada.cli.create_package')
    def test_package(self, create_package, get_lambada_class):
        """Test out listing our dancers."""
        # Run with defaults
        result = self.runner.invoke(
            cli.cli,
            [
                '--path', make_fixture_path('basic'),
                'package',
            ]
        )
        self.assertEqual(0, result.exit_code)
        create_package.assert_called_with(
            make_fixture_path('basic'),
            get_lambada_class(),
            './requirements.txt',
            'lambda.zip',
        )
        # Invalid requirement handling
        result = self.runner.invoke(
            cli.cli,
            [
                '--path', make_fixture_path('basic'),
                'package',
                '--requirements', './test_requirements.txt',
                '--destination', 'blah.zip'
            ]
        )
        self.assertEqual(0, result.exit_code)
        create_package.assert_called_with(
            make_fixture_path('basic'),
            get_lambada_class(),
            './test_requirements.txt',
            'blah.zip',
        )

    @patch('lambada.cli.PackageUploader')
    @patch('lambada.cli.create_package')
    def test_upload(self, create_package, uploader):
        """Test out listing our dancers."""
        # Run on all
        result = self.runner.invoke(
            cli.cli,
            [
                '--path', make_fixture_path('basic'),
                'upload',
            ]
        )
        self.assertEqual(0, result.exit_code)
        create_package.assert_called()
        for dancer in BASIC_DANCERS:
            self.assertIn(
                'Uploading Package for {}'.format(dancer),
                result.output
            )
        self.assertEqual(len(BASIC_DANCERS), uploader.call_count)

        # Specify only one dancer
        result = self.runner.invoke(
            cli.cli,
            [
                '--path', make_fixture_path('basic'),
                'upload', 'hi'
            ]
        )
        self.assertEqual(2, create_package.call_count)
        self.assertIn('Uploading Package for hi', result.output)
        self.assertNotIn('test_argless', result.output)

        # Specify non-existent dancer
        result = self.runner.invoke(
            cli.cli,
            [
                '--path', make_fixture_path('basic'),
                'upload', 'fhqwhgads'
            ]
        )
        self.assertNotEqual(0, result.exit_code)
        self.assertIn("Dancer fhqwhgads doesn't exist", result.output)
