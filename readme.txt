Tinker Automation: Accessible Molecular Simulation
===============================================

Overview
--------
This project automates the configuration process for Tinker molecular simulation software, making it easier for users to set up and run simulations. By managing user inputs and configuration files, it streamlines the workflow and reduces manual errors.

Features
--------
- Loads default simulation parameters from `templateConfig.YAML`.
- Allows users to override defaults via `userConfig.YAML` and command-line arguments.
- Merges all configuration sources, with command-line arguments taking highest priority.
- Saves the final configuration to `userConfig.YAML` for reproducibility.
- Uses structured logging to track program execution and configuration changes.

How It Works
------------
1. The program starts by loading default values from `templateConfig.YAML`.
2. If `userConfig.YAML` exists, its values override the defaults.
3. Any command-line arguments provided by the user override both YAML files.
4. The merged configuration is saved to `userConfig.YAML` and logged.

Configuration Files
------------------
- `templateConfig.YAML`: Contains default simulation parameters (e.g., box size, ion types, file names).
- `userConfig.YAML`: Stores user-specific overrides and the final configuration used for simulation.

Example Usage
-------------
Run the automation script with optional command-line arguments:

    python utils.py --box.size 77.0 --output_prefix user_protein_final

This will update the configuration and save it to `userConfig.YAML`.

Logging
-------
The program uses Python's logging module to record:
- Program start
- Loading and saving of YAML files
- Completion of user config parsing
- The final active configuration

Purpose
-------
This tool is designed to make molecular simulation with Tinker more accessible by automating and validating user inputs, reducing manual editing of configuration files, and providing clear feedback through logging.

Contact
-------
For questions or contributions, please contact the project maintainer.
