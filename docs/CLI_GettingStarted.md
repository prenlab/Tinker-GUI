# Getting Started with CLI

Prepare Tinker XYZ and KEY file for MD simulations from PDB files.

## Prerequisites

1. Python 3
2. PyYAML

## Usage

1. First clone this repo.

1. Print help messages:
    ```
    python Tinker-GUI/cli.py -h
    ```
    A detailed instruction of how to pass in command line arguments will be shown. Command line arguments has the highest precedence.
    ```
    usage: cli.py [-h] [-c CONFIG] [--generate-yaml-template] [--tinker_path TINKER_PATH] [--amoeba_prm AMOEBA_PRM] [--output_prefix OUTPUT_PREFIX] [--solutes-protein SOLUTES__PROTEIN [SOLUTES__PROTEIN ...]]
                [--solutes-nucleic_acid SOLUTES__NUCLEIC_ACID [SOLUTES__NUCLEIC_ACID ...]] [--solvent-name SOLVENT__NAME] [--ions-neutralizers IONS__NEUTRALIZERS [IONS__NEUTRALIZERS ...]] [--ions-salts-names IONS__SALTS__NAMES [IONS__SALTS__NAMES ...]]
                [--ions-salts-concentrations IONS__SALTS__CONCENTRATIONS [IONS__SALTS__CONCENTRATIONS ...]] [--box-type BOX__TYPE] [--box-buffer BOX__BUFFER]

    Tinker-GUI CLI Config Manager

    optional arguments:
    -h, --help            show this help message and exit
    -c CONFIG, --config CONFIG
                            Path to the YAML config file.
    --generate-yaml-template
                            Generate a sample YAML config and exit.
    --tinker_path TINKER_PATH
                            Path to the Tinker executables. (Default: /path/to/tinker/bin)
    --amoeba_prm AMOEBA_PRM
                            Path to the AMOEBA parameter file. (Default: /path/to/amoeba.prm)
    --output_prefix OUTPUT_PREFIX
                            Prefix for output files. (Default: my_system)
    --solutes-protein SOLUTES__PROTEIN [SOLUTES__PROTEIN ...]
                            List of protein PDB files. (Default: /path/to/my_protein.pdb /path/to/my_protein_2.pdb)
    --solutes-nucleic_acid SOLUTES__NUCLEIC_ACID [SOLUTES__NUCLEIC_ACID ...]
                            List of nucleic acid PDB files. (Default: /path/to/my_dna.pdb)
    --solvent-name SOLVENT__NAME
                            Solvent name. (Default: water)
    --ions-neutralizers IONS__NEUTRALIZERS [IONS__NEUTRALIZERS ...]
                            List of neutralizing ions. (Default: Na+ Cl-)
    --ions-salts-names IONS__SALTS__NAMES [IONS__SALTS__NAMES ...]
                            List of salt names. (Default: K+ Cl-)
    --ions-salts-concentrations IONS__SALTS__CONCENTRATIONS [IONS__SALTS__CONCENTRATIONS ...]
                            List of respective concentrations in mol/L. (Default: 0.15 0.15)
    --box-type BOX__TYPE  Box type. (Default: cube)
    --box-buffer BOX__BUFFER
                            Box buffer size in Å. (Default: 12.0)
    ```

1. You can also use a YAML file to pass in arguments. Run this to get a template YAML file.
    ```
    python Tinker-GUI/cli.py --generate-yaml-template
    ```
    It will generate a template YAML named `sample_config.yaml` like this:
    ```
    tinker_path: /path/to/tinker/bin
    amoeba_prm: /path/to/amoeba.prm
    output_prefix: my_system
    solutes:
        protein:
        - /path/to/my_protein.pdb
        - /path/to/my_protein_2.pdb
        nucleic_acid:
        - /path/to/my_dna.pdb
    solvent:
        name: water
        density: 1.0
    ions:
        neutralizers:
        - Na+
        - Cl-
        salts:
            names:
            - K+
            - Cl-
            concentrations:
            - 0.15
            - 0.15
    box:
        type: cube
        buffer: 12.0
    ```
    You can then modify it based on your case then run the program this way:
    ```
    python Tinker-GUI/cli.py -c sample_config.yaml
    ```

1. The final output will look like below. The first two files are Tinker XYZ and KEY file for the prepared MD system. All intermediate files and log will be in `temp/`.
    ```
    my_system_final.key 
    my_system_final.xyz 
    sample_config.yaml 
    temp
    ├── 1fjs_pro.pdb
    ├── 1fjs_pro.seq
    ├── 1fjs_pro.xyz
    ├── config.yaml
    ├── log
    ├── my_system_aligned_solvated_neutralized_K_added_Cl_added.xyz
    ├── my_system_aligned_solvated_neutralized_K_added.xyz
    ├── my_system_aligned_solvated_neutralized.xyz
    ├── my_system_aligned_solvated.xyz
    ├── my_system_aligned.xyz
    ├── my_system.key
    ├── my_system.xyz
    ├── water_cube_120A_trimmed.xyz
    └── water_cube_120A.xyz
    ```