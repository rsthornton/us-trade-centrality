#!/bin/sh
# Fetch the CFS 2012 public use microdata file (free Census download).
# Already run 2026-06-10; rerun only if the local copy is lost.
# Lands at the path configs/cfs_2012.yaml expects.

set -e

DEST="/Users/home/Desktop/halcyonic-projects/archive/reference"
URL="https://www2.census.gov/programs-surveys/cfs/datasets/2012/2012-pums-files/cfs-2012-pumf-csv.zip"

cd "$DEST"
curl -L -o cfs-2012-pumf-csv.zip "$URL"
unzip -o cfs-2012-pumf-csv.zip
ls -lh cfs_2012_pumf_csv.txt
