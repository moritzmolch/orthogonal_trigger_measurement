import law
import order as od

from trigger_sf.tasks.base import DatasetTask

law.contrib.load("wlcg")


class NTupleFiles(DatasetTask, law.ExternalTask):

    def output(self):
        # get the base directory for the NTuple files related to this dataset
        ntuple_dir = law.wlcg.WLCGDirectoryTarget(
            f"CROWNRun/{self.campaign_inst.x.year}/{self.dataset_inst.name}/{self.channel_inst.name}",
            fs="wlcg_fs_ntuple",
        )

        # get all children .root files
        ntuple_files = [ntuple_dir.child(child) for child in ntuple_dir.listdir(pattern="*.root")]

        return ntuple_files


class CreateHistograms(DatasetTask):

    category = law.Parameter(
        description="name of the category",
    )

    variables = law.CSVParameter(
        description="list of variables",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # get category instance
        self.category_inst = self.config_inst.get_category(self.category)

        # get variable instances and sort variable names
        self.variable_insts = od.UniqueObjectIndex(
            od.Variable,
            [self.config_inst.get_variable(v) for v in self.variables],
        )

    @property
    def variables_string(self):
        return "__".join(self.variables)

    @property
    def store_parts(self):
        return super().store_parts + (self.category, self.variables_string)

    def requires(self):
        return {
            "NTupleFiles": NTupleFiles.req(self)
        }

    def output(self):
        return self.local_target("histogram.pickle")

    def run(self):
        # delayed imports, as packages are only needed for this task
        import ROOT
        from trigger_sf.util.rdf import category_selection, channel_selection, weight_production
        from trigger_sf.util.histograms import create_hist

        # get list of ntuple files
        ntuple_files = [file.uri() for file in self.input()["NTupleFiles"]]

        # load ntuple files and create context
        events = ROOT.RDataFrame("ntuple", ntuple_files)
        ROOT.RDF.Experimental.AddProgressBar(events)
        context = {
            "campaign": self.campaign_inst,
            "channel": self.channel_inst,
            "category": self.category_inst, 
            "dataset": self.dataset_inst,
            "process": self.process_inst,
            "events": events,
        }

        # produce weights
        context = weight_production(context)

        # apply selections
        context = channel_selection(context)
        context = category_selection(context)

        # get histogram data as numpy array
        events = context["events"]
        variable_expressions = [v.expression for v in self.variable_insts]
        values = events.AsNumpy(columns=variable_expressions + ["total_weight"])
        weight = values.pop("total_weight")

        # create and fill the histogram
        h = create_hist(self.config_inst, self.variable_insts)
        args = [
            self.category_inst.name,
            self.process_inst.get_root_processes()[0].name,
        ]
        args.extend([values[e] for e in variable_expressions])
        h.fill(*args, weight=weight)

        # save the histogram as task output
        self.output().dump(h, formatter="pickle")
