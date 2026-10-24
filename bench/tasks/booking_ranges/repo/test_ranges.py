from ranges import free_slots, merge_ranges


def test_merges_overlap():
    assert merge_ranges([(1, 3), (2, 5)]) == [(1, 5)]


def test_unsorted_input():
    assert merge_ranges([(5, 7), (1, 2)]) == [(1, 2), (5, 7)]


def test_free_slots_simple():
    assert free_slots([(10, 12)], 9, 17) == [(9, 10), (12, 17)]
