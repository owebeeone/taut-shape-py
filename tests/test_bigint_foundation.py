"""The shape package must expose the application's actual bigint-capable owner."""
import pytest
from taut.wire import cbor as canonical
from taut_shape.foundation import cbor


@pytest.mark.parametrize("n", [0, -1, 5, -5, 2**8192, -(2**8192)])
def test_bigint_foundation_round_trip(n):
    assert cbor is canonical
    encoded = cbor.dumps(cbor.Bignum(n))
    value = cbor.loads(encoded)
    assert isinstance(value, cbor.Bignum)
    assert value.value == n
    assert cbor.dumps(value) == encoded


def test_bigint_foundation_refuses_redundant_zero():
    with pytest.raises(cbor.DecodeError) as error:
        cbor.loads(bytes.fromhex("c24100"))
    assert error.value.tag == "NonCanonicalBigInt"
