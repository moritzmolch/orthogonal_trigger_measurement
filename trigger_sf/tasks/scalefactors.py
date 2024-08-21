import law
import luigi
import order as od

from trigger_sf.tasks.base import EfficiencyTask
from trigger_sf.tasks.efficiencies import CalculateEfficiencies


class CalculateScaleFactors(EfficiencyTask):

    def requires(self):
        return {
            "CreateEfficiencies_data": CalculateEfficiencies.req(self, processes=[p.name for p in self.data_process_insts]),
            "CreateEfficiencies_mc": CalculateEfficiencies.req(self, processes=[p.name for p in self.mc_process_insts]),
        }

    def output(self):
        return self.local_target("scalefactors.npz")

    def run(self):
        # load efficiency dictionaries
        eff_dict_data = self.input()["CreateEfficiencies_data"].load(formatter="numpy")
        eff_dict_mc = self.input()["CreateEfficiencies_mc"].load(formatter="numpy")

        # perform division and error estimation
        sf_nominal = eff_dict_data["nominal"] / eff_dict_mc["nominal"]
        sf_up = eff_dict_data["up"] / eff_dict_mc["down"]
        sf_down = eff_dict_data["down"] / eff_dict_mc["up"]

        # save scale factors
        self.output().dump(
            nominal=sf_nominal,
            up=sf_up,
            down=sf_down,
            formatter="numpy",
        )


class PlotScaleFactors(EfficiencyTask):

    extensions = law.CSVParameter(
        description="extensions of the image file to be produced; default: 'png,pdf'",
        default=["png", "pdf"]
    )

    def requires(self):
        return {
            "CalculateScaleFactors": CalculateScaleFactors.req(self),
        }

    def output(self):
        return {
            (variation, extension): self.local_target(f"scalefactors__{variation}.{extension}")
            for variation in self.variations
            for extension in self.extensions
        }

    def run(self):
        # delayed imports, as packages are only needed for this task
        import matplotlib as mpl
        import mplhep
        import numpy as np
        from trigger_sf.util.plotting import plot_2d_colormesh

        # load scale factors dictionary
        scalefactors = self.input()["CalculateScaleFactors"].load(formatter="numpy")

        # variable bin edges and labels
        variable_insts = list(self.variable_insts.values())
        x_bin_edges = np.array(variable_insts[0].bin_edges)
        y_bin_edges = np.array(variable_insts[1].bin_edges)
        x_label = variable_insts[0].get_full_x_title()
        y_label = variable_insts[1].get_full_x_title()

        # keyword arguments for pcolormesh command
        pcolormesh_kwargs = {
            "cmap": "coolwarm",
            "vmin": 0,
            "vmax": 2,
        }

        # keyword arguments for colorbar command
        colorbar_kwargs = {"extend": "both"}

        # keyword arguments for cms label command
        mplhep_label_kwargs = {
            "lumi": self.campaign_inst.x.lumi,
            "fontsize": 22,
        }

        # produce the efficiency plot
        with mpl.style.context(mplhep.style.CMS):
            for variation in self.variations:
                # colorbar label
                z_label = f"$\\epsilon_{{data}}/\\epsilon_{{MC}}$ ({variation})"

                # create the plot
                fig, ax = plot_2d_colormesh(
                    x_bin_edges,
                    y_bin_edges,
                    scalefactors[variation],
                    x_label,
                    y_label,
                    z_label,
                    pcolormesh_kwargs=pcolormesh_kwargs,
                    colorbar_kwargs=colorbar_kwargs,
                    mplhep_label_kwargs=mplhep_label_kwargs,
                )

                for extension in self.extensions:
                    self.output()[(variation, extension)].dump(fig, formatter="mpl")


