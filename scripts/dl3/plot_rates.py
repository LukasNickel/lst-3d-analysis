import logging
from argparse import ArgumentParser

import astropy.units as u
import matplotlib
import numpy as np
from astropy.table import Table
from gammapy.data import DataStore
from matplotlib import pyplot as plt

from scriptutils.log import setup_logging

if matplotlib.get_backend() == "pgf":
    from matplotlib.backends.backend_pgf import PdfPages
else:
    from matplotlib.backends.backend_pdf import PdfPages


log = logging.getLogger(__name__)


def main(input_path, output):  # noqa
    ds = DataStore.from_file(input_path)
    figures = []

    zen = []
    az = []
    ontime = []
    elapsed_time = []
    counts = []
    obs_ids = []
    deadc = []

    threshold_5 = []
    threshold_10 = []
    threshold_reco_data = []

    for o in ds.get_observations():
        i = o.obs_info
        log.info(o.obs_id)
        zen.append(90 - i["ALT_PNT"])
        az.append(i["AZ_PNT"])
        ontime.append(i["ONTIME"])
        elapsed_time.append(i["TELAPSE"])
        counts.append(len(o.events.table))
        deadc.append(i["DEADC"])
        obs_ids.append(o.obs_id)

        aeff_energy = o.aeff.axes["energy_true"].center
        # aeff in first fov offset bin
        x = o.aeff.data[:, 0]
        threshold_5.append(aeff_energy[np.argmax(x > 0.05 * max(x))].to_value(u.GeV))
        threshold_10.append(aeff_energy[np.argmax(x > 0.01 * max(x))].to_value(u.GeV))

        energies = o.events.energy.to_value(u.GeV)
        bins = np.linspace(0, 200, 200)
        c, edges = np.histogram(energies, bins)
        centers = (edges[1:] + edges[:-1]) / 2
        threshold_reco_data.append(centers[np.argmax(c)])

    ontime = u.Quantity(ontime, u.s)
    elapsed_time = u.Quantity(elapsed_time, u.s)
    deadc = np.array(deadc)

    rate = np.array(counts) / ontime
    rate2 = np.array(counts) / elapsed_time
    rate3 = np.array(counts) / elapsed_time / deadc

    Table(
        {
            "rate": rate,
            "counts": counts,
            "ontime": ontime,
            "elapsed_time": elapsed_time,
            "obs_id": obs_ids,
            "zen": zen,
            "az": az,
        },
    )
    fig, ax = plt.subplots()
    ax.scatter(az, ontime, label="ON Time")
    ax.scatter(az, elapsed_time, label="Elapsed Time")
    ax.scatter(az, elapsed_time * deadc, label="Elapsed Time * Deadc")
    ax.set_xlabel("Azimuth / deg")
    ax.set_ylabel("Time / s")
    ax.legend()
    figures.append(fig)

    fig, ax = plt.subplots()
    ax.scatter(zen, ontime, label="ON Time")
    ax.scatter(zen, elapsed_time, label="Elapsed Time")
    ax.scatter(zen, elapsed_time * deadc, label="Elapsed Time * Deadc")
    ax.set_xlabel("Zenith / deg")
    ax.set_ylabel("Time / s")
    ax.legend()
    figures.append(fig)

    fig, ax = plt.subplots()
    ax.scatter(obs_ids, ontime, label="ON Time")
    ax.scatter(obs_ids, elapsed_time, label="Elapsed Time")
    ax.scatter(obs_ids, elapsed_time * deadc, label="Elapsed Time * Deadc")
    ax.set_xlabel("Obs id")
    ax.set_ylabel("Time / s")
    ax.legend()
    figures.append(fig)

    for t in (threshold_5, threshold_10, threshold_reco_data):
        fig, ax = plt.subplots()
        ax.scatter(az, t)
        ax.set_xlabel("Azimuth / deg")
        ax.set_ylabel("Threshold energy / GeV")
        figures.append(fig)

        fig, ax = plt.subplots()
        ax.scatter(zen, t)
        ax.set_xlabel("Zenith / deg")
        ax.set_ylabel("Threshold energy / GeV")
        figures.append(fig)

        fig, ax = plt.subplots()
        ax.scatter(np.cos(np.deg2rad(zen)), t)
        ax.set_xlabel("cos(zd)")
        ax.set_ylabel("Threshold energy / GeV")
        figures.append(fig)

    for r in (rate, rate2, rate3):
        fig, ax = plt.subplots()
        ax.scatter(obs_ids, r)
        ax.set_xlabel("Obs id")
        ax.set_ylabel(f"Rate / {rate.unit}")
        figures.append(fig)

        fig, ax = plt.subplots()
        ax.scatter(zen, r)
        ax.set_xlabel("Zenith / deg")
        ax.set_ylabel(f"Rate / {rate.unit}")
        figures.append(fig)

        fig, ax = plt.subplots()
        ax.scatter(np.cos(np.deg2rad(zen)), r)
        ax.set_xlabel("cos(zd)")
        ax.set_ylabel(f"Rate / {rate.unit}")
        figures.append(fig)

        fig, ax = plt.subplots()
        ax.scatter(az, r)
        ax.set_xlabel("Azimuth / deg")
        ax.set_ylabel(f"Rate / {rate.unit}")
        figures.append(fig)

    if output is None:
        plt.show()
    else:
        with PdfPages(output) as pdf:
            for fig in figures:
                pdf.savefig(fig)


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-i", "--input-path", required=True)
    parser.add_argument("-o", "--output", required=True)
    parser.add_argument("--log-file")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()
    setup_logging(logfile=args.log_file, verbose=args.verbose)

    main(args.input_path, args.output)
