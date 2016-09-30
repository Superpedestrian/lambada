Lambada
-------
.. image:: https://img.shields.io/travis/Superpedestrian/lambada.svg
  :target: https://travis-ci.org/Superpedestrian/lambada
  :alt: Build status
.. image:: https://img.shields.io/coveralls/Superpedestrian/lambada.svg
  :target: https://coveralls.io/r/Superpedestrian/lambada
  :alt: Coverage
.. image:: https://img.shields.io/pypi/v/lambada.svg
  :target: https://pypi.python.org/pypi/lambada
  :alt: 'PyPI Package'
.. image:: https://readthedocs.org/projects/lambada/badge/?version=latest
  :target: http://lambada.readthedocs.io/en/latest/?badge=latest
  :alt: Latest Documentation
.. image:: https://readthedocs.org/projects/lambada/badge/?version=release
  :target: :target: http://lambada.readthedocs.io/en/latest/?badge=release
  :alt: Release Documentation


A flask like framework for building multiple lambdas in one
library/package by utilizing `lambda-uploader
<https://pypi.python.org/pypi/lambda-uploader>`_.


Quickstart
==========


All you'll need to do to create a minimal lambada application is to
add the following to a file called ``lambda.py`` :

.. code-block:: python

    from lambada import Lambada

    tune = Lambada(role='arn:aws:iam:xxxxxxx:role/lambda')


    @tune.dancer
    def test_lambada(event, context):
        print('Event: {}'.format(event))

and a ``requirements.txt`` file that includes the lambada package
(either ``lambada`` or ``https://github.com/Superpedestrian/lambada``
for the latest release or developer version respectively.

Much like a flask app, we now have a python file that is configured to
upload a lambda function with the name ``test_lambada`` in your AWS
account in the ``us-east-1`` region (since that is the default), and
the handler will be set to ``lamda.tune``, again the default.

So what is this doing over just writing the same thing without this framework?

For one it gives you a command line toolset to test, list, and publish
multiple functions to AWS as independant Lambda's with one code base.

Now that you have your code, you can run the ``lambada`` command line
tool after running ``pip install -r requirements.txt`` to do something
like ``lambada list``

::

    List of discovered lambda functions/dancers:

    test_lambada:
        description:

You can also test that lambda with an event passed on the command line
using ``lambada run test_lambada --event 'Hello'`` to get:

::

    Event: Hello

which creates a faked AWS Context object before running the specified
*dancer*.

From there we can also package the functions (the same package works
for all defined *dancers*/Lambda functions).  So without configuring
any AWS credentials, we can run ``lambada package`` to create a zip
file with all your requirements packaged up (from the earlier created
``requirements.txt``) that you can manually upload to AWS Lambda
through the Web interface or similar.

If you have your AWS API credentials setup, and the correct
permissions, you can also run ``lambada upload`` to have the function
created and/or versioned with the packaged code for each *dancer*.

Pretty neat so far, but where it starts to get cool is when there are
many *dancers* with different requirements, VPCs, timeouts, and memory
requirements all in the same deployable package similar to the
following.  We're going to go ahead and call our file
``fouronthefloor.py`` just as a reference for the customization you
can do, so the contents of ``fouronthefloor.py`` would look like:

.. code-block:: python

    from lambada import Lambada

    chart = Lambada(
        handler='fouronthefloor.chart',
        role='arn:aws:iam:xxxxxxx:role/lambda',
        region='us-west-2',
        timeout=60,
        memory=128
    )


    @chart.dancer
    def test_lambada(event, context):
        print('Event: {}'.format(event))


    @chart.dancer(
        name='not_the_function_name',
        description='Cool description',
        memory=512,
        region='us-east-1',
        requirements=['requirements.txt', 'xtra_requirements.txt']
    )
    def cool_oneoff(event, context):
        print('Wow, so much memory! in a diff region and extra reqs!')


    @chart.dancer(memory=1024, timeout=5)
    def bob_loblaw(event, _):
        print('Such a great reference!')

Which gives a ``lambada list`` that looks like:

::

    List of discovered lambda functions/dancers:

    bob_loblaw:
        description:
        timeout: 5
        memory: 1024

    test_lambada:
        description:

    not_the_function_name:
        description: Cool description
        region: us-east-1
        requirements: ['requirements.txt', 'xtra_requirements.txt']
        memory: 512
                
And with a few lines we've created three lambdas with different execution
requirements all with one ``lambada upload`` command. Such a simple
seductive dance 😜.
