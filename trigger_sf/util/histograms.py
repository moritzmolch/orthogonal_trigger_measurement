import hist


def create_hist(config, variables):
    category_names = list(config.categories.names())
    process_names = list(config.processes.names())

    # create categorical axes
    axes = [
        hist.axis.StrCategory(category_names, name="category"),
        hist.axis.StrCategory(process_names, name="process"),
    ]

    # create variable axes
    for variable in variables:
        axes.append(hist.axis.Variable(
            variable.bin_edges, underflow=True, overflow=True, name=variable.name
        ))

    # create the full histogram
    h = hist.Hist(*axes, storage=hist.storage.Weight())

    return h
