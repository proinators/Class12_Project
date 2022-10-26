"""
Voting System

Note:
This program requires the following third-party packages:
    cryptopgraphy (for Fernet encryption)
    reedsolo (for error correction, to prevent data corruption)
    pwinput (for masking sensitive information)
"""

# Imports from the built-in library
import pickle
import base64
from pwinput import pwinput
from os.path import isfile, isdir
from os import mkdir
from hashlib import sha224, sha256

# Third-party package imports
from cryptography.fernet import Fernet
from reedsolo import RSCodec, ReedSolomonError

# Global Parameters/Constants
cand_path = "candidates/"  # The path where the candidate list will be stored
vote_path = "votes/"  # The path where the votes will be stored
pin_key = "-#*KEY*#-"  # The key of the dict item where the hash of the pin will be stored. It's best not to change it.
is_debug = False  # Enables debug messages
interface_separator = "\n_____________________________________________"  # For the interface

# Utility functions - Such as getting the path of a file, get hash of a name & category, etc.
path = lambda is_cand, name: (cand_path if is_cand else vote_path) + name + ".dat"
ensure_dir = lambda path: mkdir(path) if not isdir(path) else True
get_hash = lambda cat, name: sha224((cat + "::" + name).encode()).digest()
get_pin_hash = lambda pin: sha256(pin).digest()
get_key = lambda pin_hash, pin: (
    (base64.urlsafe_b64encode(pin_hash + pin).decode()[:43] + "=").encode()
    if get_pin_hash(pin) == pin_hash
    else False
)
get_masked = lambda msg: pwinput(msg, mask="*")
debug = lambda msg: print("[DEBUG]", msg) if is_debug else None


def get_int(msg):
    while True:
        try:
            return int(input(msg))
        except ValueError:
            print("Invalid input. Please enter an integer.\n")


class PinException(Exception):
    pass


# Classes
class Interface:
    """
    The user interface class that manages the windows (say in GUIs)
    """

    def __init__(self, *args, **kwargs):
        """Performs all the initialization for the UI"""
        self.backend = Backend(self.error_handler)
        debug("Backend initialized")
        # Intro
        print("VOTE-E")
        print("Voting system")
        print("____________________\n")

        # Give the option to use an existing candidate list or create a new one
        if input("Do you want to register new candidates (Y for yes, otherwise no): ").lower() == "y":
            self.backend.register(
                input("Enter the filename: "),
                get_masked(
                    "Enter the PIN to be used (Warning: You can't access your vote data without the pin): "
                ).encode(),
                self.register()
            )
        else:
            self.backend.read_candidates(input("Enter the filename: "))
        print()

    def error_handler(self, exception):
        """An error handling function passed to the backend.

        This will display the error and can be modified to take necessary actions to correct the error

        :param exception: The exception that was raised
        """
        debug(exception)

    def get_pin(self) -> bytes:
        """Asks the user for the PIN, and returns the PIN if correct.
        Keeps asking for the PIN until it is verified

        :returns: The correct PIN
        """
        while True:
            pin = get_masked("Enter the PIN: ").encode()

            if self.backend.verify_pin(pin):
                return pin
            print("Invalid PIN.\n")

    def main(self):
        """The main function of the program.
        This is executed after initialization
        """
        pin = self.get_pin()
        print()

        # Get 10 votes and store them all in a file
        for vote in [self.get_vote() for _ in range(get_int("Enter the total number of votes: "))]:
            self.backend.store_votes(pin, vote)

        # Display the results
        self.display_votes()

    def register(self):
        """The register window that allows the user to create an event.
        It asks for categories and the names of the candidates for each, and then returns it.

        :returns: The candidate dict
        """
        print(interface_separator)
        candidates = {}
        while True:
            cat = input("Enter category (Enter QUIT to exit): ")
            if cat == "QUIT":
                break
            print("Enter the names for the category (Enter QUIT to exit):")
            names = []
            while True:
                name = input()
                if name == "QUIT":
                    break
                names.append(name)
            candidates[cat] = names
            print()
        print(interface_separator)

        debug(candidates)
        return candidates

    def get_vote(self):
        """Gets the vote of a person from each category.
        It returns a dict with the first element being
        the token and the rest being hashes of the candidate details
        to whom the vote was casted

        :returns: The votes as a dictionary
        """
        print(interface_separator)
        votes = []
        for cat in self.backend.candidates:
            if cat == pin_key:
                continue
            names = self.backend.candidates[cat]
            length = len(names)
            print(f"Candidates for {cat}:")
            print("\n".join([f"{i + 1}. {names[i]}" for i in range(length)]))
            while True:
                try:
                    option = int(get_masked(f"Please choose an option from 1 to {length}: ")) - 1

                    assert 0 <= option < length
                    votes.append(get_hash(cat, names[option]))
                    break
                except Exception as e:
                    print("Invalid input.")
                    continue
            print()
        print("_____________________________________________")

        return votes

    def display_votes(self):
        """Displays the vote results and the winners"""
        votes = self.backend.read_votes(self.get_pin())
        candidates = self.backend.candidates
        winners = {}
        print(interface_separator)
        for cat in candidates:
            if cat == pin_key:
                continue
            for name in candidates[cat]:
                index = get_hash(cat, name)
                if index in votes:
                    if cat not in winners:
                        winners[cat] = (name, votes[index])
                    elif votes[index] == winners[cat][1]:
                        winners[cat] = ("{} and {}".format(winners[cat][0], name), votes[index])
                    elif votes[index] > winners[cat][1]:
                        winners[cat] = (name, votes[index])
                    print(f"Cat: {cat}, Name: {name}, Votes:", votes[index])
                else:
                    print(f"Cat: {cat}, Name: {name}, Votes: 0")

        print("\nWinners for each of the categories:")
        for cat in winners:
            print(f"{cat}: {winners[cat][0]} ({winners[cat][1]} votes)")
        print("_____________________________________________")


