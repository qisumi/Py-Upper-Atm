# Third-Party Notices

UpperAtmPy wraps and packages several atmospheric and space-environment model
implementations that originate outside this project. The project-level MIT
license applies only to original UpperAtmPy code, documentation, tests,
examples, build files, and wrapper glue. It does not relicense third-party
model source code, model data, or archived reference materials.

## NRLMSIS 2.0

Files under `src/model/pymsis2/` include NRLMSIS 2.0 model source code and
supporting data. The upstream `readme.txt` and source headers state that the
MSIS software is property of the United States Government as represented by
the Secretary of the Navy, is covered by U.S. Patent Number 10,641,925, and is
licensed for academic, non-commercial purposes only.

Users must review and comply with the full upstream terms in
`src/model/pymsis2/readme.txt` and the headers of the NRLMSIS 2.0 source files.

## CCMC ModelWeb Archive Materials

The `TODO/` directory contains model source code, data files, and reference
materials collected from the CCMC ModelWeb Catalogue and Archive. Many of
these files come from universities, government agencies, or individual model
authors and may have their own notices or no explicit license statement.

Files ported from `TODO/` into `src/model/` retain their upstream provenance.
Files copied from `TODO/` into `data/` likewise remain upstream model data and
are not relicensed by UpperAtmPy.
Before redistributing a derived package or using a model in a commercial or
restricted setting, review the notices in the relevant model directory and
confirm that the intended use is permitted.

## Project Contributions

Unless a file states otherwise, new UpperAtmPy wrapper code, tests, examples,
documentation, and build-system changes contributed directly to this repository
are available under the MIT License in `LICENSE`.
