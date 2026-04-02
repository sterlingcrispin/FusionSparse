# Corpus

`FusionSparse` uses Autodesk's official `FusionAPIReference` repository as a development-time input for parsing, metadata generation, and release diffs.

## Expected location

The corpus lives at:

`corpus/FusionAPIReference`

This repository now tracks the Autodesk corpus as a git submodule pinned by the parent repo.

## Clone and update

Fresh clone:

`git clone --recurse-submodules https://github.com/sterlingcrispin/FusionSparse.git`

If the repo is already cloned:

`git submodule update --init --recursive`

To refresh the Autodesk corpus to the latest `main` when intentionally updating the source snapshot:

`git submodule update --remote corpus/FusionAPIReference`

The parent repo should then commit the updated gitlink and refreshed generated artifacts together.

## Required directories

The corpus loader verifies:

- `Fusion_API_Python_Reference/defs`
- `Fusion_API_CPP_Reference/include`
- `Fusion_API_Documentation/files`

It also records optional sources when present:

- `processed_docs/md`
- `tools/generate_index.py`
- `llms.txt`

## Lockfile

`corpus/corpus.lock.json` is generated from the loader and records the exact corpus path, commit, and file counts used by the current build.