class Backend:
    """The backend services"""

    def __init__(self, error_handler):
        """Initialization for the backend services

        :param error_handler: The function of the Interface class that handles errors
        """
        self.error_handler = error_handler
        self.vote_file_name = ""
        self.candidates = {}
        self._codec = RSCodec(160)

        if not ensure_dir(cand_path):
            debug("Candidates path created")
        if not ensure_dir(vote_path):
            debug("Vote path created")

    def encrypt(self, key: bytes, data: dict) -> bytes:
        """Encrypts the data and encodes it using the RS algorithm.

        :param key: The encryption key
        :param data: The data to encrypt
        :returns: The encrypted data
        """
        f = Fernet(key)
        return self._codec.encode(f.encrypt(pickle.dumps(data)))

    def decrypt(self, key: bytes, data: bytes) -> dict:
        """Decrypts the data and decodes it using the RS algorithm.

        :param key: The encryption key
        :param data: The data to decrypt
        :returns: The decrypted data
        """
        f = Fernet(key)
        try:
            return pickle.loads(f.decrypt(bytes(self._codec.decode(data)[0])))
        except Exception as e:
            self.error_handler(e)
            return {}

    def verify_pin(self, pin) -> bool:
        """Verifies whether the PIN matches the stored hash

        :param pin: The input PIN
        :returns: Whether the PIN is correct or not
        """
        try:
            return self.candidates[pin_key] == get_pin_hash(pin)
        except Exception as e:
            self.error_handler(e)
            return False

    def register(self, filename: str, pin: bytes, candidates: dict) -> dict:
        """Registers the candidates.
        It stores the candidate dict in a file.

        :param filename: The filename of the file in which the data is stored
        :param pin: The pin to be stored
        :param candidates: A dict containing the candidate details
        :returns: The candidate dict
        """
        self.vote_file_name = filename
        for key in candidates:
            candidates[key] = tuple(candidates[key])
        candidates[pin_key] = get_pin_hash(pin)
        try:
            with open(path(True, filename), "wb") as file:
                pickle.dump(candidates, file)
        except Exception as e:
            self.error_handler(e)
        self.candidates = candidates
        return candidates

    def read_candidates(self, filename: str) -> dict:
        """Reads the candidate list

        :param filename: The file name of the candidate list
        :returns: The the loaded data
        """
        self.vote_file_name = filename
        try:
            with open(path(True, filename), "rb") as file:
                candidates = pickle.load(file)
                self.candidates = candidates
                return candidates
        except Exception as e:
            self.error_handler(e)
            return {}

    def store_votes(self, pin: bytes, votes: list) -> bool:
        """Stores the list of vote data
        It iterates through votes, which should
        contain the vote data generated by get_vote()
        The encrypted data is stored in a file in vote_path
        with its name being the encryption key. Just for fun.

        :param pin: The PIN used to encrypt the vote file
        :param votes: A list of vote data
        :returns: Whether the votes were stored successfully?
        """
        debug(votes)
        key = get_key(self.candidates[pin_key], pin)
        if not key:
            self.error_handler(PinException)
            return None
        if isfile(path(False, self.vote_file_name)):
            with open(path(False, self.vote_file_name), "rb") as file:
                debug("Store: Vote data found.")
                data = self.decrypt(key, file.read())
        else:
            debug("Store: Vote data not found. Creating new file.")
            data = {}
        for vote in votes:
            if vote in data:
                data[vote] += 1
            else:
                data[vote] = 1
        debug(data)

        with open(path(False, self.vote_file_name), "wb") as file:
            file.write(self.encrypt(key, data))
        return True

    def read_votes(self, pin: bytes) -> dict:
        """Reads and displays the data from a vote file

        :param pin: The PIN used to encrypt the vote data
        :returns: The vote data
        """
        key = get_key(self.candidates[pin_key], pin)
        if not key:
            self.error_handler(PinException)
            return None
        if isfile(path(False, self.vote_file_name)):
            data = self.decrypt(key, open(path(False, self.vote_file_name), "rb").read())
            debug("Read: Votes found: " + str(data))
        else:
            debug("Read: Votes not found")
            data = {}
        return data


if __name__ == "__main__":
    ui = Interface()
    ui.main()
    input("\n\nPress any key to exit...")
