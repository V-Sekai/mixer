# GPLv3 License
#
# Copyright (C) 2020 Ubisoft
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
Fuzzing tests for codec and message handling using hypothesis.

This module tests the JSON codec and message encoding/decoding operations
with randomly generated data to ensure robustness.
"""

import json
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck

from mixer.blender_data.json_codec import Codec, EncodeError, DecodeError
from mixer.blender_data.proxy import Proxy, Delta, DeltaUpdate, DeltaAddition, DeltaDeletion
from mixer.blender_data.messages import BlenderDataMessage, BlenderRemoveMessage, BlenderRenamesMessage

# Strategies for generating test data
@st.composite
def random_json_like_data(draw, max_depth=3):
    """Generate random JSON-like data structures."""
    if max_depth <= 0:
        return draw(st.one_of(
            st.none(),
            st.booleans(),
            st.integers(-1000, 1000),
            st.floats(-1000, 1000, allow_nan=False, allow_infinity=False),
            st.text(st.characters(whitelist_categories=('L', 'N', 'P', 'S', 'Zs')), max_size=50)
        ))

    return draw(st.one_of(
        st.none(),
        st.booleans(),
        st.integers(-1000, 1000),
        st.floats(-1000, 1000, allow_nan=False, allow_infinity=False),
        st.text(st.characters(whitelist_categories=('L', 'N', 'P', 'S', 'Zs')), max_size=50),
        st.lists(random_json_like_data(max_depth - 1), min_size=0, max_size=10),
        st.dictionaries(
            st.text(st.characters(whitelist_categories=('L', 'N', 'P', 'S')), max_size=20),
            random_json_like_data(max_depth - 1),
            min_size=0, max_size=10
        )
    ))

@st.composite
def random_proxy_like_data(draw):
    """Generate random data that might be serialized as a proxy."""
    return {
        '_type': draw(st.sampled_from(['StructProxy', 'DatablockProxy', 'DeltaUpdate', 'DeltaAddition'])),
        '_data': draw(random_json_like_data()),
        'mixer_uuid': draw(st.uuids()).hex if draw(st.booleans()) else None,
    }

@st.composite
def random_binary_data(draw):
    """Generate random binary data for codec testing."""
    return draw(st.binary(min_size=0, max_size=10000))

@given(data=random_binary_data())
@settings(max_examples=100, deadline=500, suppress_health_check=[HealthCheck.too_slow])
def test_codec_decode_fuzzing(data):
    """Test codec decode operations with random binary data."""
    codec = Codec()

    try:
        # This should not crash even with completely random data
        result = codec.decode(data)

        # If decoding succeeds, result should be a valid proxy or delta
        if result is not None:
            assert isinstance(result, (Proxy, Delta))

    except (DecodeError, json.JSONDecodeError, UnicodeDecodeError):
        # Expected for invalid data - codec should handle gracefully
        pass
    except Exception as e:
        # Other exceptions indicate bugs
        pytest.fail(f"Codec decode failed unexpectedly: {e}")

@given(proxy_data=random_proxy_like_data())
@settings(max_examples=50, deadline=1000)
def test_codec_encode_fuzzing(proxy_data):
    """Test codec encode operations with random proxy-like data."""
    codec = Codec()

    # Create a mock proxy object
    class MockProxy(Proxy):
        def __init__(self, data):
            super().__init__()
            self._data = data
            self._type = data.get('_type', 'MockProxy')

    mock_proxy = MockProxy(proxy_data)

    try:
        # Test encoding
        encoded = codec.encode(mock_proxy)
        assert isinstance(encoded, bytes)
        assert len(encoded) > 0

        # Test round-trip: decode what we encoded
        decoded = codec.decode(encoded)
        assert decoded is not None

    except EncodeError:
        # Expected for some invalid proxy structures
        pass
    except Exception as e:
        pytest.fail(f"Codec encode failed unexpectedly: {e}")

@given(
    message_data=random_json_like_data(),
    uuid_str=st.uuids().map(lambda x: x.hex)
)
@settings(max_examples=30, deadline=1000)
def test_blender_data_message_fuzzing(message_data, uuid_str):
    """Test BlenderDataMessage operations with random data."""
    try:
        # Create a mock datablock proxy
        class MockDatablockProxy:
            def __init__(self, data, uuid):
                self.data = data
                self.mixer_uuid = uuid

        mock_proxy = MockDatablockProxy(message_data, uuid_str)

        # Test message creation and encoding
        message = BlenderDataMessage()
        encoded = message.encode(mock_proxy, json.dumps(message_data))

        assert isinstance(encoded, bytes)
        assert len(encoded) > 0

        # Test message decoding
        decoded_message = BlenderDataMessage()
        index = decoded_message.decode(encoded)
        assert index >= 0

    except Exception as e:
        pytest.fail(f"BlenderDataMessage operations failed: {e}")

@given(uuid_str=st.uuids().map(lambda x: x.hex))
@settings(max_examples=20, deadline=500)
def test_blender_remove_message_fuzzing(uuid_str):
    """Test BlenderRemoveMessage operations with random UUIDs."""
    try:
        # Test message encoding
        encoded = BlenderRemoveMessage.encode(uuid_str, "test_debug_info")

        assert isinstance(encoded, bytes)
        assert len(encoded) > 0

        # Test message decoding
        message = BlenderRemoveMessage()
        message.decode(encoded)

        assert message.uuid == uuid_str

    except Exception as e:
        pytest.fail(f"BlenderRemoveMessage operations failed: {e}")

@given(
    renames=st.lists(
        st.tuples(
            st.uuids().map(lambda x: x.hex),
            st.text(st.characters(whitelist_categories=('L', 'N', 'P', 'S')), max_size=50),
            st.text(st.characters(whitelist_categories=('L', 'N', 'P', 'S')), max_size=50)
        ),
        min_size=0, max_size=10
    )
)
@settings(max_examples=20, deadline=500)
def test_blender_renames_message_fuzzing(renames):
    """Test BlenderRenamesMessage operations with random rename data."""
    try:
        # Convert renames to the expected format
        renames_data = [f"{uuid}:{old_name}:{new_name}" for uuid, old_name, new_name in renames]

        # Test message encoding
        encoded = BlenderRenamesMessage.encode(renames_data)

        assert isinstance(encoded, bytes)
        assert len(encoded) > 0

        # Test message decoding
        message = BlenderRenamesMessage()
        message.decode(encoded)

        # Verify decoded data matches input
        assert len(message.renames) == len(renames_data)
        for i, rename_str in enumerate(message.renames):
            assert rename_str == renames_data[i]

    except Exception as e:
        pytest.fail(f"BlenderRenamesMessage operations failed: {e}")

@given(
    json_str=st.text(st.characters(whitelist_categories=('L', 'N', 'P', 'S', 'Zs', 'Z', 'C')), max_size=1000)
)
@settings(max_examples=50, deadline=500)
def test_json_codec_edge_cases(json_str):
    """Test JSON codec with malformed JSON strings."""
    codec = Codec()

    try:
        # Try to encode a string that might not be valid JSON
        # This tests the codec's error handling
        data = {"test": json_str}
        encoded = codec.encode(data)
        assert isinstance(encoded, bytes)

        # Try to decode it back
        decoded = codec.decode(encoded)
        assert decoded == data

    except (EncodeError, DecodeError, json.JSONDecodeError, UnicodeDecodeError):
        # Expected for malformed data
        pass
    except Exception as e:
        pytest.fail(f"JSON codec edge case failed: {e}")

@given(
    nested_data=st.recursive(
        st.one_of(
            st.none(),
            st.booleans(),
            st.integers(),
            st.floats(allow_nan=False, allow_infinity=False),
            st.text(max_size=50)
        ),
        lambda children: st.one_of(
            st.lists(children, max_size=5),
            st.dictionaries(st.text(max_size=20), children, max_size=5)
        ),
        max_leaves=20
    )
)
@settings(max_examples=30, deadline=1000)
def test_codec_nested_structures(nested_data):
    """Test codec with deeply nested data structures."""
    codec = Codec()

    try:
        # Test encoding nested structures
        encoded = codec.encode(nested_data)
        assert isinstance(encoded, bytes)

        # Test decoding back
        decoded = codec.decode(encoded)
        assert decoded == nested_data

    except (EncodeError, DecodeError, json.JSONDecodeError, UnicodeDecodeError, RecursionError):
        # Expected for deeply nested or problematic structures
        pass
    except Exception as e:
        pytest.fail(f"Codec nested structures test failed: {e}")

@given(
    large_data=st.lists(
        st.tuples(
            st.text(max_size=100),
            st.integers(-10000, 10000),
            st.floats(-1000, 1000, allow_nan=False, allow_infinity=False)
        ),
        min_size=100, max_size=1000
    )
)
@settings(max_examples=5, deadline=5000, suppress_health_check=[HealthCheck.too_slow])
def test_codec_large_data(large_data):
    """Test codec performance and correctness with large data sets."""
    codec = Codec()

    try:
        # Test encoding large data
        encoded = codec.encode(large_data)
        assert isinstance(encoded, bytes)
        assert len(encoded) > 1000  # Should be reasonably large

        # Test decoding back
        decoded = codec.decode(encoded)
        assert decoded == large_data

    except Exception as e:
        pytest.fail(f"Codec large data test failed: {e}")