import logging
import os
import shutil

from tinkergui.preparers import SystemPreparer
from tinkergui.utils import ConfigManager, init_logger

if __name__ == "__main__":
    temp_dir = os.path.join(os.getcwd(), "temp")
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    init_logger(log_file=os.path.join(temp_dir, "log"))
    logger = logging.getLogger(__name__)

    config_manager = ConfigManager()
    config_manager.parse_args()
    config = config_manager.get_config()
    config_manager.save_yaml(path=os.path.join(temp_dir, "config.yaml"))

    sysprep = SystemPreparer(working_directory=temp_dir)
    sysprep.prepare()
    final_txyz = sysprep.txyz_file
    shutil.copy(final_txyz, os.path.join(os.getcwd(), f"{config.output_prefix}_final.xyz"))
    sysprep.key_file.save_key_file(os.path.join(os.getcwd(), f"{config.output_prefix}_final.key"))
    logger.info(f"Final prepared files saved to {os.getcwd()} with prefix {config.output_prefix}_final .")
