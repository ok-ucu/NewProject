import importlib.util
import json
import stat
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

spec = importlib.util.spec_from_file_location(
    "nova_credentials", Path(__file__).parents[1] / "scripts" / "prepare_nova_credentials.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_private_temp_credentials(monkeypatch, tmp_path, capsys):
    data = {
        "AccessKeyId": "test-only-access",
        "SecretAccessKey": "test-only-secret",
        "SessionToken": "test-only-token",
        "Expiration": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
    }

    def run(args, **kwargs):
        assert args == [
            "aws",
            "configure",
            "export-credentials",
            "--profile",
            "default",
            "--format",
            "process",
        ]
        assert kwargs["capture_output"] and not kwargs.get("shell")
        return SimpleNamespace(returncode=0, stdout=json.dumps(data))

    monkeypatch.setattr(module.subprocess, "run", run)
    real_mkdtemp = module.tempfile.mkdtemp
    monkeypatch.setattr(module.tempfile, "mkdtemp", lambda **kw: real_mkdtemp(dir=tmp_path, **kw))
    result = module.prepare()
    directory = Path(result["directory"])
    assert stat.S_IMODE(directory.stat().st_mode) == 0o700
    assert stat.S_IMODE((directory / "credentials").stat().st_mode) == 0o600
    assert "aws_session_token = test-only-token" in (directory / "credentials").read_text()
    assert "test-only-secret" not in json.dumps(result)
    assert capsys.readouterr().out == ""


@pytest.mark.parametrize(
    "result",
    [
        SimpleNamespace(returncode=1, stdout="sensitive-error-value"),
        SimpleNamespace(returncode=0, stdout="not JSON"),
        SimpleNamespace(returncode=0, stdout='{"AccessKeyId":"static-key"}'),
        SimpleNamespace(
            returncode=0,
            stdout=json.dumps(
                {
                    "AccessKeyId": "x",
                    "SecretAccessKey": "y",
                    "SessionToken": "z",
                    "Expiration": "2000-01-01T00:00:00Z",
                }
            ),
        ),
    ],
)
def test_rejects_bad_or_static_credentials(monkeypatch, result):
    monkeypatch.setattr(module.subprocess, "run", lambda *a, **kw: result)
    with pytest.raises(module.PreparationError) as error:
        module.prepare()
    assert "sensitive-error-value" not in str(error.value)
