# Run the two public Rust methods on the Shai control grid

Sepehr Mahmoudian, 2026. This check compares the actual binary64 outputs from the public averaged categorical shared-exclusions and Williams–Beer minimum-specific-information methods with the finite reference. Binary64 is the 64-bit binary floating-point format. The complete source revision is `6a9f087be84bc21a89ff51e7da8e626e6883d73e`. All scientific source files are read from that exact Git object. Each retains its recorded SHA-256 digest. Only the small observation client is added to the isolated workspace. No project source checkout or index is edited. The reference location, data digest and original compile options are fixed. [Scientific protocol](PROTOCOL.md) · [Original frozen source list](SOURCE.json)

From this directory, first prepare the immutable external dataset following the preceding study's instructions. Use the same original Git repository and its pinned Cargo dependency cache. The Cargo commands run offline, without optional features and with one job. A compiler installed through rustup can be located by the commands below. A different compiler or operating system can produce different last bits. The original tool release and SHA-256 digests are available in TOOLCHAIN.json. Add `--original-tools` to require those exact binaries on the original platform.

```sh
repo=$(git rev-parse --show-toplevel)
work=$(mktemp -d)
cargo_bin=$(rustup which cargo)
rustc_bin=$(rustup which rustc)
python3 -I -S -B replay.py build --repository "$repo" --build "$work/build" \
  --cargo "$cargo_bin" --rustc "$rustc_bin"
python3 -I -S -B replay.py compare --build "$work/build" --grid ../spikes_.dat \
  --reference ../products-and-predictions.json --arithmetic ../arithmetic.py \
  --prepare prepare.py --registration payload.json --output "$work/ordinary"
python3 -O -I -S -B replay.py compare --build "$work/build" --grid ../spikes_.dat \
  --reference ../products-and-predictions.json --arithmetic ../arithmetic.py \
  --prepare prepare.py --registration payload.json --output "$work/optimized"
```

The original build used Rust 1.99.1, one observed Apple arm64 computer and the Cargo development profile with debug information disabled. The active compiler limits and complete original command roles are in the frozen protocol. The two original calls used an external serial 1 GiB (1,073,741,824-byte) sampled process-group ceiling. Their macOS execution also set `--sandbox-macos` with a standard-library-only Python interpreter installed outside user homes. That option denies network access and file writes to the converter and observation client. Other systems can reproduce the arithmetic and native API check with the commands shown. Their operating-system isolation and resource accounting are separate.

The input checker tests every transformed categorical row before invoking the compiled binary. It verifies the 651 rows, support, all native source labels, and the return of both direct categorical methods with no enabled optional features. The actual class width is counted in nominal inputs. A positive spike rate does not enter either method. For an exact rational product, the check constructs a 256-bit outward-rounded interval for its natural logarithm divided by 651. Both endpoints must lie within one trillionth of a nat of the returned binary64 value. Reversed label storage with intact labels is accepted. Twenty corrupted inputs or outputs and two actual malformed native inputs are refused. No general floating-point error theorem follows. [Per-channel error bounds and controls](result.json) · [All original words from the two methods](returned-rust.json) · [Measured time and sampled memory](resources.json)
