---
status: informative
last_updated: 2026-08-10
superseded_by: PRE-015
---

# Temporary documentation validation

Use only after documentation edits. Do not run these commands for a read-only
status/orientation/report task. Report checks run and not run.

```sh
git diff --check
```

```sh
perl -MFile::Basename=dirname -MFile::Spec -e 'for my $f (@ARGV) { open my $h, q{<}, $f or die qq{$f: $!\n}; my $code=0; while (<$h>) { if (/^\s*```/) { $code=!$code; next } next if $code; while (/\[[^\]]*\]\(([^)]+)\)/g) { my $p=$1; $p =~ s/#.*//; $p =~ s/^<|>$//g; next if $p eq q{} || $p =~ m{^(?:https?|mailto):}; my $x=File::Spec->rel2abs($p,dirname($f)); print qq{$f -> $1\n} unless -e $x } } }' $(rg --files --hidden -g '*.md' -g '!.git/**')
```

No output from either command is a pass. These are temporary entry points and
do not satisfy PRE-015.
