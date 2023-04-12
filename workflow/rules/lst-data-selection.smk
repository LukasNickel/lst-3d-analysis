# vim: ft=snakemake nofoldenable commentstring=#%s
# https://github.com/snakemake/snakemake/tree/main/misc/vim

import json
from itertools import chain

with open("build/runs.json", "r") as f:
    runs = json.load(f)

RUN_IDS = sorted(set(chain(*runs.values())))

with open("configs/lst_agn.json", "r") as f:
    config = json.load(f)

lstchain_env = config.get("lstchain_enviroment", "lstchain-v0.9.13")

gammapy_env = "envs/environment.yml"

irf_plots = [
    f"build/plots/irf/{irf}_Run{run_id:05d}.pdf"
    for irf in ("aeff", "edisp", "gh_cut", "radmax_cut")
    for run_id in RUN_IDS
]


include: "local.smk"


rule all:
    input:
        plots,
        irf_plots,


localrules:
    irf,
    plot_irf,


rule plot_irf:
    output:
        "build/plots/irf/{irf}_Run{run_id}.pdf",
    input:
        data="build/irf/calculated/irf_Run{run_id}.fits.gz",
        script="scripts/plot_irf_{irf}.py",
        rc=os.environ.get("MATPLOTLIBRC", "configs/matplotlibrc"),
    resources:
        mem_mb=1000,
        time=5,  # minutes
    conda:
        gammapy_env
    shell:
        "MATPLOTLIBRC={input.rc} python {input.script} -i {input.data} -o {output}"


rule calc_theta2:
    output:
        "build/dl4/{analysis}/theta2.fits.gz",
    input:
        data="build/dl3/hdu-index.fits.gz",
        config="configs/{analysis}/analysis.yaml",
        script="scripts/calc_theta2.py",
    resources:
        mem_mb=16000,
    conda:
        gammapy_env
    shell:
        "python {input.script} -c {input.config} -o {output}"


rule calc_flux_points:
    input:
        data="build/dl4/{analysis}/datasets.fits.gz",
        config="configs/{analysis}/analysis.yaml",
        model="build/dl4/{analysis}/model-best-fit.yaml",
        script="scripts/calc_flux_points.py",
    output:
        "build/dl4/{analysis}/flux_points.fits.gz",
    conda:
        gammapy_env
    shell:
        """
        python {input.script} \
            -c {input.config} \
            --dataset-path {input.data} \
            --best-model-path {input.model} \
            -o {output}
        """


ruleorder: plot_flux_points > plot


rule plot_flux_points:
    input:
        data="build/dl4/{analysis}/flux_points.fits.gz",
        model="build/dl4/{analysis}/model-best-fit.yaml",
        script="scripts/plot_flux_points.py",
    output:
        "build/plots/{analysis}/flux_points.pdf",
    conda:
        gammapy_env
    shell:
        """
        python {input.script} \
            -i {input.data} \
            --best-model-path {input.model} \
            -o {output}
        """


rule observation_plots:
    input:
        "build/dl3/hdu-index.fits.gz",
        config="configs/{analysis}/analysis.yaml",
        script="scripts/events.py",
    output:
        "build/plots/{analysis}/observation_plots.pdf",
    resources:
        mem_mb=64000,
    conda:
        gammapy_env
    shell:
        """
        python {input.script} \
            -c {input.config} \
            -o {output} \
        """


rule sensitivity:
    input:
        "build/model-best-fit.yaml",
        "build/dl3/hdu-index.fits.gz",
        script="scripts/sensitivity.py",
    output:
        "build/plots/sensitivity.pdf",
    conda:
        gammapy_env
    shell:
        "python {input.script} -o {output}"


rule calc_light_curve:
    input:
        model="build/dl4/{analysis}/model-best-fit.yaml",
        config="configs/{analysis}/analysis.yaml",
        dataset="build/dl4/{analysis}/datasets.fits.gz",
        script="scripts/calc_light_curve.py",
    output:
        "build/dl4/{analysis}/light_curve.fits.gz",
    conda:
        gammapy_env
    shell:
        """
        python {input.script} \
            -c {input.config} \
            --dataset-path {input.dataset} \
            --best-model-path {input.model} \
            -o {output} \
        """


