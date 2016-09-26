"""
Lambada package entry point
"""
from __future__ import unicode_literals
from functools import wraps
import logging

__version__ = '0.0.0'
log = logging.getLogger(__name__)


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
            description=None,
            timeout=None,
            memory=None,
    ):
        """
        Adds function to self to make it callable.

        Args:
            function (callable): Function to wrap.
            name (str): Name of function.
            description (str): Description of function.
            timeout (int): Maximum seconds allowed for function to run.
            memory (int): Number of MiBs of ram allowed to use.
        """
        # pylint: disable=too-many-arguments

        self.function = function
        self.name = name
        self.description = description
        self.timeout = timeout
        self.memory = memory

    def __call__(self, *args, **kwargs):
        """
        Calls the function.
        """
        self.function(*args, **kwargs)


class Lambada(object):
    """
    Lambada class for managing, discovery and calling
    the correct lambda dancers.
    """
    # pylint: disable=too-few-public-methods

    def __init__(
            self,
            handler='lambda.tune',
            region=None,
            role=None,
            timeout=30,
            memory=128,
            extra_files=None,
            ignore_files=None,
            vpc=None,
            subnets=None,
            security_groups=None,
    ):
        """
        Setup the data structure of dancers and do some auto configuration
        for us with deploying to AWS using ``lambda-uploader``.
        """
        # pylint: disable=too-many-arguments

        self.config = dict(
            extra_files=extra_files or [],
            handler=handler,
            ignore_files=ignore_files or [],
            memory=memory,
            region=region,
            role=role,
            timeout=timeout,
            # VPC config
            vpc=vpc,
            security_groups=security_groups,
            subnets=subnets,
        )
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
            self.dancers[dancer](event, context)
        except KeyError:
            raise Exception(
                'No Matching Dancer for the tune: {}'.format(
                    dancer
                )
            )

    def dancer(
            self,
            name=None,
            description=None,
            timeout=None,
            memory=None
    ):
        """
        Wrapper that adds a given function to the dancers dictionary to be
        called.

        Args:
            name (str): Optional lambda function name (default uses the name
                of the function decorated.
        Returns:
            function: Wrapped function
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
                _decorator, real_name, description, timeout, memory
            )

            return self.dancers[real_name]

        # name can be callable, None, or an argument, figure that out
        # and return the correct wrapper
        if callable(name):
            return _dancer(name)
        return _dancer
