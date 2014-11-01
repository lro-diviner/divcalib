def cols_to_descriptor(iterable):
    out = 'Diviner pipes descriptor file\n'
    for col in iterable:
        out += "'{0}' '{0}'\n".format(col)
    out += "'end' 'end'\n"
    return out
