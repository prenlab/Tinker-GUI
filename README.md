
# Tinker Automation: Accessible Molecular Simulation

## Overview
This project automates the configuration process for Tinker molecular simulation software, making it easier for users to set up and run simulations. By managing user inputs and configuration files, it streamlines the workflow and reduces manual errors.

## What it does
1. Convert common structure file formats (PDB, SDF, etc) to Tinker XYZ;
1. Standardize the orientation of the structures;
1. Soak it into a proper solvent box;
1. Add ions for neutralization and proper salt concentrations.
1. Output:
    1. a Tinker XYZ file;
    1. a Tinker KEY file.

## Current Status

### Ready to Use
1. Command line interface streamlining various Tinker programs for preparation of input files for MD simulation with Tinker.

### Ongoing Development
1. Improve the CLI module;
1. GUI;
1. Python-based Conversion of Tinker XYZ/ARC from/to PDB;
1. Web Interface;
1. Support systems with membranes;
1. Detection and repair of minor formating errors in input PDB file;


## Getting Started

[CLI Getting Started](docs/CLI_GettingStarted.md)

