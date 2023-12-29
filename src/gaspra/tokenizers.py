from gaspra.types import TokenSequence


from collections.abc import Iterable, Sequence


def line_tokenize(
    *string_set: str,
):
    tokenized = []
    token_dict = {}

    for s in string_set:
        lines = s.split("\n")
        # Ignore the empty string that gets generated
        # by an ending newline.

        if len(lines) > 0 and lines[-1] == "":
            lines = lines[:-1]

        for line in s.split("\n"):
            if line not in token_dict:
                token_dict[line] = len(token_dict)

        tokenized.append(tuple(token_dict[line] for line in lines))
    token_map = tuple(token_dict.keys())
    return tuple([token_map, *tokenized])
