from evalrescallers import performance_measurer

def run(options):
    pm = performance_measurer.PerformanceMeasurer(
        options.infile,
        options.species,
        r_means_resistant=not options.r_means_susceptible,
    )
    pm.run(options.outprefix)


