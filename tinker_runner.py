import os
import logging
import subprocess
from typing import List, Optional


class TinkerRunner:
    def __init__(self, logger: Optional[logging.Logger] = None):
        if logger is None:
            self.logger = logging.getLogger("TinkerRunner")
            if not self.logger.hasHandlers():
                handler = logging.StreamHandler()
                formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
                handler.setFormatter(formatter)
                self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
        else:
            self.logger = logger

    def run(self, command: str, args: List[str], input_data: Optional[str] = None) -> str:
        """Runs a command and returns stdout, passing input_data to stdin if necessary."""
        cmd = [command] + args
        self.logger.info(f"Running: {' '.join(cmd)}")
        try:
            result = subprocess.run(
                cmd,
                input=input_data,
                text=True,
                capture_output=True,
                check=True
            )
            self.logger.info(f"{command} output:\n{result.stdout}")
            return result.stdout
        except subprocess.CalledProcessError as e:
            self.logger.error(f"{command} failed:\n{e.stderr}")
            raise

    def create_keyfile(self, keyfile_name: str, prm_path: str):
        """Create a keyfile for Tinker with forcefield parameter path.

        Behavior:
        - expands user (~) and relative paths to absolute
        - if keyfile_name has no directory, default into prm's directory
        - ensures the parent directory exists
        - writes the file and returns the absolute path on success
        - logs and raises exceptions on failure
        """
        try:
            # Expand prm path and make absolute
            prm_path_expanded = os.path.abspath(os.path.expanduser(prm_path))

            # If keyfile_name has no directory component, default it into the prm's directory
            keyfile_candidate = os.path.expanduser(keyfile_name)
            if os.path.dirname(keyfile_candidate) == '':
                prm_dir = os.path.dirname(prm_path_expanded) or os.getcwd()
                keyfile_path = os.path.join(prm_dir, keyfile_candidate)
            else:
                keyfile_path = keyfile_candidate

            # Make keyfile_path absolute
            keyfile_path = os.path.abspath(keyfile_path)

            # Ensure parent directory exists
            parent = os.path.dirname(keyfile_path)
            if parent and not os.path.exists(parent):
                os.makedirs(parent, exist_ok=True)

            # Write the keyfile
            with open(keyfile_path, 'w') as f:
                f.write(f"parameters {prm_path_expanded}\n")

            self.logger.info(f"Created keyfile '{keyfile_path}' with parameters {prm_path_expanded}")
            return keyfile_path
        except Exception as e:
            self.logger.error(f"Failed to create keyfile '{keyfile_name}': {e}")
            raise

    def pdb_to_xyz(self, pdb: str, key: str):
        """Convert PDB to XYZ using Tinker's pdbxyz."""
        return self.run('pdbxyz', [pdb, '-k', key])

    def align_inertial_frame(self, xyz: str, key: str) -> str:
        """
        Align molecule or box to inertial frame.
        Returns the name of the new file generated (e.g., xyz_2).
        """
        input_data = "18\n"  # Option 18 in xyzedit
        self.run('xyzedit', [xyz, '-k', key], input_data=input_data)
        new_xyz = xyz + "_2"
        self.logger.info(f"Aligned to inertial frame: {new_xyz}")
        return new_xyz

    def build_water_box(self, water_xyz: str, key: str, input_prompts: Optional[str] = None):
        """Run crystal for water box creation."""
        return self.run('crystal', [water_xyz, '-k', key], input_data=input_prompts)

    def soak_protein(self, protein_xyz: str, key: str, solvent_box_xyz: str) -> str:
        """
        Merge solute and solvent using xyzedit option 27.
        solvent_box_xyz is provided at prompt.
        Returns new .xyz output file name.
        """
        # Prepare input: option 27, enter solvent box file, press enter to confirm output
        input_data = f"27\n{solvent_box_xyz}\n\n"
        self.run('xyzedit', [protein_xyz, '-k', key], input_data=input_data)
        new_xyz = protein_xyz + "_3"
        self.logger.info(f"Solvated molecule output: {new_xyz}")
        return new_xyz

    def analyze_charge(self, xyz: str, key: str) -> str:
        """Run analyze program to calculate charge, returns output."""
        return self.run('analyze', [xyz, '-k', key, 'M'])

    def add_ions(self, xyz: str, key: str, ion_type: int, num_ions: int, atom_numbers: List[int]) -> str:
        """
        Use xyzedit option 28 to add ions.
        atom_numbers is a list of solute atom indices.
        ion_type: integer (e.g., 363 = Cl-, 352 = Na+)
        Returns new .xyz output file name.
        """
        atom_nums_str = ' '.join(map(str, atom_numbers))
        # Create input: option 28, atom numbers, enter, ion type and #, enter, enter to finish, extra enters as needed
        input_data = f"28\n{atom_nums_str}\n{ion_type}, {num_ions}\n\n"
        self.run('xyzedit', [xyz, '-k', key], input_data=input_data)
        new_xyz = xyz + "_2"
        self.logger.info(f"Added ions. Output: {new_xyz}")
        return new_xyz

    def rename_file(self, src: str, dest: str):
        os.rename(src, dest)
        self.logger.info(f"Renamed {src} to {dest}")

    # Extra: parse charge from analyze output (if needed)
    def parse_total_charge(self, analyze_output: str) -> int:
        """Extracts the total charge reported by analyze."""
        for line in analyze_output.splitlines():
            if "Total Charge" in line:
                try:
                    return int(float(line.split()[-1]))
                except Exception:
                    pass
        raise ValueError("Charge not found in analyze output.")
