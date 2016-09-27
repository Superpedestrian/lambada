"""
Sample lambda library using lambada for use in multiple AWSXS lambdas.
"""
from __future__ import unicode_literals, print_function
import logging
from os import environ

from lambada import Lambada

logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.DEBUG)

tune = Lambada(
    handler='lambda.tune',
    region='us-east-1',
    role=environ.get('LAMBADA_ROLE')
)


def print_args(event, context):
    """
    Prints out the event and context we were called with.
    """
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
