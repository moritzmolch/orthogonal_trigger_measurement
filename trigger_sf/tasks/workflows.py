import law

from trigger_sf.tasks.base import EfficiencyTask
from trigger_sf.tasks.efficiencies import PlotEfficiencies
from trigger_sf.tasks.scalefactors import PlotScaleFactors


class HadronicRecoilTriggerWorkflow(EfficiencyTask, law.WrapperTask):
    channel = "mm"
    variables = ["met", "ht"]
    processes = ["data", "dyjets", "ttbar"]
    ref_category = "mm_incl"
    sig_ref_category = "sig_pfht_trigger"

    def requires(self):
        # define parameters, which all tasks have in common
        common_params = {
            "channel": self.channel,
            "variables": self.variables,
            "ref_category": self.ref_category,
            "sig_ref_category": self.sig_ref_category,
        }

        # efficiency and scale factor plots for the hadronic recoil trigger
        reqs = [
            PlotEfficiencies.req(self, **common_params, processes=list(self.mc_process_insts.names())),
            PlotEfficiencies.req(self, **common_params, processes=list(self.data_process_insts.names())),
            PlotScaleFactors.req(self, **common_params, processes=self.processes),
        ]
        return reqs
