from evalrescallers import plots, utils


def run(options):
    plots.make_res_susc_bar_charts(
        options.infile,
        options.datasets.split(','),
        utils.comma_sep_string_to_ordered_dict(options.tools),
        utils.comma_sep_string_to_ordered_dict(options.drugs),
        options.outprefix,
    )


