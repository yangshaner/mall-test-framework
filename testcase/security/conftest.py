# testcase/security/conftest.py
import pytest
import requests

from common.client.admin_client import AdminClient
from common.client.member_client import MemberClient
from common.config.config_loader import config


@pytest.fixture(scope="session")
def anon_session():
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Accept": "application/json",
    })
    return session


@pytest.fixture(scope="session")
def member_base_url():
    return config.get("member", {}).get("base_url", "").rstrip('/')


@pytest.fixture(scope="session")
def admin_base_url():
    return config.get("admin", {}).get("base_url", "").rstrip('/')


@pytest.fixture(scope="function")
def admin_client_factory():
    clients = []

    def _create(username, password=None):
        client = AdminClient(username=username)
        if password:
            client._password = password
        client._login()
        clients.append(client)
        return client

    yield _create

    for c in clients:
        try:
            c.clear_token()
        except Exception:
            pass


@pytest.fixture(scope="function")
def member_client_factory():
    clients = []

    def _create(username, password=None):
        client = MemberClient(username=username)
        if password:
            client._password = password
        client._login()
        clients.append(client)
        return client

    yield _create

    for c in clients:
        try:
            c.clear_token()
        except Exception:
            pass