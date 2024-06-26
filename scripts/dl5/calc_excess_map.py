import logging
import pickle
from argparse import ArgumentParser

from gammapy.estimators import ExcessMapEstimator

from scriptutils.io import load_datasets_with_models
from scriptutils.log import setup_logging

log = logging.getLogger(__name__)


def main(datasets_path, models_path, output):
    datasets = load_datasets_with_models(datasets_path, models_path)

    # TODO make the smoothing configurable
    # Understand how exactly this works
    # Do I need the best fit models attached? fit bkg? No, right?
    # Kernel width vs spatial model size?
    estimator = ExcessMapEstimator(
        correlation_radius="0.2 deg",
        selection_optional="all",
    )
    maps = {}
    # Stacked
    stacked = datasets.stack_reduce()
    ts_maps = estimator.run(stacked)
    ts_maps.write(output, overwrite=True)
    maps["stacked"] = ts_maps
    for d in datasets:
        ts_maps = estimator.run(d.to_masked())
        maps[d.name] = ts_maps

    with open(output, "wb") as f:
        pickle.dump(maps, f)


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--datasets-path", required=True)
    parser.add_argument("--models-path", required=True)
    parser.add_argument("-o", "--output", required=True)
    parser.add_argument("--log-file")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()
    setup_logging(logfile=args.log_file, verbose=args.verbose)

    main(args.datasets_path, args.models_path, args.output)
