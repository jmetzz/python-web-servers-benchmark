

def to_str(values, separator=','):
    return separator.join(str(cell) for cell in values)


def avg(values):
    return sum(values) / float(len(values)) if len(values) > 0 else 0
