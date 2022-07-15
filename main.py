"""
Voting System - By Pratyush
Prototype (Modular)

Note:
1. This program requires the following third-party packages:
    cryptopgraphy (for Fernet encryption)
    reedsolo (for error correction, to prevent data corruption)
2. The program asks for 5 votes only, for debugging purposes
"""

from interface import *
from backend import *


if __name__ == "__main__":
    ui = Interface()
    ui.main()
