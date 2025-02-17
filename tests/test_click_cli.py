import pytest
from yaml import safe_dump
from click.testing import CliRunner

from freezeyt.cli import main
from testutil import FIXTURES_PATH, context_for_test, assert_dirs_same

APP_NAMES = [
    p.name
    for p in FIXTURES_PATH.iterdir()
    if (p / 'app.py').exists() and (p / 'test_expected_output').exists()
]


def run_freezeyt_cli(cli_args, app_name, check=True):
    app_dir = FIXTURES_PATH / app_name

    runner = CliRunner(env={'PYTHONPATH': str(app_dir)})

    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.syspath_prepend(app_dir)
        result = runner.invoke(main, cli_args)

    print(result.stdout)

    if check:
        if result.exception is not None:
            raise result.exception
        assert result.exit_code == 0

    return result


def run_and_check(cli_args, app_name, build_dir):
    error_path = FIXTURES_PATH / app_name / 'error.txt'
    expected = FIXTURES_PATH / app_name / 'test_expected_output'

    result = run_freezeyt_cli(cli_args, app_name, check=False)

    if error_path.exists():
        assert result.exit_code != 0

    else:
        if result.exception is not None:
            raise result.exception
        assert result.exit_code == 0

        assert_dirs_same(build_dir, expected)


@pytest.mark.parametrize('app_name', APP_NAMES)
def test_cli_with_fixtures_output(tmp_path, app_name):
    config_file = tmp_path / 'config.yaml'
    build_dir = tmp_path / 'build'

    with context_for_test(app_name) as module:
        cli_args = ['app', str(build_dir)]
        freeze_config = getattr(module, 'freeze_config', None)

        if not getattr(module, 'config_is_serializable', True):
            pytest.skip('Config is not serializable')

        if freeze_config != None:
            with open(config_file, mode='w') as file:
                safe_dump(freeze_config, stream=file)

            cli_args.extend(['--config', config_file])

        run_and_check(cli_args, app_name, build_dir)


def test_cli_with_prefix_option(tmp_path):
    app_name = 'app_url_for_prefix'
    build_dir = tmp_path / 'build'

    with context_for_test(app_name,) as module:
        freeze_config = getattr(module, 'freeze_config')
        prefix = freeze_config['prefix']
        cli_args = ['app', str(build_dir), '--prefix', prefix]

        run_and_check(cli_args, app_name, build_dir)


def test_cli_with_config_variable(tmp_path):
    app_name = 'app_with_extra_files'
    build_dir = tmp_path / 'build'

    with context_for_test(app_name,):
        cli_args = ['app', str(build_dir), '--import-config', 'app:freeze_config']

        run_and_check(cli_args, app_name, build_dir)


def test_cli_with_extra_page_option(tmp_path):
    app_name = 'app_with_extra_page_deep'
    build_dir = tmp_path / 'build'

    with context_for_test(app_name) as module:
        cli_args = ['app', str(build_dir)]

        freeze_config = getattr(module, 'freeze_config')

        extra_pages = []
        for extra in freeze_config['extra_pages']:
            extra_pages.append('--extra-page')
            extra_pages.append(extra)

        cli_args.extend(extra_pages)

        run_and_check(cli_args, app_name, build_dir)


def test_cli_prefix_conflict(tmp_path):
    app_name = 'app_url_for_prefix'
    config_file = tmp_path / 'config.yaml'
    build_dir = tmp_path / 'build'

    with context_for_test(app_name) as module:
        freeze_config = getattr(module, 'freeze_config')
        prefix = freeze_config['prefix']
        cli_args = ['app', str(build_dir), '--prefix', prefix]

        data = {'prefix': 'http://pyladies.cz/lessons/'}
        with open(config_file, mode='w') as file:
            safe_dump(data, stream=file)

        cli_args.extend(['--config', config_file])

        run_and_check(cli_args, app_name, build_dir)


def test_nonstandard_app_name(tmp_path):
    build_dir = tmp_path / 'build'
    run_and_check(
        ['application:wsgi_application', str(build_dir)],
        'app_nonstandard_name',
        build_dir,
    )


def test_nonstandard_dotted_app_name(tmp_path):
    build_dir = tmp_path / 'build'
    run_and_check(
        ['application:obj.app', str(build_dir)],
        'app_nonstandard_name',
        build_dir,
    )


def test_cleanup_config_works_if_runs_from_cli(tmp_path):
    app_name = 'app_cleanup_config'
    build_dir = tmp_path / 'build'

    with context_for_test(app_name):
        cli_args = ['app', str(build_dir), '--import-config', 'app:freeze_config']
        run_and_check(cli_args, app_name, build_dir)
    assert build_dir.exists()
    assert (build_dir / 'index.html').exists()


def test_cleanup_from_cli_has_higher_priority(tmp_path):
    app_name = 'app_cleanup_config'
    build_dir = tmp_path / 'build'

    with context_for_test(app_name):
        cli_args = ['app', str(build_dir), '--cleanup', '--import-config', 'app:freeze_config']
        run_and_check(cli_args, app_name, build_dir)
    assert not build_dir.exists()

