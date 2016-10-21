# -*- coding: utf-8 -*-
"""
Lambada package entry point
"""
from __future__ import unicode_literals
from functools import wraps
import logging
import os

from six import iteritems
import yaml

__version__ = '0.2.1'
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

CONFIG_PATHS = [
    os.path.join(os.getcwd(), '_lambada.yml'),  # "Private" bouncer config
    os.environ.get('BOUNCER_CONFIG', ''),
    os.path.join(os.getcwd(), 'lambada.yml'),
    os.path.join(os.path.expanduser('~'), '.lambada.yml'),
    '/etc/lambada.yml',
]


def get_config_from_env(env_prefix='BOUNCER_'):
    """
    Get any and all environment variables with given prefix, remove
    prefix, lower case the name, and add as a dictionary item that
    is returned.

    Args:
        env_prefix (str): environemnt variable prefix.

    Returns:
        dict: empty if no environment variables were found, or the
            dictionary of found variables that match the prefix.
    """
    config = {}
    for key, value in iteritems(os.environ):
        if key.startswith(env_prefix) and key != 'BOUNCER_CONFIG':
            config[key[len(env_prefix):].lower()] = value
    return config


def get_config_from_file(config_file=None):

    """
    Finds configuration file and returns the python object
    in it or raises on parsing failures.

    Args:
        config_file (str): Optional path to configuration file, runs
            through :data:`CONFIG_PATHS` if none is specified.

    Raises:
        yaml.YAMLError

    Returns:
        dict: empty if no configuration file was found, or the
            contents of that file.
    """
    if not config_file:
        for config_path in CONFIG_PATHS:
            if os.path.isfile(config_path):
                config_file = config_path
                break
    if not config_file:
        return {}

    with open(config_file) as config:
        return yaml.load(config)


class Bouncer(object):
    """Configuration class for lambda type deployments where you
    don't want to keep security information in source control, but
    don't have environment variable configuration as a feature of
    Lambda.  It pairs with the command line interface to package and
    serializes the current configuration into the zip file when
    packaging.  This allows changing with local environment variable
    changes or different configuration file paths at package time).

    Configuration files, if not specified, are loaded in the following
    order, with the first one found being the only configuration (they
    do not layer):

    - Path specified by ``BOUNCER_CONFIG`` environment variable.
    - ``lambada.yml`` in the current working directory.
    - ``.lambada.yml`` in your ``HOME`` directory
    - ``/etc/lambada.yml``

    That said no configuration file is required and any environment
    variable with a certain prefix will be added to the attributes of
    this class when instantiated.  The default is ``BOUNCER_`` so the
    environment variable ``BOUNCER_THING`` will be set in the object
    as ``bouncer.thing`` after construction.

    These prefixed environment variables will also override whatever
    value is in the config, so if your config file has a ``thing``
    variable in it, and ``BOUNCER_THING`` is set, the value of the
    environment variable will override the configuration file.

    """
    # pylint: disable=too-few-public-methods
    _frozen = False

    def __init__(self, config_file=None, env_prefix='BOUNCER_'):
        """
        Finds and sets up configuration by yaml file

        Args:
            config_file (str): Path to configuration file
            env_prefix (str): Prefix of environment variables to
                use as configuration
        """
        config = get_config_from_file(config_file)
        config.update(get_config_from_env(env_prefix))

        self.__dict__ = config
        self._frozen = True

    def __getattr__(self, name):
        """Return elements of the configuration as attributes."""
        return self.__dict__[name]

    def __setattr__(self, name, value):
        """Return elements of the configuration as attributes."""
        if self._frozen and name != '_frozen':
            raise TypeError('Bouncers should not be updated after creation.')
        return super(Bouncer, self).__setattr__(name, value)

    def export(self, stream):
        """
        Write out the current configuration to the given stream as YAML.

        Args:
            destination (str): Path to output file.
        Raises:
            IOError
            yaml.YAMLError
        """
        yaml.dump(
            {k: v for k, v in iteritems(self.__dict__) if k != '_frozen'},
            stream,
            default_flow_style=False
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

    def __init__(self, handler='lambda.tune', bouncer=Bouncer(), **kwargs):
        """
        Setup the data structure of dancers and do some auto configuration
        for us with deploying to AWS using :mod:`lambda_uploader`. See
        :data:`OPTIONAL_CONFIG` for arguments and defaults.
        """
        self.config = dict(handler=handler)
        self.bouncer = bouncer
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
