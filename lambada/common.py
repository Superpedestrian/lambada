"""
Common classes, functions, etc.
"""
import imp
from glob import glob
import os
import time
import traceback

import click
from lambda_uploader.config import Config, REQUIRED_PARAMS

from lambada import Lambada


def get_lambada_class(path):
    """
    Given the path, find the lambada
    class label by :func:`dir` ing for that type.

    Args:
        path (click.Path): Path to folder or file
    """
    # Need to catch a lot more exceptions than usual
    # since I am trying to blindly load python files.
    # pylint: disable=broad-except
    tune = None
    module_list = []

    if os.path.isdir(path):
        counter = 0
        for python_file in glob(path + '*.py'):
            try:
                module_list.append(
                    imp.load_source(
                        '__temp{}__'.format(counter),
                        python_file
                    )
                )
                counter += 1
            except (Exception, SystemExit):
                click.echo('Unable to import {}'.format(python_file))
                click.echo('Got stack trace:\n{}'.format(
                    ''.join(traceback.format_exc())
                ))

    elif os.path.isfile(path):
        module_list.append(
            imp.load_source('__temp__', path)
        )
    else:
        raise click.ClickException('Path does not exist')

    for module in module_list:
        for name in dir(module):
            try:
                item = getattr(module, name, None)
            except ImportError:
                item = None
            if isinstance(item, Lambada):
                tune = item
                break
        if tune:
            break
    return tune


def get_time_millis():
    """
    Returns the current time in milliseconds since epoch.
    """
    return int(round(time.time() * 1000))


class LambadaConfig(Config):
    """
    Small override to load config from dictionary instead
    of from a configuration file.
    """
    def __init__(self, path, config):
        """
        Takes config dictionary directly instead of
        retrieving it from a configuration file.
        """
        # pylint: disable=super-init-not-called
        self._path = path
        self.config = self._config = config
        self._set_defaults()
        if self._config['vpc']:
            self._validate_vpc()

        for param, clss in REQUIRED_PARAMS.items():
            self._validate(param, cls=clss)


class LambdaContext(object):
    """
    Convenient class duplication of the one passed in by Amazon as
    defined at:

    http://docs.aws.amazon.com/lambda/latest/dg/python-context-object.html
    """
    # pylint: disable=too-many-instance-attributes,too-few-public-methods
    def __init__(
            self,
            function_name,
            function_version=None,
            invoked_function_arn=None,
            memory_limit_in_mb=None,
            aws_request_id=None,
            log_group_name=None,
            log_stream_name=None,
            identity=None,
            client_context=None,
            timeout=None
    ):
        """
        Setup all the attributes of the class.
        """
        # pylint: disable=too-many-arguments,too-few-public-methods
        self.function_name = function_name
        self.function_version = function_version
        self.invoked_function_arn = invoked_function_arn
        self.memory_limit_in_mb = memory_limit_in_mb
        self.aws_request_id = aws_request_id
        self.log_group_name = log_group_name
        self.log_stream_name = log_stream_name
        self.identity = identity
        self.client_context = client_context

        if timeout:
            self._end = get_time_millis() + (timeout * 1000)

    def get_remaining_time_in_millis(self):
        """
        If we have a timeout return the amount of time left.
        """
        if not self._end:
            return None
        return self._end - get_time_millis()

    def __str__(self):
        """
        return all attributes as repr to make
        debugging easier.
        """
        return str(vars(self))
