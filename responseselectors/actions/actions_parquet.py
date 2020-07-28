"""parquet related functions"""
import os
import logging
import pandas as pd

logger = logging.getLogger(__name__)


def convert_bytes(num):
    """
    this function will convert bytes to MB.... GB... etc
    """
    for x in ["bytes", "KB", "MB", "GB", "TB"]:
        if num < 1024.0:
            break
        num /= 1024.0

    return f"{num:.1f} {x}"


def file_size(file_path):
    """
    this function will return the file size
    """
    if os.path.isfile(file_path):
        file_info = os.stat(file_path)
        return convert_bytes(file_info.st_size)

    return f"File does not exist: {file_path}"


def persist_df(df, local_dir, fname, verbose=1):
    """Writes a pandas data-frame to parquet.gzip, using fastparquet

    CONVENTIONS:
    (-) A parquet file will be written using engine='fastparquet' & compression='gzip
    (-) All column names will be converted into strings prior to writing of the file.
    (-) MultiIndex is not allowed, because 'fastparquet' does not support it

    # Inputs
        df: a pandas data-frame, with a single index
        local_dir: location to write fname
        fname: name of the file to write, recommended is <---->.parquet.gzip
        verbose: 0 = silent ; 1 = prints feedback

    # Returns
        True if sucessfull, else False
    """
    if verbose > 0:
        logger.info("---------------------------------------------------------------")

    if isinstance(df.index, pd.MultiIndex):
        raise ValueError("df has a MultiIndex. This is not supported by fastparquet")

    # parquet requires strings as column names
    df.columns = [str(c) for c in df.columns]

    # write it to local disk
    local_fname = f"{local_dir}/{fname}"
    df.to_parquet(local_fname, engine="fastparquet", compression="gzip")
    if verbose > 0:
        logger.info(
            "Completed writing local file (%s): %s", file_size(local_fname), local_fname
        )
        logger.info("---------------------------------------------------------------")
    return True


def read_df(local_dir, fname, verbose=1):
    """Reads a pandas data-frame from parquet.gzip, using fastparquet

    CONVENTIONS:
    (-) See persist_df for writing parquet files
    (-) The parquet file must have been written with engine='fastparquet' &
        compression='gzip

    # Inputs
        local_dir: location of fname
        fname: the parquet.gzip file to read
        verbose: 0 = silent ; 1 = prints feedback

    # Returns
        a pandas dataframe
    """
    if verbose > 0:
        logger.info("---------------------------------------------------------------")

    local_fname = f"{local_dir}/{fname}"
    if verbose > 0:
        logger.info("Reading: %s (%s)", local_fname, file_size(local_fname))

    df = pd.read_parquet(local_fname, engine="fastparquet")

    if verbose > 0:
        logger.info("shape of dataframe = %s", df.shape)
        logger.info("---------------------------------------------------------------")

    return df
