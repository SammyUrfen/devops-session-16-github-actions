import pytest

from app.calculator import add, divide, multiply, subtract
from app.main import app


def test_add():
    assert add(10, 5) == 15


def test_subtract():
    assert subtract(10, 5) == 5


def test_multiply():
    assert multiply(10, 5) == 50


def test_divide_by_zero():
    with pytest.raises(ValueError):
        divide(10, 0)


@pytest.fixture
def client():
    return app.test_client()


def test_health(client):
    assert client.get("/health").get_json() == {"status": "ok"}


def test_divide_endpoint(client):
    assert client.get("/divide?a=10&b=4").get_json() == {"result": 2.5}


def test_divide_by_zero_endpoint(client):
    assert client.get("/divide?a=1&b=0").status_code == 400


def test_unknown_op(client):
    assert client.get("/power?a=2&b=3").status_code == 404
