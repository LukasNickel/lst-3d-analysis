import logging
from argparse import ArgumentParser
from pathlib import Path

from scriptutils.link_utils import link
from scriptutils.log import setup_logging

log = logging.getLogger(__name__)


def main():
    parser = ArgumentParser()
    parser.add_argument("--mc-nodes-link-dir", required=True)
    parser.add_argument("--model-config-link-path", required=True)
    parser.add_argument("-o", "--output-path", required=True)
    parser.add_argument("--prod", required=True)
    parser.add_argument("--dec", required=True)
    parser.add_argument("--log-file")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()
    setup_logging(logfile=args.log_file, verbose=args.verbose)

    prod = args.prod
    dec = args.dec

    # Target is where the files are and linkname is where we want
    # to have them available in the build dir

    # Link the unmerged mc nodes
    template_target_nodes = (
        "/fefs/aswg/data/mc/DL1/AllSky/{prod}/TrainingDataset/{dec}"  # noqa
    )
    target_nodes = Path(template_target_nodes.format(prod=prod, dec=dec))
    linkname_nodes = Path(args.mc_nodes_link_dir)
    link(target_nodes, linkname_nodes)

    # Link model training config
    template_target_model = "/fefs/aswg/data/models/AllSky/{prod}/{dec}"
    target_model = Path(template_target_model.format(prod=prod, dec=dec))
    # config name might not be lstchain_config.json, but contain data, prod id...
    candidates_config = [x for x in target_model.glob("*lstchain*.json")]
    if len(candidates_config) == 0:
        raise Exception("config not found")
    elif len(candidates_config) > 1:
        raise Exception(f"Found multiple candidates: {candidates_config}")
    target_config = candidates_config[0]
    linkname_model = Path(args.model_config_link_path)
    link(target_config, linkname_model)

    output = Path(args.output_path)
    log.debug(f"Touch dummy output at {output}")
    output.touch()


if __name__ == "__main__":
    main()
