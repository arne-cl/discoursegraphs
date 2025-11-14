import pytest
from discoursegraphs.corpora import pcc


@pytest.fixture(scope='session')
def maz_1423():
    """these objects/variables are available to all tests in the test suite"""
    return pcc['maz-1423']
