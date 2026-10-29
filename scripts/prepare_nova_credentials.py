#!/usr/bin/env python3
"""Export short-lived CLI credentials privately OUTSIDE the repo; never invoke Bedrock."""

import argparse
import configparser
import io
import json
import os
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path


class PreparationError(Exception):
    pass


def prepare(profile="default"):
    # Capture credentials in memory. Never use shell eval, print raw output or log errors.
    result = subprocess.run(
        ["aws", "configure", "export-credentials", "--profile", profile, "--format", "process"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        raise PreparationError("AWS credentials unavailable. Run aws login --profile " + profile)
    try:
        data = json.loads(result.stdout)
        required = ("AccessKeyId", "SecretAccessKey", "SessionToken", "Expiration")
        if not all(isinstance(data.get(k), str) and data[k] for k in required):
            raise ValueError("Short-lived credentials required")
        expiration = datetime.fromisoformat(data["Expiration"].replace("Z", "+00:00"))
        if (
            expiration.tzinfo is None
            or (expiration - datetime.now(timezone.utc)).total_seconds() < 300
        ):
            raise ValueError("Session expired or expires too soon")
        config = configparser.RawConfigParser()
        config["default"] = {
            "aws_access_key_id": data["AccessKeyId"],
            "aws_secret_access_key": data["SecretAccessKey"],
            "aws_session_token": data["SessionToken"],
        }
        output = io.StringIO()
        config.write(output)
    except (ValueError, TypeError, KeyError):
        raise PreparationError(
            "A valid temporary AWS session is required. Re-run aws login."
        ) from None
    # Always create a new private OS temporary directory, never a repo file or ~/.aws copy.
    directory = Path(tempfile.mkdtemp(prefix="spry-nova-aws-"))
    os.chmod(directory, 0o700)
    credentials = directory / "credentials"
    fd = os.open(credentials, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as target:
        target.write(output.getvalue())
    return {"directory": str(directory), "expiration": expiration.isoformat(), "profile": profile}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", default="default")
    parser.add_argument("--directory-only", action="store_true")
    args = parser.parse_args()
    try:
        prepared = prepare(args.profile)
        print(prepared["directory"] if args.directory_only else json.dumps(prepared))
    except (PreparationError, OSError) as exc:
        # OSError text can include local paths; never dump subprocess stdout/stderr.
        message = (
            str(exc)
            if isinstance(exc, PreparationError)
            else "Local credential preparation failed."
        )
        parser.exit(1, message + "\n")


if __name__ == "__main__":
    main()
