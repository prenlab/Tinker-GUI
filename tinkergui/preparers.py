import logging
import math
import os
import re
import shutil

from .utils import ConfigManager, TinkerKeyFile, AtomTypeFinder, make_readable_ids
from .tinker_runner import TinkerRunner


logger = logging.getLogger(__name__)
config = ConfigManager().get_config()

class BasePreparer:
    """Base class for all kinds of molecular system preparers."""
    def __init__(self, working_directory, raw_structure_file, key_file) -> None:
        self.wd = working_directory
        self.raw_structure_file = raw_structure_file
        if raw_structure_file:
            # set txyz file path
            self.txyz_file = os.path.splitext(self.raw_structure_file)[0] + ".xyz"
        else:
            self.txyz_file = ''
        self.key_file = key_file
        if os.path.exists(raw_structure_file):
            # check and copy raw structure file to working directory
            if not os.path.exists(os.path.join(self.wd, os.path.basename(self.raw_structure_file))):
                shutil.copy(self.raw_structure_file, self.wd)
            self.raw_structure_file = os.path.join(self.wd, os.path.basename(self.raw_structure_file))

    def pdb_to_txyz(self):
        """Convert PDB file to Tinker XYZ format."""
        assert os.path.splitext(self.raw_structure_file)[1].lower() == '.pdb', "Input file must be a PDB file."
        tinker = TinkerRunner(wd=self.wd, tinker_path=config.tinker_path)
        tinker.call(
            program='pdbxyz',
            cmd_args=f"{os.path.basename(self.raw_structure_file)} -k {self.key_file.latest_path}",
            inter_inps='\n\n',
            envs='',
            pre_cmds='',
            expected_outfiles=(self.txyz_file,),
        )
        logger.info(f"Converted PDB {self.raw_structure_file} to Tinker XYZ {self.txyz_file}.")

    def align_to_inertial_frame(self):
        """Align the molecular system to its inertial frame."""
        assert os.path.exists(self.txyz_file), "This operation cannot be done without a Tinker XYZ file."
        tinker = TinkerRunner(wd=self.wd, tinker_path=config.tinker_path)
        outs = tinker.call(
            program='xyzedit',
            cmd_args=f"{os.path.basename(self.txyz_file)} -k {self.key_file.latest_path}",
            inter_inps='\n\n',
            envs='',
            pre_cmds='',
        )
        option_num = re.findall(r"\((\d+)\) Translate and Rotate to Inertial Frame", outs)[0]
        outs = tinker.call(
            program='xyzedit',
            cmd_args=f"{os.path.basename(self.txyz_file)} -k {self.key_file.latest_path}",
            inter_inps=f'{option_num}\n\n',
            envs='',
            pre_cmds='',
            expected_outfiles=(self.txyz_file + "_2",),
            custom_outfile_suffix='_aligned',
        )
        logger.info(f"Aligned Tinker XYZ {self.txyz_file} to its inertial frame.")
        return os.path.join(self.wd, os.path.splitext(self.txyz_file)[0] + "_aligned.xyz")

    def get_net_charge(self) -> float:
        """Calculate and return the net charge of the molecular system."""
        assert os.path.exists(self.txyz_file), "This operation cannot be done without a Tinker XYZ file."
        tinker = TinkerRunner(wd=self.wd, tinker_path=config.tinker_path)
        outs = tinker.call(
            program='analyze',
            cmd_args=f"{os.path.basename(self.txyz_file)} -k {self.key_file.latest_path}",
            inter_inps='M\n',
            envs='',
            pre_cmds='',
        )
        charge = re.findall(r"Total Electric Charge :\s+([-+]?\d*\.\d+|\d+)\s+Electrons", outs)[0]
        charge = int(float(charge))
        return charge

    def get_bounding_box_size(self, buffer: float = 12.0):
        """Calculate and return the minimum bounding box dimensions with optional padding buffer."""
        assert os.path.exists(self.txyz_file), f"This operation cannot be done without a Tinker XYZ file. {self.txyz_file} not found."
        with open(self.txyz_file) as f:
            lines = f.readlines()
        if "." in lines[1].strip().split()[1]:
            lines = lines[2:]  # skip the second line if it contains a float (box info)
        else:
            lines = lines[1:]  # skip the first line (number of atoms)

        xs = [float(line.strip().split()[2]) for line in lines if line.strip()]
        ys = [float(line.strip().split()[3]) for line in lines if line.strip()]
        zs = [float(line.strip().split()[4]) for line in lines if line.strip()]
        x_size = math.ceil(max(xs) - min(xs) + 2 * buffer)
        y_size = math.ceil(max(ys) - min(ys) + 2 * buffer)
        z_size = math.ceil(max(zs) - min(zs) + 2 * buffer)
        logger.info(f"Calculated bounding box size: ({x_size}, {y_size}, {z_size}) Å with buffer {buffer} Å.")
        return (x_size, y_size, z_size)

    def prepare(self):
        """Prepare the molecular system."""
        raise NotImplementedError("This method should be implemented by subclasses.")
    

