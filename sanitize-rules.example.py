"""Template for sanitize-rules.local.py — copy, then fill in your own values.

    cp sanitize-rules.example.py sanitize-rules.local.py

`sanitize-rules.local.py` is gitignored, and it is the only file that names the
real identifiers being scrubbed. Keeping it out of the repo matters: a committed
mapping would publish your name, your colleagues' names, your employer, your
clients, and your local paths — precisely what the export exists to remove.

Both lists are ORDERED and each entry is tagged with how to read the pattern:

    "re"   — a raw regex, used as-is
    "word" — a bare identifier; the caller wraps it in a standalone-token
             boundary that counts punctuation and underscores as edges.
             Prefer this for names and ticket prefixes. Do NOT hand-write `\\b`:
             regex counts `_` as a word character, so `\\bNAME\\b` misses
             `_as NAME_` in markdown emphasis, and the scan misses it too.

SUBSTITUTIONS runs top-to-bottom over every copied text file, so put the more
specific rule before the shorter one it contains ("Acme Corp Ltd" before "Acme").
FORBIDDEN is the fail-closed scan: anything still matching after substitution
aborts the sync, and nothing is committed.
"""

SUBSTITUTIONS = [
    # people
    ("re", r"Your Real Name", "Your Name"),
    ("word", r"Firstname", "Your Name"),
    ("re", r"colleague-handle", "alice"),
    ("re", r"Colleague Name", "Alice Chen"),
    # employer / clients / projects
    ("re", r"realcorp\.com", "example.com"),
    ("re", r"RealCorp", "AcmeCorp"),
    ("word", r"CLIENT", "ExampleClient"),
    ("word", r"PRJ", "TICKET"),
    # hosts and ids
    ("re", r"your-real-org\.atlassian\.net", "your-org.atlassian.net"),
    ("word", r"U0[A-Z0-9]{8,}", "YOUR_SLACK_USER_ID"),
    ("word", r"C0[A-Z0-9]{8,}", "YOUR_SLACK_CHANNEL_ID"),
    # local paths — longest first
    ("re", r"/Users/you/path/to/vault", "~/vault"),
    ("re", r"/Users/you", "/Users/you"),
]

FORBIDDEN = [
    ("re", r"realcorp\.com"),
    ("re", r"RealCorp"),
    ("re", r"colleague-handle"),
    ("re", r"Colleague Name"),
    ("re", r"your-real-org"),
    ("word", r"Firstname"),
    ("word", r"CLIENT"),
    ("word", r"PRJ"),
    ("word", r"U0[A-Z0-9]{8,}"),
    ("word", r"C0[A-Z0-9]{8,}"),
]
