#!/usr/bin/env python3
import pathlib
import argparse
import sys
from dataclasses import dataclass


FASTQ_SUFFIXES = {"fastq", "fastq.gz"}
FAST5_SUFFIXES = {"fast5"}

@dataclass
class ValidationResult:
    success: bool
    reason: str


def parse_args():

    parser = argparse.ArgumentParser()
    parser.add_argument("DIRECTORY", help="Directory to check - either run directory or directory with runs(requires --datadir flag)")
    parser.add_argument("--datadir",action="store_true", help="treat DIRECTORY as directory with multiple runs to test")
    parser.add_argument("--ignore",type=str,dest="ignore", default="",help="comma-separated list of directories to ignore, requires --datadir")
    
    
    args = parser.parse_args()
    if args.ignore and (len(args.ignore) > 0):
        if not args.datadir:
            print("--ignore requires --datadir argument, exiting now", file=sys.stderr)
            sys.exit(1)
    return args


def validate_run_directory(dirname:str)->ValidationResult:
    bp  = pathlib.Path(dirname)
    if not bp.exists():
        return ValidationResult(False, "run directory does not exist")
    
    if not bp.is_dir():
        return ValidationResult(False, f"path {dirname} is not a directory!")
    
    samples = list(bp.glob("*"))
    if not any(map(lambda x: x.is_dir(), samples)):
        return ValidationResult(False, f"did not find any sample directories in {dirname}")
    for sample in filter(lambda x: x.is_dir(), samples):

        subruns = list(filter(lambda x: x.is_dir(), sample.glob("*"))) # no idea wtf are these subruns, TODO: figure out
        if len(subruns) == 0:
            return ValidationResult(False, f"did not find any subrun directories in {sample}")

        for subrun in subruns:
            all_stuff_in_subrun = list(subrun.glob("*"))

            # check that fastq_pass and fast5_pass exist
            if not ("fastq_pass" in map(lambda x: x.name, filter(lambda y: y.is_dir(), all_stuff_in_subrun))):
                return ValidationResult(False, f"did not find fastq_pass in {subrun}")
            
            if not ("fast5_pass" in map(lambda x: x.name, filter(lambda y: y.is_dir(), all_stuff_in_subrun))):
                return ValidationResult(False, f"did not find fast5_pass in {subrun}")
            

            if len ((subrun / "fastq_pass").glob("*.fastq*")) == 0:
                return ValidationResult(False, f"Did not find any fastq files in {subrun / 'fastq_pass' }")
            

            if len ((subrun / "fast5_pass").glob("*.fast5")) == 0:
                return ValidationResult(False, f"Did not find any fast5 files in {subrun / 'fast5_pass' }")
            


            fastq_basenames = set(map(lambda x: x.name.split(".")[0], (subrun / "fastq_pass").glob("*.fastq*")))

            fast5_basenames = set(map(lambda x: x.name.split(".")[0], (subrun / "fast5_pass").glob("*.fast5")))

            if fastq_basenames != fast5_basenames:
                return ValidationResult(False, f"files in fastq_pass and fast5_pass in {subrun} did not match ")



    return ValidationResult(True, "")
        
    


if __name__ == "__main__":
    args = parse_args()
    if args.datadir:
        if not pathlib.Path(args.DIRECTORY).is_dir():
            print(f"{args.DIRECTORY} is not a directory, exiting now", file=sys.stderr)
            sys.exit(1)
        dirs_to_ignore = set(args.ignore.strip().split(","))
        dirs_to_check = list(filter(lambda x: not (x.name in dirs_to_ignore), pathlib.Path(args.DIRECTORY).glob("*")))
        failed = False
        for d in dirs_to_check:
            vres = validate_run_directory(d)
            if not vres.success:
                print(f"[{d}] error: {vres.reason}", file=sys.stderr)

                failed = True

        if failed:
            sys.exit(1)



        
    else:
        res = validate_run_directory(args.DIRECTORY)
        if not res.success:
            print(f"Failed to validate directory {args.DIRECTORY}: {res.reason}", file=sys.stderr)
            sys.exit(1)




