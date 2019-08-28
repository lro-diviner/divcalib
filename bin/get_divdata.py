#!/usr/bin/env python
import pandas as pd
import sys
import os
from subprocess import call
from diviner.data_prep import parse_divdata_times, index_by_time

# global list of columns to be extracted. will be adaptable by user later
columns = "year,month,date,hour,minute,second,jdate,c,det,clat,clon,radiance,tb".split(
    ","
)

# prepare the divdata_cache access
user = os.environ["USER"]
if sys.platform == "darwin":
    datadir = os.path.join(os.environ["HOME"], "data", "diviner")
else:
    datadir = os.path.join("/raid1", user)
divdata_cache = os.path.join(datadir, "divdata")
if not os.path.exists(divdata_cache):
    os.mkdir(divdata_cache)


def create_cmd_string(tstr, cstart, detstart, outfname, cend=None, detend=None):
    if not cend:
        cend = cstart
    if not detend:
        detend = detstart
    pipes_root = "/u/marks/luner/pipes/rel"
    divdata_cmd = "/u/marks/luner/c38/rel/divdata"
    divdata_opt1 = "daterange={0}".format(tstr)
    divdata_opt2 = "clat=-90,90 c={0},{1} det={2},{3}".format(
        cstart, cend, detstart, detend
    )
    pextract_cmd = os.path.join(pipes_root, "pextract")
    pprint_cmd = os.path.join(pipes_root, "pprint")
    pextract_opt = "extract={}".format(",".join(columns))
    pprint_opt = "titles=0 >"
    cmd = (
        "tcsh -c '{divdata_cmd} {divdata_opt1} {divdata_opt2}|"
        "{pextract_cmd} {pextract_opt}|"
        "{pprint_cmd} {pprint_opt} "
        "{outfname}'".format(
            divdata_cmd=divdata_cmd,
            divdata_opt1=divdata_opt1,
            divdata_opt2=divdata_opt2,
            pextract_cmd=pextract_cmd,
            pextract_opt=pextract_opt,
            pprint_cmd=pprint_cmd,
            pprint_opt=pprint_opt,
            outfname=outfname,
        )
    )
    return cmd


def output_basename(tstr, cstart, cend, detstart, detend, ext):
    basename = "{tstr}_{cstart}-{cend}_{detstart}-{detend}_divdata.{ext}".format(
        tstr=tstr, cstart=cstart, cend=cend, detstart=detstart, detend=detend, ext=ext
    )
    return basename