class ProteinPreparer(BasePreparer):
    """Preparer for proteins."""
    def __init__(self, working_directory, raw_structure_file, key_file, protonation_state='auto') -> None:
        super().__init__(working_directory, raw_structure_file, key_file)
        self.protonation_state = protonation_state   #TODO: implement protonation state handling

    def prepare(self):
        """Prepare the protein structure: add hydrogens, set protonation states, etc."""
        self.pdb_to_txyz()


class NucleicAcidPreparer(BasePreparer):
    """Preparer for nucleic acids."""
    def __init__(self, working_directory, raw_structure_file, key_file) -> None:
        super().__init__(working_directory, raw_structure_file, key_file)

    def prepare(self):
        """Prepare the nucleic acid structure: add hydrogens, check base pairing, etc."""
        self.pdb_to_txyz()


class LigandPreparer(BasePreparer):
    """Preparer for small molecule ligands."""
    def __init__(self, working_directory, raw_structure_file, key_file) -> None:
        super().__init__(working_directory, raw_structure_file, key_file)

    def prepare(self):
        """Prepare the ligand structure: generate parameters, optimize geometry, etc."""
        pass


class SolventBoxPreparer(BasePreparer):
    """Preparer for solvent boxes."""
    def __init__(self, working_directory, solvent_name, box_type, box_size, key_file) -> None:
        self.solvent_name = solvent_name
        self.box_type = box_type
        self.box_size = box_size
        if self.solvent_name.lower() == "water":
            raw_structure_file = os.path.join(os.path.dirname(__file__), "data", "water_cube_120A.xyz")
        else: 
            raw_structure_file = ''
        super().__init__(working_directory, raw_structure_file=raw_structure_file, key_file=key_file)
        self.atom_type_finder = AtomTypeFinder(prm_file_path=config.amoeba_prm)

    def prepare(self):
        """Prepare the solvent box: generate solvent molecules, pack the box, etc."""
        if self.solvent_name.lower() == "water":
            assert max(self.box_size) <= 120, "Predefined water box is only as big as 120 Å."
            assert self.box_type.lower() == "cuboid", "Predefined water box is only cubic."
            water_O_type = self.atom_type_finder.find_atom_type(description="Water O")
            water_H_type = self.atom_type_finder.find_atom_type(description="Water H")
            tinker = TinkerRunner(wd=self.wd, tinker_path=config.tinker_path)
            outs = tinker.call(
                program='xyzedit',
                cmd_args=f"{os.path.basename(self.txyz_file)} -k {self.key_file.latest_path}",
                inter_inps='\n\n',
                envs='',
                pre_cmds='',
            )
            option_nums = [
                re.findall(r"\((\d+)\) Replace Old Atom Type with a New Type", outs)[0],
                re.findall(r"\((\d+)\) Translate and Rotate to Inertial Frame", outs)[0],
                re.findall(r"\((\d+)\) Trim a Periodic Box to a Smaller Size", outs)[0],
            ]
            outs = tinker.call(
                program='xyzedit',
                cmd_args=f"{os.path.basename(self.txyz_file)} -k {self.key_file.latest_path}",
                inter_inps=(
                    f"{option_nums[0]}\n1,{water_O_type}\n"
                    f"{option_nums[0]}\n2,{water_H_type}\n"
                    f"{option_nums[1]}\n"
                    f"{option_nums[2]}\n{self.box_size[0]},{self.box_size[1]},{self.box_size[2]}\n"
                    "\n"
                ),
                envs='',
                pre_cmds='',
                expected_outfiles=(self.txyz_file + "_2",),
                custom_outfile_suffix='_trimmed',
            )
            new_txyz = os.path.join(self.wd, os.path.splitext(self.txyz_file)[0] + "_trimmed.xyz")
            logger.info(f"Prepared water solvent box Tinker XYZ: {new_txyz} .")
            return new_txyz, (water_O_type, water_H_type)
        else:
            raise NotImplementedError(f"Solvent {self.solvent_name} is not yet implemented.")
        

