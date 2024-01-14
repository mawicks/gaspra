import pytest

from gaspra.tokenizers import (
    CharTokenizer,
    LineTokenizer,
    NullTokenizer,
    SpaceTokenizer,
    SymbolTokenizer,
    line_encode_strings,
)


@pytest.fixture(
    params=(
        NullTokenizer,
        CharTokenizer,
        LineTokenizer,
        SymbolTokenizer,
        SpaceTokenizer,
    )
)
def tokenizer(request: pytest.FixtureRequest):
    return request.param()


ENCODER_TEST_CASES = [
    "a b c\nxx y z\n",
    "abc def xyz\n1234 456 789\n",
    "a += b*c;\n   switch() {};",
    "the quick brown fox",
    "$abc a-b-c d_e\nxyz",
    "$ABC!@#$%^&*()",
    bytes(range(256)),
]


@pytest.mark.parametrize("string", ENCODER_TEST_CASES)
def test_generic_encoder(string, tokenizer):
    if type(string) is str:
        string = string.encode("utf-8")

    # There's an arbitrary bytes string in the test data
    # which is a good test case for the encoders that don't
    # require a UTF-8 encoding.  However it's not a good test
    # for CharTokenizer or SymbolTokenizer.  Skiopo those
    # for any such test cases.

    try:
        string.decode("utf-8")
    except UnicodeDecodeError:
        if type(tokenizer) in (CharTokenizer, SymbolTokenizer):
            return

    encoded = tokenizer.from_bytes(string)

    # Another exception for Chartokenizer and NullTokenizer which
    # don't group characters.
    if type(tokenizer) not in (NullTokenizer, CharTokenizer):
        assert len(encoded) < len(string)

    assert tokenizer.to_bytes(encoded) == string


@pytest.mark.parametrize(
    ["s", "reconstruction"],
    [
        ("", ""),
        ("\n", "\n"),
        ("\n\n", "\n\n"),
        ("\n\n\n", "\n\n\n"),
        ("a", "a"),
        ("a\n", "a\n"),
        ("a\n\n", "a\n\n"),
        ("a\nb", "a\nb"),
        ("a\nb\n", "a\nb\n"),
        ("a\nb\nc", "a\nb\nc"),
        ("a\nb\nc\n", "a\nb\nc\n"),
        ("\na\nb\nc\n", "\na\nb\nc\n"),
    ],
)
def test_line_encode(s, reconstruction):
    """This tests that the decoder returned correctly remaps tokens
    but it also tests how files with newlines get encoded"""
    token_mapper, token_stream = line_encode_strings(s)

    # Each token in token_stream represents a line.  When its expanded
    # back into the file, a newline at the end of each line is implied.
    # There is no difference between a string with just "a" (no ending
    # newline and a string with just "a\n" after encoding.  Files
    # with no newlines at the end will gain a newline after token
    # expansion.  The expanded file always has a newline at the end.
    # Here we use "join" to insert the newlines *between* the lines,
    # and we need to artifically insert the trailing newline.
    # Empty files are empty files, i.e., zero lines.
    assert reconstruction == "\n".join(token_mapper[t] for t in token_stream)
