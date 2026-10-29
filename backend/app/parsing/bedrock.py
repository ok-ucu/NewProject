"""Shared Messages transport. Importing it never constructs an AWS client."""

import json


def invoke_messages(model_id: str, region: str, prompt: str, max_tokens: int = 1024) -> dict:
    import boto3
    from botocore.config import Config

    client = boto3.client(
        "bedrock-runtime",
        region_name=region,
        config=Config(read_timeout=30, connect_timeout=5, retries={"max_attempts": 0}),
    )
    response = client.invoke_model(
        modelId=model_id,
        contentType="application/json",
        accept="application/json",
        body=json.dumps(
            {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "messages": [{"role": "user", "content": prompt}],
            }
        ),
    )
    return json.loads(response["body"].read())
