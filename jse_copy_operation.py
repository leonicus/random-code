from logging import getLogger

from perf_aut.infra.perf_operations.templated_operation import TemplatedFilesOperation
from perf_aut.utils.perf_utils.files_utils import FileUtils

logger = getLogger(__name__)
class JseCopyOperation(TemplatedFilesOperation):
    ORIGIN_FOLDER = r"\\10.196.20.254\vol_QA\python_perf_tools\EncodedFiles"
    FILE_TEMPLATE = r"\\10.196.20.254\vol_QA\python_perf_tools\EncodedTemplates\myscript.jse"
    LENGTH_RANDOM_STRING = 15

    def __init__(self, num_files: int = 1) -> None:
        super().__init__(source_dir=self.ORIGIN_FOLDER, num_files=num_files, template_file=self.FILE_TEMPLATE)
        self.test_name = "copy_jse"

    def prepare_operation(self) -> None:
        if not FileUtils.clean_dir(self.ORIGIN_FOLDER):
            raise Exception(f"unable to clean {self.ORIGIN_FOLDER}")
        self.prepare_src_folder()

    def modify_content(self, base_string: str, **kwargs) -> str:
        additional_string = create_random_string(15)
        return f'''
       {base_string} \n
       random_string= "Hello  {additional_string}"
       '''
