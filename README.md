
# Tinker Automation: Accessible Molecular Simulation

## Overview
This project automates the configuration process for Tinker molecular simulation software, making it easier for users to set up and run simulations. By managing user inputs and configuration files, it streamlines the workflow and reduces manual errors.

## Features
- Loads default simulation parameters from `templateConfig.YAML`.
- Allows users to override defaults via `userConfig.YAML` and command-line arguments.
- Merges all configuration sources, with command-line arguments taking highest priority.
- Saves the final configuration to `userConfig.YAML` for reproducibility.
- Uses structured logging to track program execution and configuration changes.

## How It Works
1. The program starts by loading default values from `templateConfig.YAML`.
2. If `userConfig.YAML` exists, its values override the defaults.
3. Any command-line arguments provided by the user override both YAML files.
4. The merged configuration is saved to `userConfig.YAML` and logged.

## Configuration Files
- `templateConfig.YAML`: Contains default simulation parameters (e.g., box size, ion types, file names).
- `userConfig.YAML`: Stores user-specific overrides and the final configuration used for simulation.

## Example Usage
Run the automation script with optional command-line arguments:

    python utils.py --box.size 77.0 --output_prefix user_protein_final

This will update the configuration and save it to `userConfig.YAML`.

This project streamlines the setup of biomolecular systems for molecular dynamics (MD) simulations using the Tinker software suite. It automates the process of managing user inputs and configuration files, making simulation preparation more accessible and less error-prone.

## Key Information/Process Information
- The workflow begins with a cleaned molecular structure (e.g., a protein from the PDB) and ends with a fully solvated, neutralized system ready for simulation.
- Default simulation parameters are loaded from `templateConfig.YAML`.
- User-specific overrides are read from `userConfig.YAML` and command-line arguments, with CLI arguments taking the highest priority.
- The merged configuration is saved to `userConfig.YAML` for reproducibility and future use.
- The configuration files include important parameters such as box size, ion types, salt concentration, and file names for input/output.
- The automation supports standard Tinker preparation steps, including structure conversion, keyfile creation, box building, solvation, ion addition, and final inspection.
- The parameter file (e.g., amoebabio18.prm) is required for force field settings and correct ion type numbers.

## Logging
The program uses Python's logging module to record:
- Program start
- Loading and saving of YAML files
- Completion of user config parsing
- The final active configuration
