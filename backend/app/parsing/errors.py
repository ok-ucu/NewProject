"""Allowlisted SDK error metadata only. Never log exception text, headers or input."""

import re

from botocore.exceptions import BotoCoreError, ClientError

CATEGORIES = {
    "ThrottlingException": "throttling",
    "TooManyRequestsException": "throttling",
    "ServiceQuotaExceededException": "quota",
    "LimitExceededException": "quota",
    "AccessDeniedException": "authorization_or_model_access",
    "ExpiredTokenException": "credentials_expired_or_invalid",
    "ExpiredToken": "credentials_expired_or_invalid",
    "UnrecognizedClientException": "credentials_expired_or_invalid",
    "InvalidClientTokenId": "credentials_expired_or_invalid",
    "InvalidSignatureException": "credentials_expired_or_invalid",
    "SignatureDoesNotMatch": "credentials_expired_or_invalid",
    "ValidationException": "invalid_request_or_model_profile",
    "ResourceNotFoundException": "model_or_profile_not_found",
    "ModelNotReadyException": "model_not_ready",
    "ModelTimeoutException": "model_timeout",
    "InternalServerException": "service_error",
    "ServiceUnavailableException": "service_unavailable",
    "ModelErrorException": "model_error",
}
SDK_CATEGORIES = {
    "NoCredentialsError": "credentials_unavailable",
    "PartialCredentialsError": "credentials_unavailable",
    "CredentialRetrievalError": "credentials_unavailable",
    "TokenRetrievalError": "credentials_unavailable",
    "SSOTokenLoadError": "credentials_unavailable",
    "UnauthorizedSSOTokenError": "credentials_expired_or_invalid",
    "ParamValidationError": "local_request_validation",
    "ReadTimeoutError": "network_timeout",
    "ConnectTimeoutError": "network_timeout",
    "EndpointConnectionError": "network_connection",
    "ConnectionClosedError": "network_connection",
    "SSLError": "network_tls",
}


def safe_provider_error(exc: Exception) -> dict:
    result = {
        "aws_error_code": None,
        "aws_http_status": None,
        "aws_request_id": None,
        "error_category": "invalid_response",
        "sdk_error_type": None,
    }
    if isinstance(exc, ClientError):
        payload = exc.response if isinstance(exc.response, dict) else {}
        error = payload.get("Error", {})
        meta = payload.get("ResponseMetadata", {})
        error = error if isinstance(error, dict) else {}
        meta = meta if isinstance(meta, dict) else {}
        code = error.get("Code")
        known = isinstance(code, str) and code in CATEGORIES
        result["aws_error_code"] = code if known else "UnknownClientError"
        result["error_category"] = CATEGORIES[code] if known else "unknown_aws_error"
        result["sdk_error_type"] = "ClientError"
        status = meta.get("HTTPStatusCode")
        if type(status) is int and 100 <= status <= 599:
            result["aws_http_status"] = status
        request_id = meta.get("RequestId")
        if isinstance(request_id, str) and re.fullmatch(r"[A-Za-z0-9-]{1,128}", request_id):
            result["aws_request_id"] = request_id
    else:
        kind = type(exc).__name__
        if kind in SDK_CATEGORIES:
            result["sdk_error_type"] = kind
            result["error_category"] = SDK_CATEGORIES[kind]
        elif isinstance(exc, BotoCoreError):
            result["sdk_error_type"] = "OtherBotoCoreError"
            result["error_category"] = "sdk_error"
        # All other parsing/SDK exception details are deliberately omitted.
    return result
