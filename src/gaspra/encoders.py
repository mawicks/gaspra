from collections.abc import Iterable, Sequence


def line_encode_strings(
    *string_set: str,
):
    encoded = []
    encoding = {}

    for s in string_set:
        lines = s.split("\n")

        for line in lines:
            if line not in encoding:
                encoding[line] = len(encoding)

        encoded.append(tuple(encoding[line] for line in lines))
    decoding = tuple(encoding.keys())
    return tuple([decoding, *encoded])


def line_encoder(contents: bytes, encoding: dict[bytes, int]):
    lines = contents.split(b"\n")

    for line in lines:
        if line not in encoding:
            encoding[line] = len(encoding)

    return tuple(encoding[line] for line in lines)


def line_decoder(contents: Iterable[int], decoding: Sequence[bytes]):
    return b"\n".join(decoding[t] for t in contents)


def space_encoder(string: bytes, encoding):
    unencoded_tokens = string.split(b" ")

    for token in unencoded_tokens:
        if token not in encoding:
            encoding[token] = len(encoding)

    return tuple(encoding[token] for token in unencoded_tokens)


def space_decoder(contents: Iterable[int], decoding: Sequence[bytes]):
    return b" ".join(decoding[t] for t in contents)
