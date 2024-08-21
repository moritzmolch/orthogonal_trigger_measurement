from __future__ import annotations
from functools import cache
import json
import order as od
from pathlib import Path
import scinum
from typing import Any, Dict, Optional
import yaml


@cache
def sample_database(database_file: Path | str) -> Dict[str, Any]:
    database_file = Path(database_file)
    sample_database = {}
    with open(database_file, mode="r") as f:
        if database_file.suffix == ".json":
            sample_database = json.load(f)
        elif database_file.suffix == ".yaml":
            sample_database = yaml.safe_load(f)
    return sample_database


def add_config(analysis: od.Analysis, year: int, postfix: Optional[str] = None):
    if year != 2018:
        raise ValueError("other eras than 2018 not implemented yet")

    # create the campaign
    cpn = od.Campaign(
        name="ul_2018",
        id=1,
        aux={
            "year": 2018,
            "lumi": 59.83,
        },
    )

    # add config to analysis via created campaign
    config = analysis.add_config(campaign=cpn)

    return config


def add_processes(analysis: od.Analysis, config: od.Config):

    config.add_process(
        name="data",
        id=100,
        label="data",
        is_data=True,
    )

    config.add_process(
        name="dyjets",
        id=200,
        label=r"DY($\ell\ell$)+jets",
        is_data=False,
    )

    config.add_process(
        name="ttbar",
        id=300,
        label=r"t$\bar{t}$",
        is_data=False,
    )


def add_datasets(analysis: od.Analysis, config: od.Config):

    # get processes
    data = config.get_process("data")
    dyjets = config.get_process("dyjets")
    ttbar = config.get_process("ttbar")

    # ID counter
    id = 1

    # add data samples
    for sub_era in ["A", "B", "C", "D"]:
        # construct the dataset name
        name = f"SingleMuon_Run2018{sub_era}-UL2018"

        # get sample database
        dataset_db_entry = sample_database(analysis.x.sample_database_path)[name]

        # create process
        process = data.add_process(
            name="data_singlemuon_2018{}".format(sub_era),
            id=data.id + id,
            is_data=True,
        )

        # create dataset
        config.add_dataset(
            name=name,
            id=id,
            keys=[dataset_db_entry["dbs"]],
            processes=[process],
            n_files=dataset_db_entry["nfiles"],
            n_events=dataset_db_entry["nevents"],
        )

        # increase ID counter
        id += 1


    # add DY+Jets samples
    for pt_bin in ["0To50", "50To100", "100To250", "250To400", "400To650", "650ToInf"]:
        # construct the dataset and process name
        name = f"DYJetsToLL_LHEFilterPtZ-{pt_bin}_MatchEWPDG20_TuneCP5_13TeV-amcatnloFXFX-pythia8_RunIISummer20UL18NanoAODv9-106X"
        process_name = "dyjets_"
        pt_bin_parts = pt_bin.split("To")
        if pt_bin_parts[1] == "Inf":
            process_name += f"{pt_bin_parts[0]}"
        else:
            process_name += f"{pt_bin_parts[0]}to{pt_bin_parts[1]}"

        # get sample database
        dataset_db_entry = sample_database(analysis.x.sample_database_path)[name]

        # create process
        process = dyjets.add_process(
            name=process_name,
            id=dyjets.id + id,
            is_data=False,
            xsecs={
                13: scinum.Number(dataset_db_entry["xsec"]),
            },
            aux={
                "generator_weight": dataset_db_entry["generator_weight"],
            },
        )

        # create dataset
        config.add_dataset(
            name=name,
            id=id,
            keys=[dataset_db_entry["dbs"]],
            processes=[process],
            n_files=dataset_db_entry["nfiles"],
            n_events=dataset_db_entry["nevents"],
        )

        # increase ID counter
        id += 1

    # add ttbar samples
    for channel in ["Hadronic", "SemiLeptonic", "2L2Nu"]:
        # construct the dataset and process name
        name = f"TTTo{channel}_TuneCP5_13TeV-powheg-pythia8_RunIISummer20UL18NanoAODv9-106X"
        process_name = "ttbar_"
        if channel == "Hadronic":
            process_name += "had"
        elif channel == "SemiLeptonic":
            process_name += "sl"
        elif channel == "2L2Nu":
            process_name += "dl"

        # get sample database
        dataset_db_entry = sample_database(analysis.x.sample_database_path)[name]

        # create process
        process = ttbar.add_process(
            name=process_name,
            id=ttbar.id + id,
            is_data=False,
            xsecs={
                13: scinum.Number(dataset_db_entry["xsec"]),
            },
            aux={
                "generator_weight": dataset_db_entry["generator_weight"],
            },
        )

        # create dataset
        config.add_dataset(
            name=name,
            id=id,
            keys=[dataset_db_entry["dbs"]],
            processes=[process],
            n_files=dataset_db_entry["nfiles"],
            n_events=dataset_db_entry["nevents"],
        )

        # increase ID counter
        id += 1


