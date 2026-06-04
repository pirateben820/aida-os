"""Tests for the capability/permission system."""
import pytest

from capabilities.model import CapabilityRegistry


@pytest.fixture
def caps():
    return CapabilityRegistry()


def test_archon_can_read_files(caps):
    assert caps.check("archon", "read_files") is True


def test_archon_cannot_manage_secrets(caps):
    assert caps.check("archon", "manage_secrets") is False


def test_security_require_local(caps):
    # security agent should not have external network access
    assert caps.check("security", "network_access_external") is False


def test_require_raises_on_deny(caps):
    with pytest.raises(PermissionError):
        caps.require("hermes", "execute_shell")


def test_unknown_agent_denied(caps):
    assert caps.check("unknown_agent", "read_files") is False
