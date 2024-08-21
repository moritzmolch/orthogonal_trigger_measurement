#!/usr/bin/env bash


main() {
    # local paths of this script/directory
    local this_file="$( [ ! -z "${ZSH_VERSION}" ] && echo "${(%):-%x}" || echo "${BASH_SOURCE[0]}" )"
    local this_dir="$( cd "$( dirname "${this_file}" )" && pwd )"

    # environment paths
    export TSF_BASE="${this_dir}"
    export TSF_LOCAL_STORE="${TSF_BASE}/data"
    export TSF_MODULES="${TSF_BASE}/modules"

    # grid environment and LCG software stack
    source "/cvmfs/grid.cern.ch/alma9-ui-test/etc/profile.d/setup-alma9-test.sh"
    source "/cvmfs/sft.cern.ch/lcg/views/LCG_105/x86_64-el9-gcc11-opt/setup.sh"

    # software paths
    export PATH="${TSF_MODULES}/law/bin:${PATH}"
    export PYTHONPATH="${TSF_BASE}:${TSF_MODULES}/law:${TSF_MODULES}/order:${TSF_MODULES}/scinum:${TSF_MODULES}/luigi:${PYTHONPATH}"

    # law setup
    export LAW_HOME="${TSF_BASE}/.law"
    export LAW_CONFIG_FILE="${TSF_BASE}/law.cfg"
    source "$( law completion )"
    law index --quiet

}

main "${@}"