import argparse
import collections.abc
import json
import yaml
import sys
from typing import Any, Dict, List, Optional
import os
import logging
import subprocess
from collections import OrderedDict

logger = logging.getLogger(__name__)

def init_logger(log_file=None, level=logging.INFO):
    root_logger = logging.getLogger()
    for h in root_logger.handlers:
        root_logger.removeHandler(h)
    basic_fmt = "[%(asctime)s] %(levelname)-8s | %(filename)-12s:%(lineno)-4d | %(message)s"
    logging.basicConfig(
        filename=None, filemode="a", format=basic_fmt, level=level,
    )
    if log_file:
        root_logger = logging.getLogger()
        fhlr = logging.FileHandler(log_file)
        formatter = logging.Formatter(basic_fmt)
        fhlr.setFormatter(formatter)
        root_logger.addHandler(fhlr)


def recursive_update(d, u):
    """recursivly update a dictionary
    https://stackoverflow.com/questions/3232943/update-value-of-a-nested-dictionary-of-varying-depth

    Args:
        d (dict): dictionary being updated
        u (dict): dictionary storing updates

    Returns:
        dict: updated dictionary
    """
    for k, v in u.items():
        if isinstance(v, collections.abc.Mapping):
            d[k] = recursive_update(d.get(k, {}), v)
        else:
            d[k] = v
    return d


