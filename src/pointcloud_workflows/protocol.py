"""Versioned subprocess responses, independent of optional data and ML packages."""

import argparse
import json

from . import __version__


VERSION = 1


class ProtocolError(Exception):
    """An expected failure with a stable machine-readable category."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


class ProtocolParser(argparse.ArgumentParser):
    def error(self, message):
        raise ProtocolError("usage_error", message)

    def print_help(self, file=None):
        # argparse also accepts clustered short options such as -hh. Intercept
        # the help action itself before it can write outside the envelope.
        raise ProtocolError("usage_error", "help output does not support protocol mode; use doctor")


def requested(arguments):
    """Recognize even malformed or misplaced version requests before parsing."""
    return any(arg == "--protocol-version" or arg.startswith("--protocol-version=")
               for arg in arguments)


def validate_request(arguments):
    versions = []
    for index, arg in enumerate(arguments):
        if arg == "--protocol-version":
            versions.append(arguments[index + 1] if index + 1 < len(arguments) else None)
        elif arg.startswith("--protocol-version="):
            versions.append(arg.split("=", 1)[1])
    if versions != [str(VERSION)]:
        raise ProtocolError("usage_error", "specify --protocol-version 1 exactly once before the command")
    if any(arg in ("-h", "--help", "--version") for arg in arguments):
        raise ProtocolError("usage_error", "help and version output do not support protocol mode; use doctor")


def command_hint(arguments):
    """Name an attempted command for parse errors; empty when undetermined."""
    remaining = list(arguments)
    if remaining and remaining[0] == "--protocol-version":
        remaining = remaining[2:]
    elif remaining and remaining[0].startswith("--protocol-version="):
        remaining = remaining[1:]
    if not remaining or remaining[0].startswith("-"):
        return ""
    name = remaining[0]
    if name in ("config", "run") and len(remaining) > 1 and not remaining[1].startswith("-"):
        name += " " + remaining[1]
    return name


def encode(command, *, result=None, error=None):
    """Serialize the entire envelope before writing anything to stdout."""
    return json.dumps({
        "protocol_version": VERSION,
        "pcw_version": __version__,
        "command": command,
        "ok": error is None,
        "result": result if error is None else None,
        "error": None if error is None else {"code": error.code, "message": str(error)},
    }, allow_nan=False)
