from bmu import label


def test_dict_to_flat():
    namespace = 'ns'
    trees = [{'a': [{'b': ['c', 'd']}, {'e': [{'f': ['g', 'h']}]}]}, {'i': ['j', 'k']}]
    flats = [
        [
            'ns/a',
            'ns/a/b',
            'ns/a/b/c',
            'ns/a/b/d',
            'ns/a/e',
            'ns/a/e/f',
            'ns/a/e/f/g',
            'ns/a/e/f/h',
        ],
        [
            'ns/i',
            'ns/i/j',
            'ns/i/k',
        ]
    ]
    for tree, flat in zip(trees, flats):
        assert label.get_label_names(namespace, tree) == set(flat)