def get_divdata(
    tstr,
    cstart,
    detstart,
    savedir=divdata_cache,
    cend=None,
    detend=None,
    create_hdf=True,
    drop_dates=True,
    keep_csv=False,
    save_hdf=False,
    ignore_cache=False,
    get_day=False,
):
    """tstr in format %Y%m%d%H as usual.

    Parameters:
        tstr: In usual format %Y%m%d%H
        c, det:  Diviner channel and detector numbers
        savedir: path for the output files to be stored, default: current
        create_hdf: Parse the pprint text file into a pandas dataframe and return it to caller
            Default is True
        save_hdf: Save the pandas dataframe to disk, this is an option for the command-line
            use of this tool. Dataframe handle in HDF file is 'df'. Default is False
        keep_csv: boolean to decide if to delete the tmp csv or to keep
        drop_dates: if you can't cope with datetime object, you can keep
            the time columns in the dataframe.

    Have to embed everything in a tc-shell call because otherwise
    the paths are not set-up correctly.
    """
    if not cend:
        cend = cstart
    if not detend:
        detend = detstart
    if len(tstr) < 10 and get_day == False:
        print("If you really want data for a whole day, set 'get_day' to True")
        return
    # define fname paths
    basetext = output_basename(tstr, cstart, cend, detstart, detend, "tab")
    basehdf = output_basename(tstr, cstart, cend, detstart, detend, "h5")
    textfname = os.path.join(savedir, basetext)
    hdffname = os.path.join(savedir, basehdf)
    # if csv is not wanted, only the hdf is of interest, so if it's there, return that.
    # Note that hdf's are only stored with option save_hdf=True
    if not (keep_csv or ignore_cache):
        if os.path.exists(hdffname):
            print("Found divdata HDF in cache. Returning that.")
            df = pd.read_hdf(hdffname, "df")
            return df
    cmd = create_cmd_string(tstr, cstart, detstart, textfname, cend=cend, detend=detend)
    print("Calling\n", cmd)
    sys.stdout.flush()
    call(cmd, shell=True)
    if os.path.exists(textfname):
        print("Created text file", textfname)
        print("Size:", os.path.getsize(textfname))
    else:
        print("Something went wrong, cannot find the output file.")
        return
    if create_hdf:
        print("Pandas parsing...")
        df = pd.read_csv(textfname, delim_whitespace=True)
        # first column is empty
        df.drop(df.columns[0], axis=1, inplace=True)
        # parse times and drop time columns
        df = parse_divdata_times(df, drop_dates=drop_dates)
        df.sort_index(inplace=True)
        if not keep_csv:
            print("Removing temporary text file", textfname)
            os.remove(textfname)
        if save_hdf:
            print("Creating HDF file:", hdffname)
            df.to_hdf(hdffname, "df")
        return df


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Create divdata argument string, call divdata"
        " via subprocess.call() and save a text version created with pprint. Currently extracted"
        " data columns are: year,month,date,hour,minute,second,jdate,c,det,clat,clon,radiance,tb."
        " Parse and save into a HDF5 file with pandas if --create_hdf option is used."
        " Note that the optional arguments (starting with --) can be provided at any position"
        " in the command, e.g. at the end after timestring cstart and detstart."
    )

    # positional arguments
    parser.add_argument(
        "timestring",
        default="%Y%m%d%H",
        help="In usual format %(default)s, for example 2010100412. "
        "Currently no time-range implemented. Output filename will be "
        "'timestring_divdata.csv'.",
    )
    parser.add_argument(
        "cstart",
        help="cstart. Diviner channel number to start from. "
        "Ranges between 1 and 9. Finish with --cend if required. "
        "Default is to only provide data for this channel.",
        type=int,
        choices=range(1, 10),
    )
    parser.add_argument(
        "detstart",
        help="detstart. Diviner detector number to start from. "
        "Finish with optional argument --detend if required. "
        "Default is to only provide data for this detector.",
        type=int,
        choices=range(1, 22),
    )

    # optional arguments
    parser.add_argument(
        "-s",
        "--savedir",
        help="Path to folder where to save the output file. "
        "Default is to use '', which means current folder.",
        default="",
    )
    parser.add_argument(
        "--cend",
        help="Last Diviner channel to provide data for.",
        type=int,
        choices=range(1, 10),
    )
    parser.add_argument(
        "--detend",
        help="Last Diviner detector number to provide data for.",
        type=int,
        choices=range(1, 22),
    )
    parser.add_argument(
        "--create_hdf",
        help="Boolean flag. If active, parse CSV file with pandas"
        " and save HDF5 file with times parsed into "
        "datetime index. Dataframe handle in HDF file "
        "is 'df'.",
        action="store_true",
    )
    parser.add_argument(
        "--keep_csv",
        help="Boolean flag. If active, don't delete the csv file "
        "if active after creating the HDF5 file.",
        action="store_true",
    )
    parser.add_argument(
        "--keep_dates",
        help="Boolean. Drop the separate date and "
        "time columns when parsing time into a datetime "
        "object. Default is 'False'.",
        action="store_true",
    )
    parser.add_argument(
        "-t",
        "--test",
        help="Print out the call command for verification and" " exit.",
        action="store_true",
    )

    parser.add_argument(
        "-c",
        "--col",
        help="Add a requested column to the pextract call."
        " One can either put columns in a comma-separated"
        " list like 'abc,def' (no whitespaces) or"
        " call this argument several times like '-c abc"
        " -c def'.",
        action="append",
    )

    args = parser.parse_args()
    if len(args.timestring) != 10:
        print("\n Nope! timestring has to be 10 characters!\n")
        parser.print_help()
        sys.exit()
    if args.col:
        columns.extend(args.col)
    if args.test:
        cmd = create_cmd_string(
            args.timestring,
            args.cstart,
            args.detstart,
            args.savedir,
            cend=args.cend,
            detend=args.detend,
        )
        print("Command verification:\n", cmd)
        sys.exit()
    get_divdata(
        args.timestring,
        args.cstart,
        args.detstart,
        args.savedir,
        cend=args.cend,
        detend=args.detend,
        keep_csv=args.keep_csv,
        drop_dates=~args.keep_dates,
        create_hdf=args.create_hdf,
        save_hdf=args.create_hdf,
    )

