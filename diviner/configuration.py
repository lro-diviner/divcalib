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

    @property
    def root(self):
        return Path(self.data["paths"]["root"])

    @property
    def prodrun(self):
        return self.root / self.data["paths"]["prodrun"]

    @property
    def savedir(self):
        p = self.prodrun / self.data["paths"]["rad_tb"]
        if not p.exists():
            print(f"Creating {p}.")
            p.mkdir(parents=True)
        return p

    @property
    def pipes_dir(self):
        p = self.prodrun / self.data["paths"]["pipes"]
        if not p.exists():
            print(f"Creating {p}.")
            p.mkdir(parents=True)
        return p

    def get_rdr2_pipes_savename(self, tstr, c, savedir=None, corrected="corrected"):
        if savedir is None:
            savedir = self.pipes_dir
        return savedir / f"{tstr}_C{c}_RDR_2.{self.out_format}"
