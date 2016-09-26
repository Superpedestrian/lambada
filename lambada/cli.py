"""
Command line interface for running, packaging,
and uploading commands to AWS.
"""
import os

import click
from lambda_uploader.package import build_package

from lambada.common import get_lambada_class, LambdaContext


@click.group()
@click.option(
    '--path',
    default='./',
    envvar='LAMBADA_PATH',
    help='Path to the python file with your Lambada class declaration.',
    type=click.Path(exists=True)
)
@click.pass_context
def cli(context, path):
    """
    Execute, package, and upload all of your lambda functions
    """
    tune = get_lambada_class(path)
    if not tune:
        raise click.ClickException('Unable to find Lambada class declaration')
    context.obj = dict(tune=tune, path=path)


@cli.command(name='list')
@click.pass_obj
def list_dancers(obj):
    """
    Lists all of the discovered lambda commands
    """
    def indent_echo(item):
        """Adds 4 spaces to item and echos it."""
        click.echo('{}{}'.format(' ' * 4, item))

    click.echo('List of discovered lambda functions/dancers:')
    for _, dancer in obj['tune'].dancers.iteritems():
        click.echo('{}:'.format(dancer.name))
        indent_echo('description: {}'.format(dancer.description))
        indent_echo('timeout: {}'.format(dancer.timeout))
        indent_echo('memory: {}'.format(dancer.memory))
        click.echo()


@cli.command()
@click.option(
    '--event',
    default='test',
    help='Event string to pass to your dancer.'
)
@click.argument('dancer')
@click.pass_obj
def run(obj, dancer, event):
    """
    Runs a given function with a given event and a simulated context.
    """
    context = LambdaContext(function_name=dancer)
    obj['tune'](event, context)


@cli.command()
@click.option(
    '--destination',
    default='lambda.zip',
    envvar='LAMBADA_PACKAGE_DESTINATION',
    help='name of zip file you would like to create',
    type=click.Path(exists=False, dir_okay=False)
)
@click.option(
    '--requirements',
    default='./requirements.txt',
    envvar='LAMBADA_REQUIREMENTS',
    help='Path to requirements.txt to include in package',
    type=click.Path(exists=True, dir_okay=False)
)
@click.pass_obj
def package(obj, requirements, destination):
    """
    Creates a zip file with everything needed to upload to AWS Lambda
    manually.  Useful for checking everything out before uploading.
    """
    path = obj['path']
    tune = obj['tune']
    if os.path.isfile(path):
        path = os.path.dirname(path)
    path = os.path.abspath(path)
    pkg = build_package(
        path,
        requirements,
        virtualenv=None,
        ignore=tune.config['ignore_files'],
        extra_files=tune.config['extra_files'],
        zipfile_name=destination
    )
    pkg.clean_workspace()
