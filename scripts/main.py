import os
import dotenv

import sys


def __append_project_root_to_path() -> None:
    """
    assumes that root is one directory above
    """
    root_absolute_path: str = os.path.abspath(__file__ + "/..")
    root_path_name: str = os.path.dirname(root_absolute_path)
    sys.path.append(root_path_name)


__append_project_root_to_path()

from scripts import nubot


def __set_cwd_to_project_root() -> None:
    """
    assumes that root is one directory above
    """
    root_absolute_path: str = os.path.abspath(__file__ + "/..")
    root_path_name: str = os.path.dirname(root_absolute_path)
    os.chdir(root_path_name)


def __get_bot_token() -> str:
    dotenv.load_dotenv()
    return os.getenv("NUBOT_TOKEN")


def main() -> None:
    __set_cwd_to_project_root()
    bot: nubot.Nubot = nubot.Nubot()
    bot.run(__get_bot_token())


if __name__ == "__main__":
    main()
