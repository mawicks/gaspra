# Why `difftools` exists

Recently, I became interested in string matching. In particular, I was
interested in the Longest Common Substring (LCS) and similar problems. I
discovered that efficient string matching is hard to find, especially in
Python. Much of what you find on the internet is either slow, or in some
cases, simply doesn't work.  I wanted a pure Python solution that is
reasonably fast to experiment with some string matching algorithms.


Though implementations appear uncommon, efficient algorithms exist.
The LCS problem is solvable in linear time, yet most online examples
use a classical dynamic programming approach which is quadratic in
both space and time. Even the venerable `difflib`, which is part of
Python's standard library uses quadratic-time algorithms.
`Difftools` uses efficient suffix automata
with linear time and space complexity. The difference is dramatic.
It's the same as the difference between a quicksort and a bubble sort.
Because of this difference, nobody uses a bubble sort, which is
universally recognized as a naive approach.  Yet somehow, using
dynamic programming to solve text matching is widely accepted.
`Difflib` is practically unusable on large, document-length
strings. The table below shows the time to find the LCS in two
strings for `difflib` compared to this package. The strings are
equal-length, random sequences of the letters a, b, and c.
The lengths shown in the table are the combined length of
the two strings.
The quadratic complexity of 'difflib' is obvious.  Even though it's a pure
Python solution, `difftools` is quite fast by comparison.

| Length   |   Match Length |   Difflib (ms) |   Difftools (ms) |
|----------|----------------|----------------|------------------|
| 2k       |             13 |             31 |                3 |
| 4k       |             13 |            120 |                5 |
| 8k       |             15 |            472 |               11 |
| 16k      |             15 |          1,897 |               32 |
| 32k      |             16 |          7,828 |               52 |
| 64k      |             18 |         33,314 |              121 |
| 128k     |             19 |        135,413 |              341 |
| 256k     |             23 |        554,665 |              690 |

# Examples.

## Finding Longest Common Substrings

The function `difftools.find_lcs()` returns the starting positions and the
length of common substring of two strings with maximal length:

```
>>> import difftools                                                                                               
>>> a="Call me Ishmael. Some years ago—never mind how long \
precisely—having little or no money in my purse, and nothing \
particular to interest me on shore, I thought I would sail \
about a little and see the watery part of the world"                                                                                                                  
>>> b="It was the best of times, it was the worst of times, \
it was the age of wisdom, it was the age of foolishness, \
it was the epoch of belief, it was the epoch of incredulity, \
it was the season of Light, it was the season of Darkness, \
it was the spring of hope, it was the winter of despair, we \
had everything before us, we had nothing before us, we were \
all going direct to Heaven, we were all going direct the other \
way – in short, the period was so far like the present period, \
that some of its noisiest authorities insisted on its being \
received, for good or for evil, in the superlative degree of \
comparison only."
>>> difftools.find_lcs(a,b)
(103, 321, 10)
>>> a[103:103+10]
'd nothing '
>>> b[321:321+10]
'd nothing '
>>> 
```

## Finding Diffs

Given an original string and a modified string, the function
`difftools.changes()` returns the sequence of changes represented
interspersed with fragments from the original string.  The sequence is
a sequence of strings (fragments from the original) and tuples of two strings
representing an insertion/deletion pair.  Note that an insertion is a tuple
where the deletion string is empty, and vice versa.

```
>>> import difftools
>>> original="The quick brown fox jumps over the lazy dog near the riverbank."
>>> modified="The quick brown fox leaps over the lazy dogs near the river"
>>> list(difftools.changes(original, modified))
['The quick brown fox ', ('lea', 'jum'), 'ps over the lazy dog', ('s', ''), ' near the river', ('', 'bank.')]
```

# Merging

Here's an example of two different revisions of the same sentence that can be
resolved without any conflicts.

``` 
>>> original = "The quick brown fox jumps over the lazy dog near the riverbank."
>>> editor1 = "The quick brown fox leaps over the lazy dogs near the river."
>>> editor2 = "The quick, clever fox jumps across the lazy dogs by the riverbank."
>>> list(difftools.changes(original, editor1))
['The quick brown fox ', ('lea', 'jum'), 'ps over the lazy dog', ('s', ''), ' near the river', ('', 'bank'), '.']
>>> list(difftools.changes(original, editor2))
['The quick', (',', ''), ' ', ('cleve', 'b'), 'r', ('', 'own'), ' fox jumps ', ('ac', 'ove'), 'r', ('oss', ''), ' the lazy dog', ('s', ''), ' ', ('by', 'near'), ' the riverbank.']
>>> list(difftools.merge(original, editor1, editor2))
['The quick, clever fox leaps across the lazy dogs by the river.']
```

Here's the same example but with a different revision by editor2 that *does*
conflict with editor1.  The conflicts are represented as a tuple with two
alternate versions of the merged text.

```
>>> conflicts_with_1 = "The swift, agile fox leaps over the sleepy dog near the riverside."
>>> list(difftools.changes(original, conflicts_with_1))
['The ', ('s', 'quick bro'), 'w', ('ift, agile', 'n'), ' fox ', ('lea', 'jum'), 'ps over the ', ('s', ''), 'l', ('eep', 'az'), 'y dog near the river', ('side', 'bank'), '.']
>>> list(difftools.merge(original, editor1, conflicts_with_1))
['The swift, agile fox leaps over the sleepy dogs near the river', ('', 'side'), '.']
```

