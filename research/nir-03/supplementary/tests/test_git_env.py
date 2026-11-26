import os
import pathlib
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from git_env import build_git_environment, redact_git_error


class GitEnvironmentTests(unittest.TestCase):
    def build(self):
        home = tempfile.mkdtemp(prefix="nir03-git-env-test-")
        return build_git_environment(
            token="synthetic-test-token",
            token_file=os.path.join(home, "token"),
            askpass=os.path.join(home, "askpass"),
            home=home,
        )

    def test_exactly_one_complete_indexed_config_entry(self):
        with patch.dict(
            os.environ,
            {
                "GIT_CONFIG_COUNT": "9",
                "GIT_CONFIG_KEY_1": "core.hooksPath",
                "GIT_CONFIG_VALUE_1": "/unexpected",
                "GIT_CONFIG_PARAMETERS": "'core.pager=cat'",
                "GIT_DIR": "/unexpected/repository",
            },
        ):
            env = self.build()

        self.assertEqual(env["GIT_CONFIG_COUNT"], "1")
        self.assertEqual(env["GIT_CONFIG_KEY_0"], "http.extraheader")
        self.assertEqual(
            env["GIT_CONFIG_VALUE_0"],
            "Authorization: token synthetic-test-token",
        )
        self.assertFalse(any(k.startswith("GIT_CONFIG_KEY_1") for k in env))
        self.assertNotIn("GIT_CONFIG_PARAMETERS", env)
        self.assertNotIn("GIT_DIR", env)

    def test_git_accepts_constructed_environment(self):
        env = self.build()
        result = subprocess.run(
            ["git", "config", "--get", "http.extraheader"],
            env=env,
            text=True,
            capture_output=True,
            check=True,
        )
        self.assertEqual(
            result.stdout.strip(), "Authorization: token synthetic-test-token"
        )

    def test_git_error_redacts_credential(self):
        self.assertEqual(
            redact_git_error("failure synthetic-test-token details", "synthetic-test-token"),
            "failure [REDACTED] details",
        )


if __name__ == "__main__":
    unittest.main()
