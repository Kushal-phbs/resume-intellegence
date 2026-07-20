from pathlib import Path

from app.config.settings import Settings


def test_settings_env_file_path_is_resolved_relative_to_backend() -> None:
    expected = Path(__file__).resolve().parents[1] / ".env"
    env_file = Settings.model_config["env_file"]

    assert Path(env_file).resolve() == expected.resolve()
