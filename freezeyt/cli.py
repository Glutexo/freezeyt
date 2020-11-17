import importlib

import click
import yaml

from freezeyt.freezing import freeze


@click.command()
@click.argument('module_name')
@click.argument('dest_path')
@click.option('--prefix', help='URL of the application root')
@click.option('--extra-page', multiple=True, help='Pages without any link in application')
@click.option('-c', '--config', type=click.File(), help='YAML file of configuration')
def main(module_name, dest_path, prefix, extra_page, config):
    """
    MODULE_NAME
        Name of the Python web app module which will be frozen.

    DEST_PATH
        Absolute or relative path to the directory to which the files
    will be frozen.

    --prefix
        URL, where we want to deploy our static site

    --extra-page
        Path to page without any link in application

    -c / --config
        Path to configuration YAML file

    Example use:
        python -m freezeyt demo_app build --prefix 'http://localhost:8000/' --extra-page /extra/

        python -m freezeyt demo_app build -c config.yaml
    """
    cli_params = {
        'extra_pages': list(extra_page)
    }

    if prefix != None:
        cli_params['prefix'] = prefix

    if config != None:
        file_config = yaml.safe_load(config)

        if not isinstance(file_config, dict):
            raise SyntaxError(
                    f'File {config.name} is not prepared as YAML dictionary.'
                    )
        else:
            print("Loading config YAML file was successful")

            if (file_config.get('prefix', None) != None) and (prefix is None):
                cli_params['prefix'] = file_config['prefix']

            if file_config.get('extra_pages', None) != None:
                cli_params['extra_pages'].extend(file_config['extra_pages'])

            cli_params['extra_files'] = file_config.get('extra_files', None)

    module = importlib.import_module(module_name)
    app = module.app

    freeze(app, dest_path, cli_params)
