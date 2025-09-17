from collector import CivitaiPromptCollector

def test_collector_instantiation():
    c = CivitaiPromptCollector(db_path=":memory:")
    assert c is not None

def test_collector_requests():
    import requests
    assert requests is not None

def test_collector_numpy():
    import numpy
    assert numpy is not None

def test_collector_matplotlib():
    import matplotlib
    assert matplotlib is not None

def test_collector_pytest():
    import pytest
    assert pytest is not None
