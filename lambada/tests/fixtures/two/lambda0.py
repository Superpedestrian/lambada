# -*- coding: utf-8 -*-
"""
Basic sample lambada module
"""
from __future__ import print_function
from lambada import Lambada

tune = Lambada(role='arn:aws:iam:xxxxxxx:role/lambda')
CONSTANT = 'asdf'


@tune.dancer
def lambda0(event, _):
    """Print the event we created"""
    print('Event: {}'.format(event))  # pragma: no cover
