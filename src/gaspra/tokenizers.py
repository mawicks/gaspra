def line_tokenize(
    *string_set: str,
):
    tokenized = []
    token_dict = {}

    print(string_set)
    for s in string_set:
        lines = s.split("\n")

        for line in lines:
            if line not in token_dict:
                token_dict[line] = len(token_dict)

        tokenized.append(tuple(token_dict[line] for line in lines))
    token_map = tuple(token_dict.keys())
    return tuple([token_map, *tokenized])
