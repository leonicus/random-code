import os
from logging import getLogger
logger = getLogger(__name__)

try:
    import pygetwindow as gw
except:
    logger.info("failed importing pygetwindow, probably unsupported OS")
from perf_aut.infra.perf_managers.perf_agent_manager import AgentManager
from perf_aut.infra.perf_operations.copy_vbs_operation import VBSCopyOperation
from perf_aut.infra.polling.polling_utils import PollingConfiguration
from perf_aut.utils.perf_utils.files_utils import FileUtils



class VBSExecuteOperation(VBSCopyOperation):
    ORIGIN_FOLDER = "c:\\tmp\\vbs"
    VBS_CONSOLE_STRING = "CreatedVBS"
    def __init__(self, num_files: int = 1):
        super().__init__(num_files=num_files)
        self.verify_operation_polling_config = PollingConfiguration(tries=100, sleep_between_tries=0.01, perf_oper=True)
        self.create_tmp_dir()
        self.open_windows = []
        self.test_name = "execute_vbs"

    def check_vbs_window(self, window_title: str, expected_value: bool = True) -> bool:
        try:
            # Focus the VBS window
            windows = gw.getWindowsWithTitle(window_title)
            if windows and len(windows) == self.num_files:
                self.open_windows = windows
                logger.info(f'found open {windows} ')
                return True
            else:
                logger.info(
                    f'Expected {self.num_files} window(s) with title "{window_title}", but found {len(windows) if windows else 0}.')
                return False
        except Exception as e:
            logger.error(f'Error getting windows with title {window_title}: {e}', exc_info=True)
            return not expected_value


    def create_tmp_dir(self) -> None:
        if not FileUtils.create_dir(self.ORIGIN_FOLDER, exist_ok=True):
            raise Exception(f'unable to create folder {self.ORIGIN_FOLDER} for source')

    def prepare_operation(self) -> None:
        logger.info('going to stop agent')
        AgentManager.stop_agent()
        super().prepare_operation()
        AgentManager.start_agent()

    def run_operation(self) -> None:
        try:
            filenames = os.listdir(self.ORIGIN_FOLDER)
            logger.info(f'found files to run: {filenames}')
            for f in filenames:
                full_filename = os.path.join(self.ORIGIN_FOLDER, f)
                os.system(f'powershell.exe {full_filename}')
        except Exception as e:
            logger.error(f'failed running vbs file with error {e}', exc_info=True)

    def verify_operation(self) -> bool:
        return self.check_vbs_window(self.VBS_CONSOLE_STRING, expected_value=True)

    def clean_operation(self) -> None:
        if self.open_windows:
            logger.info(f'going to close {self.open_windows}')
            for w in self.open_windows:
                try:
                    w.close()
                except Exception as e:
                    logger.error(f'failed closing window with error {e}', exc_info=True)

    def verify_clean_operation(self) -> bool:
        return not self.check_vbs_window(self.VBS_CONSOLE_STRING, expected_value=False)