class ConfigManager:
    """Singleton General Config Manager for Tinker GUI/CLI applications.
    `CONFIG_DEFINITION` serves as the single source of truth for all configuration parameters.
    It defines each parameter's name, default value, type, and help description.
    """

    CONFIG_DEFINITION = [
        {'name': 'tinker_path', 'default': '/path/to/tinker/bin', 'type': str, 'help': 'Path to the Tinker executables.'},
        {'name': 'amoeba_prm', 'default': '/path/to/amoeba.prm', 'type': str, 'help': 'Path to the AMOEBA parameter file.'},
        {'name': 'output_prefix', 'default': 'my_system', 'type': str, 'help': 'Prefix for output files.'},

        {'name': 'solutes.protein', 'default': ['/path/to/my_protein.pdb', '/path/to/my_protein_2.pdb'], 'type': list, 'help': 'List of protein PDB files.'},
        {'name': 'solutes.nucleic_acid', 'default': ['/path/to/my_dna.pdb'], 'type': list, 'help': 'List of nucleic acid PDB files.'},
        # {'name': 'solutes.ligand', 'default': ['/path/to/my_ligand.sdf'], 'type': list, 'help': 'List of ligand SDF files.'},

        {'name': 'solvent.name', 'default': 'water', 'type': str, 'help': 'Solvent name.'},
        # {'name': 'solvent.density', 'default': 1.000, 'type': float, 'help': 'Solvent density in g/cm^3.'},

        {'name': 'ions.neutralizers', 'default': ['Na+', 'Cl-'], 'type': list, 'help': 'List of neutralizing ions.'},
        # {'name': 'ions.salts', 'default': {'K': 0.15, 'Cl': 0.15}, 'type': dict, 'help': 'Concentration of salts in mol/L.'},
        {'name': 'ions.salts.names', 'default': ['K+', 'Cl-'], 'type': list, 'help': 'List of salt names.'},
        {'name': 'ions.salts.concentrations', 'default': [0.15, 0.15], 'type': list, 'help': 'List of respective concentrations in mol/L.'},

        {'name': 'box.type', 'default': 'cuboid', 'type': str, 'help': 'Box type.'},
        {'name': 'box.buffer', 'default': 12.0, 'type': float, 'help': 'Box buffer size in Å.'},
    ]

    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        # Only initialize once due to singleton pattern
        if ConfigManager._initialized:
            return
        self.config = argparse.Namespace()
        self.parser = argparse.ArgumentParser(description="Tinker-GUI CLI Config Manager")
        self._add_arguments()
        ConfigManager._initialized = True

    def _add_arguments(self):
        """Add command-line arguments based on CONFIG_DEFINITION."""
        self.parser.add_argument(
            '-c', '--config', 
            type=str, 
            help='Path to the YAML config file.'
        )
        self.parser.add_argument(
            '--generate-yaml-template', 
            action='store_true', 
            help='Generate a sample YAML config and exit.'
        )

        for param in ConfigManager.CONFIG_DEFINITION:
            # Allow hierarchical names using dot-paths; use dashes on CLI and map to safe dest
            path_name = param['name']
            option = f"--{path_name.replace('.', '-')}"
            dest = path_name.replace('.', '__')
            if param['type'] == list:
                self.parser.add_argument(
                    option,
                    dest=dest,
                    type=type(param['default'][0]) if param['default'] else str,
                    nargs='+',
                    default=None, # Use None to detect if user provided it
                    help=param['help'] + f" (Default: {' '.join(map(str, param['default']))})"
                )
            elif param['type'] == dict:
                self.parser.add_argument(
                    option,
                    dest=dest,
                    type=json.loads,
                    default=None, # Use None to detect if user provided it
                    help=param['help'] + f" (Default: '{json.dumps(param['default'])}')"
                )
            else:
                self.parser.add_argument(
                    option,
                    dest=dest,
                    type=param['type'],
                    default=None, # Use None to detect if user provided it
                    help=param['help'] + f" (Default: {param['default']})"
                )

    def _check_arguments_validity(self):
        """Check validity of certain arguments after parsing."""
        has_solute = False
        for param in ConfigManager.CONFIG_DEFINITION:
            # check tinker_path, amoeba_prm must be different from default and exist
            if param['name'] in ['tinker_path', 'amoeba_prm']:
                value = getattr(self.config, param['name'].replace('.', '__'))
                if value == param['default']:
                    logger.error(f"Configuration parameter '{param['name']}' must be set to a valid path, not the default value.")
                    sys.exit(1)
                if not os.path.exists(value):
                    logger.error(f"Path specified for '{param['name']}' does not exist: {value}")
                    sys.exit(1)
            # check at least one of protein/nucleic_acid/ligand must be provided, different from default, and exist
            if param['name'].startswith('solutes.'):  
                try:                  
                    value = getattr(self.config.solutes, param['name'].split('.')[1])
                    if value and value != param['default']:
                        for fpath in value:
                            if not os.path.exists(fpath):
                                logger.error(f"Solute file specified for '{param['name']}' does not exist: {fpath}")
                                sys.exit(1)
                        has_solute = True
                except AttributeError:
                    continue
        if not has_solute:
            logger.error("At least one valid solute (protein, nucleic acid, or ligand) must be provided.")
            sys.exit(1)


    def _generate_yaml_template(self):
        """Generate a sample YAML configuration file based on CONFIG_DEFINITION."""
        # Use OrderedDict to maintain the order of parameters
        template_dict: Dict[str, Any] = OrderedDict()
        for param in ConfigManager.CONFIG_DEFINITION:
            # Support nested keys with dot-paths
            self._set_by_path(template_dict, param['name'].split('.'), param['default'])

        yaml_string = yaml.dump(dict(template_dict), sort_keys=False)
        if os.path.exists("sample_config.yaml"):
            logger.error("sample_config.yaml already exists. Please remove it before generating a new template.")
            return
        else:
            with open("sample_config.yaml", "w") as f:
                f.write(yaml_string)

    # ---------- Helpers for hierarchical configuration ----------
    def _set_by_path(self, d: Dict[str, Any], path: List[str], value: Any) -> None:
        cur = d
        for key in path[:-1]:
            if key not in cur or not isinstance(cur[key], (dict, OrderedDict)):
                cur[key] = {}
            cur = cur[key]
        cur[path[-1]] = value

    def _remove_by_path(self, d: Dict[str, Any], path: List[str]) -> None:
        cur = d
        for key in path[:-1]:
            if key not in cur or not isinstance(cur[key], (dict, OrderedDict)):
                return
            cur = cur[key]
        if path[-1] in cur:
            del cur[path[-1]]

    def _deep_merge(self, base: Dict[str, Any], inc: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively merge inc into base and return a new dict."""
        if not isinstance(base, (dict, OrderedDict)):
            base = {}
        if not isinstance(inc, (dict, OrderedDict)):
            return dict(base)
        result = dict()
        all_keys = list(base.keys()) + list(inc.keys())
        for k in sorted(set(all_keys), key=lambda x: all_keys.index(x)):
            bv = base.get(k)
            iv = inc.get(k)
            if isinstance(bv, (dict, OrderedDict)) and isinstance(iv, (dict, OrderedDict)):
                result[k] = self._deep_merge(bv, iv)
            elif iv is not None:
                result[k] = iv
            else:
                result[k] = bv
        return result

    def _to_namespace(self, data: Dict[str, Any]) -> argparse.Namespace:
        """Convert nested dicts into nested Namespaces for attribute access."""
        if not isinstance(data, (dict, OrderedDict)):
            return argparse.Namespace()
        result = OrderedDict()
        for k, v in data.items():
            if isinstance(v, (dict, OrderedDict)):
                result[k] = self._to_namespace(v)
            else:
                result[k] = v
        return argparse.Namespace(**result)

    def _to_plain_dict(self, ns_or_dict: Any) -> Dict[str, Any]:
        """Convert Namespace (possibly nested) to plain dict recursively."""
        if isinstance(ns_or_dict, argparse.Namespace):
            ns_or_dict = vars(ns_or_dict)
        if not isinstance(ns_or_dict, (dict, OrderedDict)):
            return {}
        out = dict()
        for k, v in ns_or_dict.items():
            if isinstance(v, argparse.Namespace) or isinstance(v, (dict, OrderedDict)):
                out[k] = self._to_plain_dict(v)
            else:
                out[k] = v
        return out
    
    # ---------- Public Methods ----------
    def parse_args(self):
        """Parse command-line arguments, load YAML config, and merge them with defaults.
        Priority: Command-line > YAML file > Defaults"""
        # Build defaults as possibly nested dict based on dotted names
        defaults = OrderedDict()
        for param in ConfigManager.CONFIG_DEFINITION:
            self._set_by_path(defaults, param['name'].split('.'), param['default'])

        cmd_args = self.parser.parse_args()

        # Check for special flags first
        if cmd_args.generate_yaml_template:
            self._generate_yaml_template()
            sys.exit(0)

        yaml_config = OrderedDict()
        if cmd_args.config:
            with open(cmd_args.config, 'r') as f:
                yaml_config = yaml.safe_load(f) or {}

        # Start with defaults and deep-merge YAML config values
        final_config = self._deep_merge(defaults, yaml_config)
        # Finally, override with command-line arguments if provided
        for param in ConfigManager.CONFIG_DEFINITION:
            path = param['name']
            dest = path.replace('.', '__')
            cmd_value = getattr(cmd_args, dest, None)
            if cmd_value is not None:
                self._set_by_path(final_config, path.split('.'), cmd_value)
        # Remove solutes entries that were not provided via CLI or YAML thus exactly the same as examplary defaults
        for param in ConfigManager.CONFIG_DEFINITION:
            if param['name'].startswith('solutes.'):
                path = param['name']
                default_value = param['default']
                final_value = final_config
                for key in path.split('.'):
                    final_value = final_value.get(key, None)
                    if final_value is None:
                        break
                if final_value == default_value:
                    self._remove_by_path(final_config, path.split('.'))

        recursive_update(self.config.__dict__, self._to_namespace(final_config).__dict__)
        self._check_arguments_validity()
        logger.info(f"Final Configuration: \n{yaml.dump(final_config, sort_keys=False)}")
        
    def get_config(self) -> argparse.Namespace:
        """Return the current configuration as an argparse.Namespace object."""
        return self.config

    def save_yaml(self, path: str):
        data = self._to_plain_dict(self.config)
        with open(path, 'w') as f:
            yaml.safe_dump(data, f, sort_keys=False)
        logger.info(f"Configuration saved to {path}")


class TinkerKeyFile:
    """Class for Tinker key files."""
    def __init__(self, key_file_path: str):
        self.key_file_path = key_file_path
        self.latest_path = key_file_path
        if not os.path.isfile(self.key_file_path):
            self.keys = []
            logger.info(f"Key file {self.key_file_path} does not exist. Starting with empty keys.")
        else:
            self.keys = self._load_key_file()
            logger.info(f"Loaded key file from {self.key_file_path}.")

    def _load_key_file(self):
        """Load and parse the Tinker key file."""
        keys = []
        with open(self.key_file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    keys.append(line.split())
        return keys
    
    def has_key(self, key: str) -> bool:
        """Check if a parameter key exists."""
        for k in self.keys:
            if k[0] == key:
                return True
        return False

    def get_key(self, key: str):
        """Get a parameter value by key."""
        for k in self.keys:
            if k[0] == key:
                return k
        return []

    def set_key(self, key: str, value: str):
        """Set a parameter value by key."""
        for k in self.keys:
            if k[0] == key:
                logger.info(f"Updating key in key file: `{key} {value}`")
                k[1:] = value.strip().split()
                break
        else:
            logger.info(f"Adding new key to key file: `{key} {value}`")
            self.keys.append([key] + value.strip().split())

    def save_key_file(self, output_path: Optional[str] = None):
        """Save the current keys to a key file."""
        # if output_path is None, create a new file with untaken numbered suffix
        if output_path is None:
            if not os.path.exists(self.key_file_path):
                path = self.key_file_path
            else:
                base_path = self.key_file_path[:-4]  # remove .key
                i = 1
                while os.path.exists(f"{base_path}_{i}.key"):
                    i += 1
                path = f"{base_path}_{i}.key"
        else:
            path = output_path

        with open(path, 'w') as f:
            for key in self.keys:
                f.write(' '.join(key) + "\n")
        logger.info(f"Key file saved to {path}")
        
        self.latest_path = path
        

class AtomTypeFinder:
    """Class for finding atom types from Tinker parameter files."""
    def __init__(self, prm_file_path: str):
        self.prm_file_path = prm_file_path
        self.atom_defs = self._load_atom_definitions()
        self.multipole_defs = self._load_multipole_definitions()

    def _load_atom_definitions(self):
        """Load and parse atom definitions from the Tinker parameter file."""
        atom_defs = []
        with open(self.prm_file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith('atom'):
                    atom_defs.append(line)
        return atom_defs
    
    def _load_multipole_definitions(self):
        """Load and parse multipole definitions from the Tinker parameter file."""
        multipole_defs = []
        with open(self.prm_file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith('multipole'):
                    multipole_defs.append(line)
        return multipole_defs

    def find_atom_type(self, description):
        """Find the atom type based on description."""
        for atom_def in self.atom_defs:
            parts = atom_def.split()
            if len(parts) >= 4:
                atom_type = parts[1]
                # atomic_number = parts[5]
                if description in atom_def:
                    return atom_type
        return 0
    
    def find_atom_charge(self, atom_type):
        """Find the atom charge based on atom type."""
        for multipole_def in self.multipole_defs:
            parts = multipole_def.split()
            m_type = parts[1]
            charge = parts[-1]
            if m_type == atom_type:
                return float(charge)
        return None
    

def make_readable_ids(ids, fill_gaps_under=1):
    ids = sorted(ids)
    readable_ids = []
    start = ids[0]
    last = ids[0]
    for i in ids[1:]:
        if i - last <= fill_gaps_under:
            last = i
            continue
        if last == start:
            readable_ids.append(last)
        else:
            readable_ids.append([start, last])
        start = i
        last = i
    # append the last one
    if last == start:
        readable_ids.append(last)
    else:
        readable_ids.append([start, last])
    return readable_ids
