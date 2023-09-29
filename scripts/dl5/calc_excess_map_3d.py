from argparse import ArgumentParser

from gammapy.analysis import Analysis, AnalysisConfig
from gammapy.datasets import Datasets

parser = ArgumentParser()
parser.add_argument("-c", "--config", required=True)
parser.add_argument("--dataset-path", required=True)
parser.add_argument("-o", "--output", required=True)
args = parser.parse_args()


def main(config, dataset_path, output):
    config = AnalysisConfig.read(config)
    analysis = Analysis(config)
    analysis.get_observations()

    Datasets.read(dataset_path)


if __name__ == "__main__":
    main(**vars(args))