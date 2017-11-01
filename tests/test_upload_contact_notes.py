"""
test_upload_contact_notes.py

Test comer_contact_notes.upload_contact_notes module.
"""
from unittest import mock

import pytest
from simple_salesforce import Salesforce

import upload_contact_notes
from salesforce_utils import get_connection


MockSalesforceConnection = mock.create_autospec(Salesforce)

@pytest.fixture(scope="session")
def mock_sf_connection(monkeypatch):
    monkeypatch.setattr(get_connection, "Salesforce", MockSalesforceConnection)


@pytest.fixture()
def comer_data_rows():
    """"""
    return [
        {
        },
        {
        },
    ]

@pytest.fixture()
def blank_data_row():
    return {
    }


class TestUploadContactNotes():

    def test_calls_save_create(self):
        pass

