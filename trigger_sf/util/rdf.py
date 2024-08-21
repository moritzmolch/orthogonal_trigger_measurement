from __future__ import annotations


def sanitize_expression(expression: str):
    return " ".join([part.strip() for part in expression.split("\n") if len(part.strip()) > 0])


def _norm_weight(context):
    # get the process, the dataset and the campaign
    process = context.get("process", None)
    dataset = context.get("dataset", None)
    campaign = context.get("campaign", None)

    # do nothing if this is data
    if process.is_data:
        return context

    # get cross section, generator weight, luminosity and number of events
    lumi = campaign.x.lumi
    n_gen_events = dataset.n_events
    xsec = process.xsecs[13]
    negative_events_fraction = process.x.generator_weight

    # calculate the normalization weight
    definition = sanitize_expression(
        f"""
        ( -1.0 * (genWeight < 0) + 1.0 * (genWeight > 0) ) / ({negative_events_fraction} * {n_gen_events})
        * {xsec.nominal} * {lumi} * 1000
        """
    )
    context["events"] = context["events"].Define("norm_weight", definition)

    # add weight to the context
    context["weights"].append("norm_weight")

    return context


def weight_production(context):
    # add an empty weights list to the context
    context.setdefault("weights", [])

    # produce the normalization weight for MC events
    context = _norm_weight(context)

    # multiply weights in the weights list (or set weight to 1)
    if len(context["weights"]) > 0:
        context["events"] = context["events"].Define(
            "total_weight",
            " * ".join(context["weights"]),
        )
    else:
        context["events"] = context["events"].Define(
            "total_weight",
            "1",
        )

    return context


def _trg_single_mu_selection(context):
    selection = sanitize_expression(
        """
        (pt_1 >= 28. && trg_single_mu27 == 1)
        || (pt_1 >= 25. && trg_single_mu24 == 1)
        """
    )
    context["events"] = context["events"].Filter(selection, "trg_single_mu_selection")
    return context


def _dibjet_selection(context):
    selection = sanitize_expression(
        """
        (
            bpair_pt_1 >= 20.
            && bpair_pt_2 >= 20.
            && abs(bpair_eta_1) <= 2.5
            && abs(bpair_eta_2) <= 2.5
            && nbtag >= 2
        ) || (
            (
                fj_Xbb_pt >= 200.
                && abs(fj_Xbb_eta) <= 2.5
                && jpt_1 < 200.
                && mt_1 < 40.
                && nbtag == 0.
            )
            &&
            (
                (bpair_btag_value_2 < 0.049 && nbtag == 1)
                || nbtag == 0 
            )
        )
        """
    )
    context["events"] = context["events"].Filter(selection, "dibjet_selection")
    return context


def _dimuon_selection(context):
    selection = sanitize_expression(
        """
        pt_1 >= 28.
        && pt_2 >= 20.
        && abs(eta_1) <= 2.1
        && abs(eta_2) <= 2.1
        && iso_1 <= 0.15
        && iso_2 <= 0.15
        && q_1 * q_2 < 0
        """
    )
    context["events"] = context["events"].Filter(selection, "dimuon_selection")
    return context


def _trg_ak8pfjet400_trimmass30_selection(context):
    selection = "trg_ak8pfjet400_trimmass30 == 1"
    context["events"] = context["events"].Filter(selection, "dimuon_selection")
    return context
    

def _trg_pfht500_pfmet100_pfmht100_idtight_selection(context):
    selection = sanitize_expression(
        """
        trg_pfht500_pfmet100_pfmht100_idtight == 1
        && trg_ak8pfjet400_trimmass30 == 0
        """
    )
    context["events"] = context["events"].Filter(selection, "trg_pfht500_pfmet100_pfmht100_idtight_selection")
    return context


def channel_selection(context):
    # get the channel
    channel = context.get("channel")

    # selection of the mm channel
    if channel.name == "mm":
        context = _dibjet_selection(
            _dimuon_selection(
                _trg_single_mu_selection(
                    context
                )
            )
        )

    # selection of the tt channel
    # tt channel is disabled for now
    if channel.name == "tt":
        context["events"] = context["events"].Filter("1 == 0", "filter_all")

    return context


def category_selection(context):
    # get the channel
    category = context.get("category")

    # selection of the AK8 jet trigger category
    if category.name == "sig_ak8jet_trigger":
        context = _trg_ak8pfjet400_trimmass30_selection(context)       

    # selection of the HT trigger category
    elif category.name == "sig_pfht_trigger":
        context = _trg_pfht500_pfmet100_pfmht100_idtight_selection(context)       

    return context
