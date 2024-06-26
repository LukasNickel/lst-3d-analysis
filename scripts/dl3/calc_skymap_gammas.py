import json
import logging
from argparse import ArgumentParser

from astropy import units as u
from gammapy.data import DataStore
from gammapy.maps import MapAxis, WcsGeom, WcsNDMap

from scriptutils.log import setup_logging

log = logging.getLogger(__name__)


@u.quantity_input(width=u.deg)
def main(input_path, config, output_path, obs_id, width, n_bins):  # noqa: PLR0913
    with open(config, "r") as f:
        config = json.load(f)

    ds = DataStore.from_dir(input_path)

    obs = ds.obs(int(obs_id), ["aeff"])

    events = obs.events

    source = obs.target_radec
    pointing = obs.get_pointing_icrs(obs.tmid)
    log.info(obs.obs_id)
    log.info(f"source: {source}")
    log.info(f"pointing: {pointing}")
    log.info(f"{pointing.separation(source)}")

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

    skymap = WcsNDMap(geom)
    skymap.fill_events(events)
    skymap.meta["pointing_ra_deg"] = pointing.ra.to_value(u.deg)
    skymap.meta["pointing_dec_deg"] = pointing.dec.to_value(u.deg)

    skymap.write(output_path, overwrite=True)


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-i", "--input-path", required=True)
    parser.add_argument("-o", "--output-path", required=True)
    parser.add_argument("-c", "--config", required=True)
    parser.add_argument("--obs-id", required=True)
    parser.add_argument(
        "--width",
        help="Width of skymap",
        default="5 deg",
        type=u.Quantity,
    )
    parser.add_argument("--n-bins", default=100, type=int)
    parser.add_argument("--log-file")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()
    setup_logging(logfile=args.log_file, verbose=args.verbose)

    main(
        args.input_path,
        args.config,
        args.output_path,
        args.obs_id,
        args.width,
        args.n_bins,
    )
