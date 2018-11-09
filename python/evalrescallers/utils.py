from collections import OrderedDict


def comma_sep_string_to_ordered_dict(string_in):
    odict = OrderedDict()
    split_string = string_in.split(',')
    if len(split_string) % 2 != 0:
        raise Exception(f'Must have even number of elements in list: {string_in}')

    for i in range(0, len(split_string) - 1, 2):
        odict[split_string[i]] = split_string[i+1]

    return odict

