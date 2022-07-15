from utils import *
from backend import *


class Interface:
    """
    The user interface class that manages the windows (say in GUIs)
    """
    def __init__(self, *args, **kwargs):
        """Performs all the initialization for the UI
        
        Make sure you include the self.backend to access all of the backend services
        """
        self.backend = Backend(self.error_handler)
        debug("Backend initialized")
        # Intro stuff
        print("Voting system - Prototype")
        print("Designed by Pratyush")
        print("____________________________")
        print("(Type QUIT to exit any of the loops)\n")

        # Give the option to use an existing candidate list or create a new one
        if input("Do you want to register new candidates (Y for yes, otherwise no): ").lower() == "y":
            candidates = self.backend.register(input("Enter the filename: "),
                input("Enter the PIN to be used (Warning: You can't access your vote data without the pin): ").encode(),
                self.register())
        else:
            candidates = self.backend.read_candidates(input("Enter the filename: "))
        print()
    
    def error_handler(self, exception):
        """An error handling function passed to the backend.
        
        This will display the error and/or take necessary actions to correct the error
        Remember to account for ReedSolomonError, which is
        raised when too many errors exist in the stored data.

        :param exception: The exception that was raised
        """
        debug(exception)
    
    def get_pin(self) -> bytes:
        """Asks the user for the PIN, and returns the PIN if correct.
        Keeps asking for the PIN until it is verified

        :returns: The correct PIN
        """
        while True:
            pin = input("\nEnter the PIN: ").encode()
            if self.backend.verify_pin(pin):
                return pin
            print("Invalid PIN.\n")
    
    def main(self):
        """The main function of the program.
        This is executed after initialization
        """
        pin = self.get_pin()

        # Get 10 votes and store them all in a file
        for vote in [self.get_vote() for i in range(5)]:
            self.backend.store_votes(pin, vote)
        
        # Display the results
        self.display_votes()

    def register(self):
        """The register window that allows the user to create an event.
        It asks for categories and the names of the candidates for each, and then returns it.

        :returns: The candidate dict
        """
        print("\n_____________________________________________")
        candidates = {}
        while True:
            cat = input("Enter category: ")
            if cat == "QUIT":
                break
            print("Enter the names for the category:")
            names = []
            while True:
                name = input()
                if name == "QUIT":
                    break
                names.append(name)
            candidates[cat] = names
            print()
        print("\n_____________________________________________")

        debug(candidates)
        return candidates
    
    def get_vote(self):
        """Gets the vote of a person from each category.
        It returns a dict with the first element being
        the token and the rest being hashes of the candidate details
        to whom the vote was casted

        :returns: The votes as a dictionary
        """
        print("\n_____________________________________________")
        votes = []
        for cat in self.backend.candidates:
            if cat == pin_key:
                continue
            names = self.backend.candidates[cat]
            l = len(names)
            print(f"Candidates for {cat}:")
            print("\n".join([f"{i+1}. {names[i]}" for i in range(l)]))
            while True:
                try:
                    option = int(input(f"Please choose an option from 1 to {l}: ")) - 1
                    assert 0 <= option < l
                except Exception as e:
                    print("Invalid input")
                    continue
                break
            votes.append(get_hash(cat, names[option]))
            print()
        print("_____________________________________________")

        return votes
    
    def display_votes(self):
        """Displays the vote results and the winners"""
        votes = self.backend.read_votes(self.get_pin())
        candidates = self.backend.candidates
        winners = {}
        print("\n_____________________________________________")
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
