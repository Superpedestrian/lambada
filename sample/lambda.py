"""
Sample lambda library using lambada for use in multiple AWS lambdas.
"""
from __future__ import unicode_literals, print_function
import logging

from lambada import Lambada, Bouncer

logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.DEBUG)

bouncer = Bouncer()
tune = Lambada(
    handler='lambda.tune',
    bouncer=bouncer,
    region='us-east-1',
    role=bouncer.role
)


def print_args(event, context):
    """
    Prints out the event and context we were called with.
    """
    print('AWS Role: {}'.format(bouncer.role))

    print('Event:')
    print(event)

    print('')

    print('Context')
    print(context)


@tune.dancer
def hello(event, context):
    """
    Handle the hi lambda.
    """
    print('Hello!')

    print_args(event, context)


@tune.dancer(description='Super cool thing', memory=512)
def goodbye(event, context):
    """
    Handle the other super cool thing.
    """
    print('Goodbye')

    print_args(event, context)
