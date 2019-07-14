from bitly.util import flatten


def test_that_nested_lists_get_flattened():
    target = [[1], [2]]
    expected = [1, 2]
    actual = flatten(target)
    assert expected == actual
