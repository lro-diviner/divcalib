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

        for k, v in self.data["calibration"].items():
            setattr(self, k, v)

        # this status attribute determines if paths are created for
        # corrected or uncorrected data
        self.corrected = False

    @property
    def root(self):
        return Path(self.data["paths"]["root"])

    @property
    def prodrun(self):
        return self.root / self.data["paths"]["prodrun"]

    @property
    def savedir(self):
        return self.prodrun / self.data["paths"]["rad_tb"]

    @property
    def corr(self):
        if self.corrected is True:
            return "corrected"
        elif self.corrected is False:
            return "uncorrected"
        else:
            return "merged"

    @property
    def rdr2_savedir(self):
        return self.prodrun / "rdr2"

    def get_tb_savename(self, tstr):
        p = self.savedir / f"{self.corr}/{tstr}_{self.corr}_tb.hdf"
        p.parent.mkdir(exist_ok=True, parents=True)
        return p

    def get_rad_savename(self, tstr):
        p = self.savedir / f"{self.corr}/{tstr}_{self.corr}_radiance.hdf"
        p.parent.mkdir(exist_ok=True, parents=True)
        return p

    def get_rdr2_savename(self, tstr, c):
        corr = self.corr
        savedir = self.rdr2_savedir
        p = savedir / f"{corr}/{self.out_format}/{tstr}_C{c}_RDR2_{corr}.{self.out_format}"
        p.parent.mkdir(exist_ok=True, parents=True)
        return p
