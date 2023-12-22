# Why `difftools` exists

Recently, I became interested in string matching. In particular, I was
interested in the Longest Common Substring (LCS) and similar problems. I
discovered that efficient string matching is hard to find, especially in
Python. Much of what you find on the internet is either slow, or in some
cases, simply doesn't work.

Though implementations appear uncommon, efficient algorithms exist.
The LCS problem is solvable in linear time, yet most online examples
use a classical dynamic programming approach which is quadratic in
both space and time. Even the venerable `difflib` that's included
in the Python standard library uses
quadratic times algorithms. This package uses efficient suffix automata
which have linear time and space complexity. The difference is enormous.
That's the same as the difference between a quicksort and a bubble sort.
Nobody would use a bubble sort, which is universally recognized
as a naive approach, yet somehow, using dynamic programming
to solve text matching is widely accepted.
`Difflib` is practically unusable on large, document-length
strings. The table below shows the time to find the LCS in two
strings for `difflib` compared to this package. The strings are
equal-length and randomly generated using the letters a-c.  The
length shown in the table is the combined length of the two strings.
The quadratic complexity of 'difflib' is obvious.

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