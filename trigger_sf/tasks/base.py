"""
Basic task structure adapted from https://github.com/riga/law_example_CMSSingleTopAnalysis/blob/master/analysis/framework/tasks.py
"""

import law
import luigi
import order as od
import os

from trigger_sf.config import trigger_sf_analysis

law.contrib.load("matplotlib", "numpy", "wlcg")


class AnalysisTask(law.Task):

    version = luigi.Parameter(
        description="version tag of the task execution; default: 'v1'",
        default="v1",
    )

    analysis = "xyh_bbtautau_trigger_sf"

    @classmethod
    def get_task_namespase(cls):
        return cls.analysis

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # get the analysis instance
        self.analysis_inst = trigger_sf_analysis

    @property
    def store_parts(self):
        return (self.task_family, )

    @property
    def store_parts_opt(self):
        parts = tuple()
        if not law.is_no_param(self.version):
            parts += (self.version,)
        return parts

    @property
    def local_store(self):
        parts = (os.getenv("TSF_LOCAL_STORE"), ) + self.store_parts + self.store_parts_opt
        return os.path.join(*parts)

    def local_path(self, *parts):
        return os.path.join(self.local_store, *[str(part) for part in parts])

    def local_target(self, *parts, **kwargs):
        target_cls = law.LocalDirectoryTarget if kwargs.pop("is_dir", False) else law.LocalFileTarget
        return target_cls(self.local_path(*parts))


class ConfigTask(AnalysisTask):
    config = luigi.Parameter(default="ul_2018")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config_inst = self.analysis_inst.get_config(self.config)
        self.campaign_inst = self.config_inst.campaign

    @property
    def store_parts(self):
        return super().store_parts + (self.config, )


class DatasetTask(ConfigTask):

    channel = luigi.Parameter(
        description="name of channel; corresponds to a 'scope' processed in CROWN",
    )

    dataset = luigi.Parameter(
        description="name of the dataset",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # get the channel instance
        self.channel_inst = self.config_inst.get_channel(self.channel)

        # get the dataset instance
        self.dataset_inst = self.config_inst.get_dataset(self.dataset)

        # if the dataset has at least one process, load the first one as process instance
        self.process_inst = None
        processes = list(self.dataset_inst.processes.values())
        if len(processes) > 0:
            self.process_inst = processes[0]

    @property
    def store_parts(self):
        return super().store_parts + (self.channel, self.dataset, )


class EfficiencyTask(ConfigTask):

    channel = luigi.Parameter(
        description="name of the channel",
    )

    variables = law.CSVParameter(
        description="comma-separated list of variables",
    )

    processes = law.CSVParameter(
        description="comma-separated list of processes",
    )

    ref_category = luigi.Parameter(
        description="name of the category, which represents the reference dataset of the trigger efficiency measurement",
    )

    sig_ref_category = luigi.Parameter(
        description="name of the category, which represents the reference+signal dataset of the trigger efficiency measurement; must be a subset of the reference category",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # get the channel instance
        self.channel_inst = self.config_inst.get_channel(self.channel)

        # get signal and reference category instances
        self.ref_category_inst = self.config_inst.get_category(self.ref_category)
        self.sig_ref_category_inst = self.config_inst.get_category(self.sig_ref_category)

        # get variable instances
        self.variable_insts = od.UniqueObjectIndex(
            od.Variable,
            [self.config_inst.get_variable(v) for v in self.variables],
        )

        # get process instances and sort process names
        self.processes = tuple(sorted(list(self.processes)))
        self.process_insts = od.UniqueObjectIndex(
            od.Process,
            [self.config_inst.get_process(v) for v in self.processes],
        )

    @property
    def categories_string(self):
        return "__".join([self.ref_category, self.sig_ref_category])

    @property
    def variables_string(self):
        return "__".join(self.variables)

    @property
    def processes_string(self):
        return "__".join(self.processes)

    @property
    def processes_label(self):
        return "+".join([p.label for p in self.process_insts.values()])

    @property
    def data_process_insts(self):
        return od.UniqueObjectIndex(
            od.Process,
            [p for p in self.process_insts if p.is_data],
        )

    @property
    def mc_process_insts(self):
        return od.UniqueObjectIndex(
            od.Process,
            [p for p in self.process_insts if p.is_mc],
        )

    @property
    def store_parts(self):
        return super().store_parts + (self.channel, self.categories_string, self.variables_string, self.processes_string)

    @property
    def variations(self):
        return ["nominal", "up", "down"]
