import law
import luigi
import order as od

from trigger_sf.tasks.base import EfficiencyTask
from trigger_sf.tasks.histograms import CreateHistograms

law.contrib.load("numpy")


class CalculateEfficiencies(EfficiencyTask):

    channel = law.Parameter(
        description="name of the channel",
    )

    variables = law.CSVParameter(
        description="comma-separated list of variables",
    )

    processes = law.CSVParameter(
        description="comma-separated list of processes",
    )

    ref_category = law.Parameter(
        description="name of the category, which represents the reference dataset of the trigger efficiency measurement",
    )

    sig_ref_category = law.Parameter(
        description="name of the category, which represents the reference+signal dataset of the trigger efficiency measurement; must be a subset of the reference category",
    )

    def requires(self):
        datasets = [
            d.name
            for d in self.config_inst.datasets.values()
            if any([list(d.processes.values())[0].has_parent_process(p) for p in self.process_insts])
        ]
        return [
            CreateHistograms.req(self, dataset=dataset, category=category)
            for dataset in datasets
            for category in [self.ref_category_inst.name, self.sig_ref_category_inst.name]
        ]

    def output(self):
        return self.local_target("efficiencies.npz")

    def run(self):
        import hist.intervals
        import numpy as np

        # load histograms
        histograms = []
        for input in self.input():
            histograms.append(input.load(formatter="pickle"))

        # sum histograms
        histogram = None
        for h in histograms:
            if histogram is None:
                histogram = h
            else:
                histogram += h

        # get histogram for ref and for sig_ref category
        processes = [p.name for p in self.process_insts]
        h_ref = histogram[self.ref_category, processes, ...][hist.sum, ...]
        h_sig_ref = histogram[self.sig_ref_category, processes, ...][hist.sum, ...]

        # divide histograms
        eff_nominal = h_sig_ref.values() / h_ref.values()
        eff_shift = hist.intervals.clopper_pearson_interval(h_sig_ref.values(), h_ref.values(), coverage=0.68)
        eff_down = eff_shift[0, ...]
        eff_up = eff_shift[1, ...]

        # prepare arrays for saving them in an .npz file
        data = {
            "nominal": eff_nominal,
            "up": eff_up,
            "down": eff_down,
        }

        # save efficiencies and uncertainties
        self.output().dump(**data, formatter="numpy")


class PlotEfficiencies(EfficiencyTask):

    extensions = law.CSVParameter(
        description="extensions of the image file to be produced; default: 'png,pdf'",
        default=["png", "pdf"]
    )

    def requires(self):
        return {
            "CalculateEfficiencies": CalculateEfficiencies.req(self),
        }

    def output(self):
        return {
            (variation, extension): self.local_target(f"efficiency__{variation}.{extension}")
            for variation in self.variations
            for extension in self.extensions
        }

    def run(self):
        # delayed imports, as packages are only needed for this task
        import matplotlib as mpl
        import mplhep
        import numpy as np
        from trigger_sf.util.plotting import plot_2d_colormesh

        # load efficiency dictionary
        efficiency = self.input()["CalculateEfficiencies"].load(formatter="numpy")

        # variable bin edges and labels
        variable_insts = list(self.variable_insts.values())
        x_bin_edges = np.array(variable_insts[0].bin_edges)
        y_bin_edges = np.array(variable_insts[1].bin_edges)
        x_label = variable_insts[0].get_full_x_title()
        y_label = variable_insts[1].get_full_x_title()

        # keyword arguments for pcolormesh command
        pcolormesh_kwargs = {
            "cmap": "viridis",
            "vmin": 0,
            "vmax": 1,
        }

        # keyword arguments for cms label command
        mplhep_label_kwargs = {
            "lumi": self.campaign_inst.x.lumi,
            "fontsize": 22,
        }

        # produce the efficiency plot
        with mpl.style.context(mplhep.style.CMS):
            for variation in self.variations:
                # colorbar label
                z_label = f"$\\epsilon$ ({variation}, {self.processes_label})"

                # create the plot
                fig, ax = plot_2d_colormesh(
                    x_bin_edges,
                    y_bin_edges,
                    efficiency[variation],
                    x_label,
                    y_label,
                    z_label,
                    pcolormesh_kwargs=pcolormesh_kwargs,
                    mplhep_label_kwargs=mplhep_label_kwargs,
                )

                for extension in self.extensions:
                    self.output()[(variation, extension)].dump(fig, formatter="mpl")
