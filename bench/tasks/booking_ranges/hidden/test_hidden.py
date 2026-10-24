import pytest

from ranges import free_slots, merge_ranges


def test_touching_ranges_merge():
    assert merge_ranges([(1, 3), (3, 5)]) == [(1, 5)]


def test_contained_range_does_not_shrink():
    assert merge_ranges([(1, 10), (2, 3)]) == [(1, 10)]


def test_unsorted_overlaps():
    assert merge_ranges([(6, 8), (1, 4), (3, 7)]) == [(1, 8)]


def test_empty_ranges_ignored():
    assert merge_ranges([(2, 2), (5, 6), (9, 9)]) == [(5, 6)]
    assert merge_ranges([]) == []


def test_invalid_range_raises():
    with pytest.raises(ValueError):
        merge_ranges([(5, 3)])


def test_free_slots_clips_to_day():
    assert free_slots([(0, 9), (17, 20)], 8, 18) == [(9, 17)]


def test_free_slots_ignores_bookings_outside_day():
    assert free_slots([(1, 2), (20, 22)], 8, 10) == [(8, 10)]


def test_free_slots_whole_day_booked():
    assert free_slots([(0, 24)], 8, 18) == []


def test_free_slots_no_bookings():
    assert free_slots([], 8, 18) == [(8, 18)]


def test_free_slots_never_overlaps_bookings():
    bookings = [(12, 14), (9, 10), (13, 16), (16, 17)]
    slots = free_slots(bookings, 8, 18)
    assert slots == [(8, 9), (10, 12), (17, 18)]
