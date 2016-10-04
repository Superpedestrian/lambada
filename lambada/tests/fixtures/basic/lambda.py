# -*- coding: utf-8 -*-
"""
Basic sample lambada module
"""
from __future__ import print_function
from lambada import Lambada

tune = Lambada(role='arn:aws:iam:xxxxxxx:role/lambda')
CONSTANT = 'asdf'


def print_return(event):
    """Print and return event."""
    event = 'Event: {}'.format(event)
    print(event)
    return event


@tune.dancer
def test_lambada(event, _):
    """Print the event we created"""
    return print_return(event)


@tune.dancer(name='hi')
def test_named(event, _):
    """Print the event we created"""
    return print_return(event)


@tune.dancer()
def test_argless(event, _):
    """Print the event we created"""
    return print_return(event)


@tune.dancer(memory=4242, region='us-west-2')
def test_multiarg(event, _):
    """Print the event we created"""
    return print_return(event)
