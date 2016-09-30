# -*- coding: utf-8 -*-
"""
Basic sample lambada module
"""
from lambada import Lambada

tune = Lambada(role='arn:aws:iam:xxxxxxx:role/lambda')
CONSTANT = 'asdf'


@tune.dancer
def test_lambada(event, _):
    """Print the event we created"""
    return 'Event: {}'.format(event)


@tune.dancer(name='hi')
def test_named(event, _):
    """Print the event we created"""
    return 'Event: {}'.format(event)


@tune.dancer()
def test_argless(event, _):
    """Print the event we created"""
    return 'Event: {}'.format(event)


@tune.dancer(memory=4242, region='us-west-2')
def test_multiarg(event, _):
    """Print the event we created"""
    return 'Event: {}'.format(event)
