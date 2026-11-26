"""Prepare one categorical row per measured Shai control condition."""
from decimal import Decimal
import json
import sys


def prepare(data):
    records = {10: [], 50: [], 100: []}
    lines = data.splitlines()
    if len(lines) != 31:
        raise ValueError("expected 31 basal-level rows")
    for basal_index, line in enumerate(lines):
        measurements = line.split()
        if len(measurements) != 21:
            raise ValueError("expected 21 apical tuft settings per row")
        for tuft_index, text in enumerate(measurements):
            spikes = Decimal(text)
            if spikes not in (0, 1, 2, 3, 4):
                raise ValueError("outside the archived integer spike counts")
            target = 0 if spikes == 0 else 1 if spikes <= 2 else 2
            basal = 10 * basal_index
            tuft = 10 * tuft_index
            above = int(basal > tuft)
            for width, rows in records.items():
                rows.append([basal // width, tuft // width, above, target])
    return records


if __name__ == "__main__":
    print(json.dumps(prepare(sys.stdin.read()), separators=(",", ":")))
