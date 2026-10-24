"""Booking calendar helpers. Ranges are half-open [start, end) pairs of ints."""


def merge_ranges(ranges):
    """Merge overlapping or touching ranges and return them sorted by start."""
    merged = []
    for start, end in ranges:
        if merged and start < merged[-1][1]:
            merged[-1] = (merged[-1][0], end)
        else:
            merged.append((start, end))
    return merged


def free_slots(bookings, day_start, day_end):
    """Return the free [start, end) gaps between bookings within the day."""
    slots = []
    cursor = day_start
    for start, end in merge_ranges(bookings):
        if start > cursor:
            slots.append((cursor, start))
        cursor = end
    if cursor < day_end:
        slots.append((cursor, day_end))
    return slots
