import os
from importlib.resources import path as resource_path
from pathlib import Path
from shutil import copy

import toml

from . import file_utils as fu

config_fname = "diviner_production_config.toml"
with resource_path("diviner.data", config_fname) as p:
    default_config_path = Path(p)


def read_config(fpath):
    return toml.load(fpath)


def copy_standard_config():
    "Copies the provided default config file into user's home."
    copy(default_config_path, Path.home())

class Config:
    def __init__(self):
        # search in home
        p = Path.home() / config_fname
        if p.exists():
            print(f"Found config {config_fname} in home directory.")
            self.data = read_config(p)
        else:
            print("No config file found.")
            return None

    @property
    def root(self):
        return Path(self.data['paths']['root'])

    @property
    def rdr2savedir(self):
        p = self.root / self.data['paths']['prodrun']
        if not p.exists():
            print(f"Creating {p}")
            p.mkdir(parents=True)
        return p

    @property
    def out_format(self):
        return self.data['calibration']['out_format']

    def get_rdr2_savename(self, tstr, c, savedir=None):
        if savedir is None:
            savedir = self.rdr2savedir
        return path.join(savedir, "{0}_C{1}_RDR_2.{2}".format(tstr, c, self.out_format))


class Configurator:

    savedir = "/luna4/maye/rdr_out/no_jpl_correction"
    # if not os.path.exists(savedir):
    #     os.makedirs(savedir)
    rdr2_root = "/luna4/maye/rdr_out/verification_no_jpl_corr"
    # if not os.path.exists(rdr2_root):
    #     os.o(rdr2_root)
    @classmethod
    def from_config_file(cls, fpath):
        config = read_config(fpath)
        tstart = config['run_control']['start']
        tstop = config['run_control']['stop']

        return cls()
    def __init__(
        self,
        tstart,
        tstop,
        overwrite=False,
        first_channel=9,
        last_channel=9,
        do_rad_corr=True,
        swap_clons=True,
        save_as_pipes=True,
    ):
        self.tstart = tstart
        self.tstop = tstop
        self.tstrings = fu.calc_daterange(tstart, tstop)
        self.run_name = tstart + "_" + tstop

        self.overwrite = overwrite

        self.c_start = first_channel
        self.c_end = last_channel

        self.do_rad_corr = do_rad_corr
        self.swap_clons = swap_clons
        self.save_as_pipes = save_as_pipes
        if save_as_pipes is True:
            self.out_format = "bin"
        else:
            self.out_format = "csv"
        self._config = None
        # set up paths
        # self.paths = SavePaths(do_rad_corr)
        # self.savedir = self.paths.savedir
        # self.rdr2_root = self.paths.rdr2_root

    @property
    def config(self):
        if self._config is None:
            # search in home
            p = Path.home() / config_fname
            if p.exists():
                print(f"Found config {config_fname} in home directory.")
                self._config = read_config(p)
            else:
                print("No config file found.")
                return None
        return self._config
