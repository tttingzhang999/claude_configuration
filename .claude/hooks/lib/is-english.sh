#!/bin/bash
# is_english "$text" — returns 0 if text contains NO CJK characters,
# non-zero otherwise. Empty input returns non-zero (not English).
#
# Uses perl (preinstalled on macOS + most Linux) for Unicode-property
# detection; BSD grep lacks -P so can't be used portably.
is_english() {
  local text="$1"
  [ -z "$text" ] && return 1
  printf '%s' "$text" | perl -CSD -e '
    local $/;
    my $t = <STDIN>;
    exit(($t =~ /\p{Han}|\p{Hiragana}|\p{Katakana}|\p{Hangul}|\p{Bopomofo}/) ? 1 : 0);
  '
}
