#    Copyright (C) 2020 BLIBWT

#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.

#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.

# flake8: noqa: T001

"""Initial entrypoint"""

import sys
if sys.version_info < (3, 6, 0):  # Minimum version - asyncio got major revamp and so did importlib
    print("Error: you must use at least Python version 3.6.0")
else:
    if sys.version_info >= (3, 9, 0):
        print("Warning: you are using an untested Python version")
    if __package__ != "t-userbot":  # In case they did python __main__.py
        print("Error: you cannot run this as a script; you must execute as a package")
    else:
        try:
            from . import main
        except ModuleNotFoundError:
            print("Error: you have not installed all dependencies correctly.")
            print("Please install all dependencies from requirements.txt")
        else:
            if __name__ == '__main__':
                main.main()  # Execute main function
