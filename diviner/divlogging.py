import logging

formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - " "%(message)s")

def setup_logger():
    logger = logging.getLogger(name="diviner")
    logger.setLevel(logging.DEBUG)
    logfname = "divcalib_verif_" + self.run_name + ".log"
    fh = logging.FileHandler(logfname)
    fh.setLevel(logging.DEBUG)
    ch = logging.StreamHandler(stream=None)
    ch.setLevel(logging.INFO)

    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    logger.addHandler(fh)
    logger.addHandler(ch)
