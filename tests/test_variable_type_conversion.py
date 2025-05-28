"""
Test variable type conversion functionality.
"""

from boilersync.variable_collector import convert_string_to_appropriate_type


def test_boolean_conversion():
    """Test that boolean-like strings are converted to actual booleans."""
    # True values
    assert convert_string_to_appropriate_type("true") is True
    assert convert_string_to_appropriate_type("True") is True
    assert convert_string_to_appropriate_type("TRUE") is True
    assert convert_string_to_appropriate_type("yes") is True
    assert convert_string_to_appropriate_type("y") is True
    assert convert_string_to_appropriate_type("1") is True
    assert convert_string_to_appropriate_type("on") is True
    assert convert_string_to_appropriate_type("enable") is True
    assert convert_string_to_appropriate_type("enabled") is True

    # False values
    assert convert_string_to_appropriate_type("false") is False
    assert convert_string_to_appropriate_type("False") is False
    assert convert_string_to_appropriate_type("FALSE") is False
    assert convert_string_to_appropriate_type("no") is False
    assert convert_string_to_appropriate_type("n") is False
    assert convert_string_to_appropriate_type("0") is False
    assert convert_string_to_appropriate_type("off") is False
    assert convert_string_to_appropriate_type("disable") is False
    assert convert_string_to_appropriate_type("disabled") is False
    assert convert_string_to_appropriate_type("") is False


def test_numeric_conversion():
    """Test that numeric strings are converted to numbers."""
    # Note: "0" and "1" are converted to boolean False/True respectively
    # Test integers that aren't boolean-like
    assert convert_string_to_appropriate_type("42") == 42
    assert convert_string_to_appropriate_type("-5") == -5
    assert convert_string_to_appropriate_type("100") == 100
    assert convert_string_to_appropriate_type("2") == 2

    # Floats
    assert convert_string_to_appropriate_type("3.14") == 3.14
    assert convert_string_to_appropriate_type("-2.5") == -2.5
    assert convert_string_to_appropriate_type("0.0") == 0.0
    assert convert_string_to_appropriate_type("1.0") == 1.0


def test_string_passthrough():
    """Test that non-convertible strings remain as strings."""
    assert convert_string_to_appropriate_type("hello") == "hello"
    assert convert_string_to_appropriate_type("world") == "world"
    assert convert_string_to_appropriate_type("some text") == "some text"
    assert convert_string_to_appropriate_type("v1.2.3") == "v1.2.3"
    assert convert_string_to_appropriate_type("user@example.com") == "user@example.com"


def test_edge_cases():
    """Test edge cases and whitespace handling."""
    # Whitespace should be stripped for boolean conversion
    assert convert_string_to_appropriate_type(" true ") is True
    assert convert_string_to_appropriate_type(" false ") is False
    assert convert_string_to_appropriate_type("  1  ") is True
    assert convert_string_to_appropriate_type("  0  ") is False

    # Numeric strings with whitespace
    assert convert_string_to_appropriate_type(" 42 ") == 42
    assert convert_string_to_appropriate_type(" 3.14 ") == 3.14


def test_boolean_vs_numeric_precedence():
    """Test that boolean conversion takes precedence over numeric conversion."""
    # These should be booleans, not numbers
    assert convert_string_to_appropriate_type("0") is False
    assert convert_string_to_appropriate_type("1") is True

    # These should be numbers since they're not in the boolean list
    assert convert_string_to_appropriate_type("2") == 2
    assert convert_string_to_appropriate_type("10") == 10
