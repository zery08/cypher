from app.core.config import Settings


def test_cors_origins_accepts_single_env_string():
    settings = Settings(
        cors_origins="http://localhost:5173",
        llm_api_key="test-key",
    )

    assert settings.cors_origins == ["http://localhost:5173"]


def test_cors_origins_accepts_comma_separated_string():
    settings = Settings(
        cors_origins="http://localhost:5173,https://example.com",
        llm_api_key="test-key",
    )

    assert settings.cors_origins == ["http://localhost:5173", "https://example.com"]


def test_settings_accept_zai_env_aliases(monkeypatch):
    monkeypatch.setenv("ZAI_API_KEY", "zai-test-key")
    monkeypatch.setenv("ZAI_MODEL", "glm-4.7")
    settings = Settings(_env_file=None)

    assert settings.llm_api_key == "zai-test-key"
    assert settings.llm_model == "glm-4.7"


def test_settings_still_accept_openai_compat_aliases(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "compat-test-key")
    monkeypatch.setenv("OPENAI_MODEL", "glm-4.7")
    settings = Settings(_env_file=None)

    assert settings.llm_api_key == "compat-test-key"
    assert settings.llm_model == "glm-4.7"


def test_settings_uses_backend_env_file_from_any_cwd(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text("ZAI_API_KEY=test-key\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    settings = Settings(_env_file=env_file)

    assert settings.llm_api_key == "test-key"
