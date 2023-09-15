#!/usr/bin/env python
# coding: utf-8
import json
import logging
from argparse import ArgumentParser

import numpy as np
import pandas as pd
from astropy import units as u
from astropy.coordinates import SkyCoord
from gammapy.maps import MapAxis, WcsGeom, WcsNDMap
from lstchain.high_level.hdu_table import add_icrs_position_params
from lstchain.io import read_data_dl2_to_QTable
from lstchain.reco.utils import get_effective_time

log = logging.getLogger(__name__)


@u.quantity_input(width=u.deg)
def main(input_path, output_path, config, width, n_bins):
    with open(config, "r") as f:
        config = json.load(f)

    events = read_data_dl2_to_QTable(input_path, "on")
    trigger_type = events["trigger_type"]
    print(pd.Series(trigger_type).value_counts())
    # which type? 1 -> Data, 32 -> Pedestal
    print("Keeping all data")
    # print("Keeping ", np.count_nonzero(data), "/", len(events))
    # events = events[data]

    t_eff, t_ela = get_effective_time(events)
    events.meta["t_effective"] = t_eff
    events.meta["t_elapsed"] = t_ela

    source = SkyCoord(
        ra=config["DataReductionFITSWriter"]["source_ra"],
        dec=config["DataReductionFITSWriter"]["source_dec"],
    )
    # adds "RA", "Dec", "theta" to events
    events = add_icrs_position_params(events, source)

    evts = SkyCoord(events["RA"], events["Dec"], frame="icrs")

    r = width / 2
    bins = u.Quantity(
        [
            np.linspace(source.ra - r, source.ra + r, n_bins + 1),
            np.linspace(source.dec - r, source.dec + r, n_bins + 1),
        ],
    )

    hist, *edges = np.histogram2d(
        evts.ra.to_value(u.deg),
        evts.dec.to_value(u.deg),
        bins=bins.to_value(u.deg),
    )

    energy_axis = MapAxis.from_edges(
        u.Quantity([1e-5, 1e5], u.TeV),  # basically [-inf, inf], but finite
        name="energy",
    )
    geom = WcsGeom.create(
        (n_bins, n_bins),
        skydir=source,
        binsz=width / n_bins,
        width=width,
        axes=[energy_axis],
    )

    skymap = WcsNDMap(geom, hist)

    skymap.write(output_path, overwrite=True)


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-i", "--input-path", required=True)
    parser.add_argument("-o", "--output-path", required=True)
    parser.add_argument("-c", "--config", required=True)
    parser.add_argument(
        "--width",
        help="Width of skymap",
        default="4 deg",
        type=u.Quantity,
    )
    parser.add_argument("--n-bins", default=100)
    parser.add_argument("--log-file")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    main(**vars(args))