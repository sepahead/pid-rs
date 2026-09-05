# Inert duplicate payload retirement

At 07:58:22 UTC on 5 September 2026, the coordinating owner removed three untracked duplicate payload files from the retained primary working tree. The operation kept their parent directories. Their combined size was 50,889 bytes.

| Inert payload identity | Bytes |
|---|---:|
| `afb14f7288296f08b4a1ae4b82f1c7e9201c83e7025049626f7c75e7f4ec1217` | 4,774 |
| `bbf3c96aba08df8a73a19650a2998dac9b3fe2fcb8686da57a0bac0c7c5bd0f5` | 18,230 |
| `137c36c5a86415bbce8f0f93ffe22554332f96d58b6ca8fd561dc19fa8e039bc` | 27,885 |

Each identity is the complete file's SHA-256. The exact payloads remain in main's [rejected lifecycle archive](../archive/ksg-m1a-rejected-lifecycle-checker-20260828/DISPOSITION.md) and [historical S1 checker archive](../archive/sxpid3-s1-historical-checkers-v1/DISPOSITION.md). They also have byte- and mode-verified private recovery copies. The archived evidence remains inert. This cleanup grants no new lifecycle, theorem, estimator, or application credit.

Before removal, each selected file was a regular untracked mode 0644 file and matched its exact mainline object. The coordinating owner recorded the selected-file disposition. The postcheck found exactly the three expected untracked entries removed from the NUL-separated status. The other 596 tracked or nonignored paths, containing 28,182,116 bytes, were unchanged. HEAD, symbolic branch, index, and all 61 refs were unchanged.

The mainline and private successors were checked again after removal. Remote main remained `e1a6648ccace699e41b4ffa48c6acd79209a7418`. No parent directory, worktree, Git ref, or other primary file was removed. The pre-action record and exact before and after evidence remain in private custody. This bounded comparison does not cover unlisted ignored private files or establish an atomic filesystem snapshot.
