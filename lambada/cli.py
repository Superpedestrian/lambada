# -*- coding: utf-8 -*-
"""
Command line interface for running, packaging,
and uploading commands to AWS.
"""
import io
import os

import click
from lambda_uploader.package import build_package
from lambda_uploader.uploader import PackageUploader
from six import iteritems

from lambada.common import get_lambada_class, LambadaConfig, LambdaContext

ZIPFILE_UPLOAD_NAME = 'lambada.zip'


def create_package(path, tune, requirements, destination=ZIPFILE_UPLOAD_NAME):
    """
    Creates and returns the package using :py:mod:`lambda_uploader`.
    """

    if os.path.isfile(path):
        path = os.path.dirname(path)
    path = os.path.abspath(path)
    # Write out bouncer configuration for package
    bouncer_config = os.path.join(path, '_lambada.yml')
    with io.open(bouncer_config, 'w', encoding='UTF-8') as bouncer_yaml:
        tune.bouncer.export(bouncer_yaml)
    pkg = build_package(
        path,
        requirements,
        virtualenv=None,
        ignore=tune.config['ignore_files'],
        extra_files=tune.config['extra_files'],
        zipfile_name=destination
    )
    pkg.clean_workspace()
    os.remove(bouncer_config)
    return pkg


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
    for _, dancer in iteritems(obj['tune'].dancers):
        click.echo()
        click.echo('{}:'.format(dancer.name))
        indent_echo('description: {}'.format(dancer.description))
        for (key, value) in dancer.override_config.items():
            indent_echo('{}: {}'.format(key, value))


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
    create_package(obj['path'], obj['tune'], requirements, destination)


@cli.command()
@click.argument('dancer', required=False)
@click.option(
    '--requirements',
    default='./requirements.txt',
    envvar='LAMBADA_REQUIREMENTS',
    help='Path to requirements.txt to include in package',
    type=click.Path(exists=True, dir_okay=False)
)
@click.pass_obj
def upload(obj, requirements, dancer):
    """
    Upload all lambda functions.
    """
    tune = obj['tune']
    click.echo('Creating package')
    pkg = create_package(
        obj['path'], obj['tune'], requirements
    )

    def upload_dancer(dancer):
        """
        Uploads the given dancer.
        """
        config_dict = tune.config.copy()
        config_dict.update(dancer.config)
        config = LambadaConfig(obj['path'], config_dict)
        click.echo('Uploading Package for {}'.format(dancer.name))
        uploader = PackageUploader(config, None)
        uploader.upload(pkg)

    if dancer:
        dancer_obj = tune.dancers.get(dancer, None)
        if dancer_obj is None:
            raise click.ClickException(
                "Dancer {} doesn't exist".format(dancer)
            )
        upload_dancer(dancer_obj)
    else:
        for _, dancer in iteritems(tune.dancers):
            upload_dancer(dancer)
    pkg.clean_zipfile()
