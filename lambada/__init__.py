# -*- coding: utf-8 -*-
"""
Lambada package entry point
"""
from __future__ import unicode_literals
from functools import wraps
import logging

from six import iteritems

__version__ = '0.1.0'
log = logging.getLogger(__name__)


OPTIONAL_CONFIG = dict(
    region='us-east-1',
    role=None,
    timeout=30,
    memory=128,
    extra_files=[],
    ignore_files=[],
    requirements=[],
    vpc=None,
    subnets=None,
    security_groups=None,
)


class Dancer(object):
    """
    Simple function wrapping class to add context
    to the function (i.e. name, description, memory.)
    """
    # pylint: disable=too-few-public-methods
    def __init__(
            self,
            function,
            name=None,
            description='',
            **kwargs
    ):
        """Creates a dancer object to let us know something has
        been decorated and store the function as the callable.

        Args:
            function (callable): Function to wrap.
            name (str): Name of function.
            description (str): Description of function.
            kwargs: See :data:`OPTIONAL_CONFIG` for options, if not
                specified in dancer, the Lambada objects configuration is
                used, and if that is unspecified, the defaults listed there
                are used.
        """
        self.function = function
        self.name = name
        self.description = description
        self.override_config = kwargs

    @property
    def config(self):
        """
        A dictionary of configuration variables that can be merged in with
        the Lambada object
        """
        return dict(
            name=self.name,
            description=self.description,
            **self.override_config
        )

    def __call__(self, *args, **kwargs):
        """
        Calls the function.
        """
        return self.function(*args, **kwargs)


class Lambada(object):
    """
    Lambada class for managing, discovery and calling
    the correct lambda dancers.
    """
    # pylint: disable=too-few-public-methods

    def __init__(self, handler='lambda.tune', **kwargs):
        """
        Setup the data structure of dancers and do some auto configuration
        for us with deploying to AWS using :mod:`lambda_uploader`. See
        :data:`OPTIONAL_CONFIG` for arguments and defaults.
        """
        self.config = dict(handler=handler)
        for key, default in iteritems(OPTIONAL_CONFIG):
            self.config[key] = kwargs.get(key, default)
        log.debug('Base lambada configuration is: %r', self.config)
        self.dancers = {}

    def __call__(self, event, context):
        """
        Lambda handler which is auto configured when pushed to Lambda

        Args:
            event: Amazon event passed in
            context: AWS Lambda context object passed in.
        """
        dancer = context.function_name
        try:
            return self.dancers[dancer](event, context)
        except KeyError:
            raise Exception(
                'No matching dancer for the Lambda function: {}'.format(
                    dancer
                )
            )

    def dancer(
            self,
            name=None,
            description='',
            **kwargs
    ):
        """
        Wrapper that adds a given function to the dancers dictionary to be
        called.

        Args:
            name (str): Optional lambda function name (default uses the name
                of the function decorated.
            description (str): Description field in AWS of the function.
            kwargs: Key/Value overrides of either defaults or Lambada class
                configuration values. See :data:`OPTIONAL_CONFIG` for
                available options.
        Returns:
            Dancer: Object with configuration and callable that is the function
                being wrapped
        """

        def _dancer(func):
            """
            Inner decorator to support syntactically simpler decorators.
            Finds out name of function and adds to dictionary of dancers
            using the name as the key.

            Args:
                Function to be wrapped.

            Returns:
                Function wrapped with arguments
            """
            @wraps(func)
            def _decorator(*args, **kwargs):
                """
                Inner decorator that gets called when the dancer executes.
                """
                log.debug(
                    'Calling %s with event: %r and context: %r',
                    real_name,
                    *args
                )
                return func(*args, **kwargs)

            # Add decorated function to registry
            if (not name) or callable(name):
                real_name = func.__name__
            else:
                real_name = name

            self.dancers[real_name] = Dancer(
                _decorator, real_name, description, **kwargs
            )

            return self.dancers[real_name]

        # name can be callable, None, or an argument, figure that out
        # and return the correct wrapper
        if callable(name):
            return _dancer(name)
        return _dancer
