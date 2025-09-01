import os
import shutil
import traceback
from logging import getLogger
from typing import Optional

from perf_aut.infra.perf_operations.copy_file import CopyFileOperation

logger = getLogger(__name__)


class TemplatedFilesOperation(CopyFileOperation):
    def __init__(self, source_dir: str, template_file: str, num_files: int = 1) -> None:
        super().__init__()
        self.num_files = num_files
        self.source = source_dir
        self.template_file = template_file

    def prepare_src_folder(self, base_name: str, extension: str) -> None:
        logger.info(f'starting source folder creation with {self.num_files} files')
        for i in range(self.num_files):
            path_to_write = os.path.join(self.source, f"{base_name}_{i}.{extension}")
            content = self.generic_modify(file_path=self.template_file)
            try:
                with open(path_to_write, 'w') as f:
                    f.write(content)
            except IOError as e:
                logger.error(f'unable to write file {path_to_write} with error {e}', exc_info=True)
                raise e

    def generic_modify(self, file_path: str):
        try:
            with open(file_path, 'r') as f:
                base_str = f.read()
            return self.modify_content(base_str)

        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            raise

        except Exception:
            logger.error(f"Unexpected error while modifying {file_path}\n{traceback.format_exc()}")
            raise

    def modify_content(self, base_string: str, **kwargs) -> Optional[str]:
        raise Exception("method must be implemented in child class")