class SystemPreparer(BasePreparer):
    """Preparer for the entire molecular system with everything included."""
    def __init__(self, working_directory=".") -> None:
        structure_file = os.path.join(working_directory, f"{config.output_prefix}.xyz")
        key_file = os.path.join(working_directory, f"{config.output_prefix}.key")
        super().__init__(working_directory, raw_structure_file=structure_file, key_file=key_file)

        self.key_file = TinkerKeyFile(key_file)
        self.key_file.set_key("parameters", os.path.abspath(config.amoeba_prm))
        self.key_file.save_key_file()

        self.components = []
        for k, v in vars(config.solutes).items():
            for vi in v:
                self.components.append(
                    {
                        'protein': ProteinPreparer,
                        'nucleic_acid': NucleicAcidPreparer,
                        'ligand': LigandPreparer
                    }[k](working_directory=self.wd, raw_structure_file=vi, key_file=self.key_file)
                )
        self.solvent_atom_types = []
        self.atom_type_finder = AtomTypeFinder(prm_file_path=config.amoeba_prm)
        self.box_size = None

    def prepare(self):
        """Prepare the entire molecular system."""
        for component in self.components:
            component.prepare()

        # combine all components into one system
        if len(self.components) > 1:
            raise NotImplementedError("Combining multiple components is not yet implemented.")
        else:
            shutil.copy(self.components[0].txyz_file, self.txyz_file)
        logger.info(f"Combined solutes and then obtained the system Tinker XYZ: {self.txyz_file}.")

        # align to inertial frame
        self.txyz_file = self.align_to_inertial_frame()
        logger.info("Aligned the system to its inertial frame.")
        
        # build solvent box
        self.box_size = self.get_bounding_box_size(buffer=config.box.buffer)
        boxfile, self.solvent_atom_types = SolventBoxPreparer(
            working_directory=self.wd,
            solvent_name=config.solvent.name,
            box_type=config.box.type,
            box_size=self.box_size,
            key_file=self.key_file
        ).prepare()
        # soak into the box
        self.txyz_file = self.soak_into_box(boxfile)
        self.key_file.set_key("a-axis", str(self.box_size[0]))
        self.key_file.set_key("b-axis", str(self.box_size[1]))
        self.key_file.set_key("c-axis", str(self.box_size[2]))
        if config.box.type.lower() != "cuboid":
            raise NotImplementedError(f"Box type {config.box.type} not yet implemented for box info in key. Currently only `cuboid` is supported.")
        # add ions
        self.txyz_file = self.neutralize()
        self.txyz_file = self.add_salts()

    def soak_into_box(self, boxfile):
        """Soak the system into a solvent box."""
        assert os.path.exists(self.txyz_file), "This operation cannot be done without a Tinker XYZ file."
        tinker = TinkerRunner(wd=self.wd, tinker_path=config.tinker_path)
        outs = tinker.call(
            program='xyzedit',
            cmd_args=f"{os.path.basename(self.txyz_file)} -k {self.key_file.latest_path}",
            inter_inps='\n\n',
            envs='',
            pre_cmds='',
        )
        option_num = re.findall(r"\((\d+)\) Soak Current Molecule in Box of Solvent", outs)[0]
        outs = tinker.call(
            program='xyzedit',
            cmd_args=f"{os.path.basename(self.txyz_file)} -k {self.key_file.latest_path}",
            inter_inps=f'{option_num}\n{os.path.basename(boxfile)}\n\n',
            envs='',
            pre_cmds='',
            expected_outfiles=(self.txyz_file + "_2",),
            custom_outfile_suffix='_solvated',
        )
        new_txyz = os.path.join(self.wd, os.path.splitext(self.txyz_file)[0] + "_solvated.xyz")
        logger.info(f"Soaked the system into solvent box: {new_txyz} .")
        return new_txyz
    
    def add_ions(self, atom_type, number, suffix):
        """Add ions of specified types and number to the system."""
        solute_atom_indices = self.get_solute_atom_indices()
        solute_atom_indices_string = ""
        for i in solute_atom_indices:
            if len(i) == 2:
                solute_atom_indices_string += f"-{i[0]},{i[1]},"
            else:
                solute_atom_indices_string += f"{i[0]},"
        solute_atom_indices_string = solute_atom_indices_string.rstrip(',')
        tinker = TinkerRunner(wd=self.wd, tinker_path=config.tinker_path)
        outs = tinker.call(
            program='xyzedit',
            cmd_args=f"{os.path.basename(self.txyz_file)} -k {self.key_file.latest_path}",
            inter_inps='\n\n',
            envs='',
            pre_cmds='',
        )
        option_num = re.findall(r"\((\d+)\) Place Monoatomic Ions around a Solute", outs)[0]
        outs = tinker.call(
            program='xyzedit',
            cmd_args=f"{os.path.basename(self.txyz_file)} -k {self.key_file.latest_path}",
            inter_inps=(
                f'{option_num}\n'
                f'{solute_atom_indices_string}\n'
                f'{atom_type},{number}\n\n'
            ),
            envs='',
            pre_cmds='',
            expected_outfiles=(self.txyz_file + "_2",),
            custom_outfile_suffix=suffix,
        )
    
    def neutralize(self):
        """Neutralize the system by adding counter ions."""
        assert os.path.exists(self.txyz_file), "This operation cannot be done without a Tinker XYZ file."
        charge = self.get_net_charge()
        # charge = 4   # just for testing
        if charge == 0:
            logger.info("The system is already neutral. No need to add counter ions.")
            return self.txyz_file
        for ion in config.ions.neutralizers:
            ion_atom_type = self.atom_type_finder.find_atom_type(description=f"Ion {ion.strip('+-123').capitalize()}")
            ion_charge = self.atom_type_finder.find_atom_charge(atom_type=ion_atom_type)
            if ion_charge * charge < 0:
                counter_ion = ion_atom_type
                num_to_add = int(abs(charge / ion_charge))

        self.add_ions(counter_ion, num_to_add, suffix='_neutralized')
        new_txyz = os.path.join(self.wd, os.path.splitext(self.txyz_file)[0] + "_neutralized.xyz")
        logger.info(f"Neutralized the system: {new_txyz} .")
        return new_txyz

    def add_salts(self):
        """Add ions to neutralize the system and set salt concentration."""
        assert os.path.exists(self.txyz_file), "This operation cannot be done without a Tinker XYZ file."
        if config.box.type.lower() == "cuboid":
            box_volume = self.box_size[0] * self.box_size[1] * self.box_size[2]
        else:
            raise NotImplementedError(f"Box type {config.box.type} not yet implemented for salt addition.")
        box_volume_liters = box_volume * 1e-27  # convert from Å^3 to liters
        for ion, conc in zip(config.ions.salts.names, config.ions.salts.concentrations):
            ion_atom_type = self.atom_type_finder.find_atom_type(description=f"Ion {ion.strip('+-123').capitalize()}")
            num_ions = int(conc * box_volume_liters * 6.022e23)  # mol/L * L * Avogadro's number
            if num_ions > 0:
                self.add_ions(ion_atom_type, num_ions, suffix=f'_{ion}_added')
                new_txyz = os.path.join(self.wd, os.path.splitext(self.txyz_file)[0] + f"_{ion}_added.xyz")
                logger.info(f"Added {num_ions} of ion {ion} to the system: {new_txyz} .")
                self.txyz_file = new_txyz
        return self.txyz_file

    def get_solute_atom_indices(self):
        with open(self.txyz_file) as f:
            lines = f.readlines()
        if "." in lines[1].strip().split()[1]:
            lines = lines[2:]  # skip the second line if it contains a float (box info)
        else:
            lines = lines[1:]  # skip the first line (number of atoms)
        lines = [line.strip().split() for line in lines]
        solute_atom_indices = [int(line[0]) for line in lines if line[5] not in self.solvent_atom_types]
        solute_atom_indices = make_readable_ids(solute_atom_indices)
        return solute_atom_indices
    




