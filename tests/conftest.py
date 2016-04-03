
from discoursegraphs.corpora import pcc


def pytest_namespace():
    """these objects/variables are available to all tests in the test suite"""
    return {'maz_1423': pcc['maz-1423']}