def add_variables(analysis: od.Analysis, config: od.Config):
    # add hadronic recoil variables
    config.add_variable(
        name="met",
        id=1,
        expression="met",
        binning=[0, 100, 150, 200, 250, 300, 350, 400],
        x_title=r"$p_{\mathrm{T}}^{\mathrm{miss}}$",
        unit="GeV",
        unit_format="{title} ({unit})",
    )

    config.add_variable(
        name="mht_pt",
        id=2,
        expression="mht_pt",
        binning=[0, 50, 100, 150, 200, 300, 400, 500, 1000],
        x_title=r"$|\vec{H}_{\mathrm{T}}|$",
        unit="GeV",
        unit_format="{title} ({unit})",
    )

    config.add_variable(
        name="ht",
        id=3,
        expression="ht",
        binning=[0, 400, 500, 600, 700, 800, 900, 1000],
        x_title=r"$H_{\mathrm{T}}$",
        unit="GeV",
        unit_format="{title} ({unit})",
    )


def add_channels(analysis: od.Analysis, config: od.Config):
    # di-muon channel
    config.add_channel(
        name="mm",
        id=1,
    )

    # di-tau_h channel
    config.add_channel(
        name="tt",
        id=2,
    )


def add_categories(analysis: od.Analysis, config: od.Config):
    # get the channels
    mm = config.get_channel("mm") 
    tt = config.get_channel("tt")

    # categories in the di-muon channel
    config.add_category(mm.add_category(
        name="mm_incl",
        id=101,
        aux={
            "variables": od.UniqueObjectIndex(od.Variable, [
                config.get_variable("ht"),
                config.get_variable("mht_pt"),
            ]),
        },
    ))

    config.add_category(mm.add_category(
        name="sig_ak8jet_trigger",
        id=102,
        aux={
            "variables": od.UniqueObjectIndex(od.Variable, []),
        },
    ))

    config.add_category(mm.add_category(
        name="sig_pfht_trigger",
        id=103,
        aux={
            "variables": od.UniqueObjectIndex(
                od.Variable,
                [
                    config.get_variable("ht"),
                    config.get_variable("mht_pt"),
                ]
            )
        }
    ))

    # categories in the di-tau_h channel
    config.add_category(tt.add_category(
        name="tt_incl",
        id=204,
        aux={
            "variables": od.UniqueObjectIndex(od.Variable, []),
        },
    ))


# create the analysis and add all objects
analysis = trigger_sf_analysis = od.Analysis(
    name="boosted_tt_trigger_sf",
    id=1,
    aux={
        "ntuple_tree": "ntuple",
        "ntuple_base_path": "root://cmsdcache-kit-disk.gridka.de//store/user/mmolch/CROWN/ntuples/nmssm_2024-08_v1",
        "sample_database_path": "/work/mmolch/xyh-bbtautau/KingMaker/sample_database/datasets.json",
    },
)
config = config_2018 = add_config(analysis, 2018)
add_variables(analysis, config)
add_processes(analysis, config)
add_datasets(analysis, config)
add_channels(analysis, config)
add_categories(analysis, config)