rule model_best_fit:
    input:
        config="configs/{analysis}/analysis.yaml",
        dataset="build/dl4/{analysis}/datasets.fits.gz",
        model="configs/{analysis}/models.yaml",
        script="scripts/fit-model.py",
    output:
        "build/dl4/{analysis}/model-best-fit.yaml",
    conda:
        gammapy_env
    shell:
        """
        python {input.script} \
            -c {input.config} \
            --dataset-path {input.dataset} \
            --model-config {input.model} \
            -o {output} \
        """


rule dataset:
    input:
        data="build/dl3/hdu-index.fits.gz",
        config="configs/{analysis}/analysis.yaml",
        script="scripts/write_datasets.py",
    output:
        "build/dl4/{analysis}/datasets.fits.gz",
    resources:
        cpus=16,
        mem_mb="32G",
        time=30,  # minutes
    conda:
        gammapy_env
    shell:
        "python {input.script} -j{resources.cpus} -c {input.config} -o {output} --n-off-regions=1"


rule dl3_hdu_index:
    conda:
        lstchain_env
    output:
        "build/dl3/hdu-index.fits.gz",
    input:
        expand(
            "build/dl3/dl3_LST-1.Run{run_id:05d}.fits.gz",
            run_id=RUN_IDS,
        ),
    resources:
        time=15,
    shell:
        """
        lstchain_create_dl3_index_files  \
            --input-dl3-dir build/dl3/  \
            --output-index-path build/dl3/  \
            --file-pattern 'dl3_*.fits.gz'  \
            --overwrite \
        """


# rule select_low_offset:
#     output:
#         "build/dl3/dl3_LST-1.Run{run_id}.fits.gz",
#     input:
#         "build/dl3/dl3_LST-1.Run{run_id}.fits.gz",
#     conda:
#         gammapy_env
#     resources:
#         time=10,
#     log:
#         "build/logs/dl3/{run_id}.log",
#     shell:
#         """
#         python scripts/select_low_offset.py \
#             -i {input} -o {output} \
#         """


rule dl3:
    output:
        "build/dl3/dl3_LST-1.Run{run_id}.fits.gz",
    input:
        data="build/dl2/dl2_LST-1.Run{run_id}.h5",
        irf="build/irf/calculated/irf_Run{run_id}.fits.gz",
        config="configs/irf_tool_config.json",
    resources:
        mem_mb="12G",
        time=30,
    conda:
        lstchain_env
    log:
        "build/logs/dl3/{run_id}.log",
    shell:
        """
        lstchain_create_dl3_file  \
            --input-dl2 {input.data}  \
            --output-dl3-path $(dirname $(realpath {output}))  \
            --input-irf {input.irf}  \
            --config {input.config} \
            --gzip \
            --overwrite \
        """


rule dl2:
    resources:
        mem_mb="64G",
    output:
        "build/dl2/dl2_LST-1.Run{run_id}.h5",
    input:
        data="build/dl1/dl1_LST-1.Run{run_id}.h5",
        config="build/models/model_Run{run_id}/lstchain_config.json",
    conda:
        lstchain_env
    log:
        "build/logs/dl2/{run_id}.log",
    shell:
        """
        lstchain_dl1_to_dl2  \
            --input-file {input.data}  \
            --output-dir $(dirname $(realpath {output}))  \
            --path-models $(dirname {input.config})  \
            --config {input.config}  \
        """


rule irf:
    resources:
        mem_mb="8G",
        time=10,
    output:
        "build/irf/calculated/irf_Run{run_id}.fits.gz",
    input:
        gammas="build/dl2/test/dl2_LST-1.Run{run_id}.h5",
        config="configs/irf_tool_config.json",
    conda:
        lstchain_env
    shell:
        """
        lstchain_create_irf_files \
            -o {output} \
            -g {input.gammas} \
            --config {input.config} \
        """
