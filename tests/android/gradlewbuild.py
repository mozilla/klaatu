import logging
import os
import subprocess

from .adbrun import ADBrun

here = os.path.dirname(__file__)
logging.getLogger(__name__).addHandler(logging.NullHandler())


class GradlewBuild(object):
    binary = "./gradlew"
    logger = logging.getLogger()
    adbrun = ADBrun()

    def __init__(self, log):
        self.log = log

    def test(self, identifier, smoke=None):
        # self.adbrun.launch()
        test_type = "ui" if smoke else "experimentintegration"
        cmd = [
            "adb shell am instrument -w",
            f"-e class org.mozilla.fenix.{test_type}.{identifier}",
            f"-e EXP_NAME '{os.getenv('EXP_NAME', '').replace('(', '').replace(')', '')}'",
            "org.mozilla.fenix.debug.test/androidx.test.runner.AndroidJUnitRunner",
        ]

        self.logger.info("Running cmd: {}".format(" ".join(cmd)))

        out = ""
        try:
            out = subprocess.check_output(
                " ".join(cmd), encoding="utf8", shell=True, stderr=subprocess.STDOUT
            )
            logging.debug(out)
            if "FAILURES" in out:
                raise (AssertionError(out))
        except subprocess.CalledProcessError as e:
            out = e.output
            raise
        finally:
            with open(self.log, "w") as f:
                f.write(str(out))
