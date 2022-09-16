"""
Given two namelist paths compares their values and reports differences and missing sections/variables
"""

import argparse
import f90nml
import os
import sys

from loguru import logger

def check_missing_elements(var1, var2):
    return set(var2).difference(var1)

if __name__ == "__main__":

    # Logger
    logger.remove()
    logger.add(
        sys.stderr,
        filter={"": "WARNING", "esm_tests": "DEBUG"},
        format="<level>{message}</level>",
    )
    logger.level("WARNING", color="<white>")
    logger = logger.opt(ansi=True)

    logger.info("")
    logger.info("Welcome to NML-Copare!")
    logger.info("======================")
    logger.info("")

    # Parsing
    parser = argparse.ArgumentParser(description="Compare 2 namelists with different formats")
    parser.add_argument('nml1', default=None)
    parser.add_argument('nml2', default=None)
    parser.add_argument(
        "-i",
        "--ignore-rep",
        help="Ignore repeated sections in a namelist",
        action="store_true",
        default=False,
    )

    args = vars(parser.parse_args())

    # Load directories
    nml1_path = args['nml1']
    nml2_path = args['nml2']
    ignore_rep = args["ignore_rep"]

    # Load namelists
    nml_paths = [nml1_path, nml2_path]
    nmls = []
    sections = []
    for path in nml_paths:
        if os.path.isfile(path):
            nml = (f90nml.read(path))
            nmls.append(nml)
            sections.append([section for section in nml])
        else:
            logger.error(f"{path} is not a file.")
            sys.exit(1)

    # Are there any sections repeated?
    rep_sect = []
    for nml in sections:
        for sect in nml:
            if nml.count(sect)>1:
                rep_sect.append(sect)
    rep_sect = list(set(rep_sect))
    if rep_sect and not ignore_rep:
        logger.warning(
            "These namelists contain repeated sections and cannot be compared. Use the "
            "<red>--ignore-rep</red> or simply <red>-i</red> flags for ignoring this "
            "sections and be able to compare the rest.\n\nRepeated sections:"
        )
        for sect in rep_sect:
            logger.warning(f"\t- {sect}")
        sys.exit(1)
    elif rep_sect:
        new_nmls = []
        # Remove this sections from the namelists
        for nml in nmls:
            for sect in rep_sect:
                c = 0
                while f"_grp_{sect}_{c}" in nml:
                    del nml[f"_grp_{sect}_{c}"]
                    c += 1
            new_nmls.append(nml)
        logger.warning("Some sections are repeated in the namelists and won't be compared:")
        for sect in rep_sect:
            logger.warning(f"\t- {sect}")
        logger.warning("")
        nmls = new_nmls
    # Removed repeated sections
    new_sections = []
    for nml in sections:
        for sect in rep_sect:
            nml = [value for value in nml if value != sect]
        new_sections.append(nml)
    sections = new_sections

    # Check missing sections
    missing_sec_in_1 = check_missing_elements(sections[0], sections[1])
    missing_sec_in_2 = check_missing_elements(sections[1], sections[0])

    different_namelists = False
    if missing_sec_in_1:
        logger.warning(f"<red>{nml1_path}</red> is missing the following sections:")
        for sect in missing_sec_in_1:
            logger.warning(f"\t- <red>{sect}</red>")
        logger.warning("")
        different_namelists = True
    if missing_sec_in_2:
        logger.warning(f"<red>{nml2_path}</red> is missing the following sections:")
        for sect in missing_sec_in_2:
            logger.warning(f"\t- <red>{sect}</red>")
        logger.warning("")
        different_namelists = True

    # Check missing variables
    missing_var_in_1 = {}
    for section in sections[0]:
        if section not in missing_sec_in_2:
            missing = check_missing_elements(nmls[0][section], nmls[1][section])
            if missing:
                missing_var_in_1[section] = missing
    if missing_var_in_1:
        different_namelists = True
        logger.warning(f"<red>{nml1_path}</red> is missing the following vars:")
        for key, value in missing_var_in_1.items():
            logger.warning(f"\t{key}:")
            for var in value:
                logger.warning(f"\t\t- <red>{var}</red>")
        logger.warning("")

    missing_var_in_2 = {}
    for section in sections[1]:
        if section not in missing_sec_in_1:
            missing = check_missing_elements(nmls[1][section], nmls[0][section])
            if missing:
                missing_var_in_2[section] = missing
    if missing_var_in_2:
        different_namelists = True
        logger.warning(f"<red>{nml2_path}</red> is missing the following vars:")
        for key, value in missing_var_in_2.items():
            logger.warning(f"\t{key}:")
            for var in value:
                logger.warning(f"\t\t- <red>{var}</red>")
        logger.warning("")

    # Compare variables here
    common_namelist = [{}, {}]
    for section in sections[0]:
        if section in sections[1]:
            for var in nmls[0][section]:
                if var in nmls[1][section]:
                    if nmls[0][section][var]!=nmls[1][section][var]:
                        logger.warning(f"\t{section}.<red>{var}</red> differ!\t{nmls[0][section][var]}\t{nmls[1][section][var]}")
                        different_namelists = True


    # Notify general differences
    if different_namelists:
        logger.error("Namelists are different!")
    else:
        logger.warning("Namelists are identical")
