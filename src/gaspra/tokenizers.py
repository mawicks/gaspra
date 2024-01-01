from collections.abc import Hashable


def line_tokenize(
    *string_set: str,
):
    tokenized = []
    token_dict = {}

    for s in string_set:
        lines = s.split("\n")

        for line in lines:
            if line not in token_dict:
                token_dict[line] = len(token_dict)

        tokenized.append(tuple(token_dict[line] for line in lines))
    token_map = tuple(token_dict.keys())
    return tuple([token_map, *tokenized])


def line_tokenize_bytes(contents: bytes, token_dict: dict[bytes, int]):
    lines = contents.split(b"\n")

    for line in lines:
        if line not in token_dict:
            token_dict[line] = len(token_dict)

    return tuple(token_dict[line] for line in lines)
