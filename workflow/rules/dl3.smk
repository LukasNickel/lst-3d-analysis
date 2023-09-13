env = ENVS["lstchain"]
bkg_env = ENVS["background"]

dl2 = Path(OUTDIRS["dl2"])
dl3 = Path(OUTDIRS["dl3"])
irfs = Path(OUTDIRS["irfs"])

scripts = Path(SCRIPTS["dl3"])

irf_config = CONFIGS["irf_tool"]
bkg_config = CONFIGS["bkg_model"]


rule dl3:
    input:
        dl3 / "hdu-index.fits.gz",
        dl3 / "bkg-exists",


rule dl2_to_dl3:
    output:
        run=dl3 / "LST-1.Run{run_id}.dl3.fits.gz",
    input:
        data=dl2 / "LST-1.Run{run_id}.dl2.h5",
        irfs=MC_NODES_IRFs,
        config=irf_config,
    params:
        irf_pattern="irfs_*.fits.gz",
        out=dl3,
        in_irfs=irfs,
    conda:
        env
    resources:
        mem_mb=12000,
        time=30,
    log:
        dl3 / "create_dl3_{run_id}.log",
    shell:
        """
        lstchain_create_dl3_file  \
            --input-dl2 {input.data}  \
            --output-dl3-path {params.out}  \
            --input-irf-path {params.in_irfs}  \
            --irf-file-pattern {params.irf_pattern} \
            --config {input.config} \
            --gzip \
            --use-nearest-irf-node \
            --overwrite \
            --log-file {log}
        """


rule dl3_hdu_index:
    output:
        dl3 / "hdu-index.fits.gz",
    input:
        runs=DL3_FILES,
    params:
        outdir=dl3,
    conda:
        env
    log:
        dl3 / "hdu_index.log",
    resources:
        time=15,
    shell:
        """
        lstchain_create_dl3_index_files  \
            --input-dl3-dir {params.outdir}  \
            --output-index-path {params.outdir}  \
            --file-pattern '*.dl3.fits.gz'  \
            --overwrite \
            --log-file {log}
        """


rule calc_count_maps:
    output:
        dl3 / "bkg_cached_maps.pkl",
    input:
        runs=DL3_FILES,
        index=dl3 / "hdu-index.fits.gz",
        config=bkg_config,
        script=scripts / "precompute_background_maps.py",
    params:
        obs_dir=dl3,
        bkg_dir=dl3,
    conda:
        bkg_env
    resources:
        partition="long",
        time=360,
    log:
        dl3 / "calc_count_maps.log",
    shell:
        """python {input.script} \
        --input-dir {params.obs_dir} \
        --output {output} \
        --config {input.config} \
        --log-file {log} \
        --overwrite
        """


rule calc_background:
    output:
        #        bkg=expand(dl3 / "bkg_{run_id}.fits.gz", run_id=RUN_IDS), # cant use function in output
        dummy=dl3 / "bkg-exists",
    input:
        runs=DL3_FILES,
        index=dl3 / "hdu-index.fits.gz",
        config=bkg_config,
        calc_script=scripts / "calc_background.py",
        link_script=scripts / "link_bkg.py",
        cached_maps=dl3 / "bkg_cached_maps.pkl",
    params:
        obs_dir=dl3,
        bkg_dir=dl3,
    conda:
        bkg_env
    resources:
        partition="long",
        time=360,
    log:
        dl3 / "calc_bkg.log",
    shell:
        """python {input.calc_script} \
        --input-dir {params.obs_dir} \
        --output-dir {params.bkg_dir} \
        --dummy-output {output.dummy} \
        --cached-maps {input.cached_maps} \
        --config {input.config} \
        --log-file {log} \
        --overwrite

        python {input.link_script} \
        --hdu-index-path {input.index} \
        --bkg-dir {params.bkg_dir} \
        """


# Use lstchain env here to ensure we can load it
rule plot_background:
    output:
        dl3 / "plots/bkg_{run_id}.pdf",
    input:
        data=dl3 / "bkg_{run_id}.fits.gz",
        rc=os.environ.get("MATPLOTLIBRC", config_dir / "matplotlibrc"),
        script=scripts / "plot_bkg.py",
    conda:
        env
    log:
        dl3 / "plots/bkg_{run_id}.log",
    shell:
        "MATPLOTLIBRC={input.rc} python {input.script} -i {input.data} -o {output}"
