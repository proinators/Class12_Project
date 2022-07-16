# Voting System Prototype - By Pratyush
For a school project


This project aims to provide a simple voting system where candidates for multiple categories can be registered. The data is stored quite securely with encyption-enabled data files.

This project includes the Python virtual environment and the third-party packages required to run the program.
Run [`main.py`](main.py) to see the prototype in action.

The project is designed in such a way that you can easily change the interface for the application. The prototype uses a simple CLI, but the `Interface` class (in [`interface.py`](interface.py)) can be changed to use, say, a Flask powered web application, or a GUI application using tkinter, etc.

Link to the project details: https://docs.google.com/document/d/12akZLW5MbphFfAxk4QEyh3bEkXYdSV8ebNNDRbbqLbk/edit?usp=sharing


## Note:
1. This program requires the following third-party packages. These packages are included in the virtual environment included in the project, but you have to install them if you plan not to use it.
    1. `cryptopgraphy` (for Fernet encryption)
    2. `reedsolo` (for error correction, to prevent data corruption)
2. The program asks for 5 votes only, for debugging purposes
3. This project is licensed under the [GNU GPL v3](https://github.com/RedMiner2005/Class12_Project/blob/main/LICENSE)
