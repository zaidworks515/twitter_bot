# slang_picker.py
import random
import requests

class SlangPicker:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SlangPicker, cls).__new__(cls)
            cls._instance.last_picked_terms = set()
        return cls._instance

    def pick_random_slang(self):
        all_terms = [
            "Lit", "Dope", "Flex", "Salty", "Cap", "Bet", "Vibe", "Lowkey", "Slaps", "Goat",
            "Fire", "Woke", "Clout", "No cap", "Chill", "Drip", "Savage", "Squad", "Shade", "Mood",
            "Baller", "Buckets", "Dime", "Splash", "Swish", "Brick", "Handles", "Posterize", "Full-Court Press", "Ankle Breaker",
            "And-one", "Alley-oop", "Crossover", "Fadeaway", "Triple-double", "Putback", "Fast break", "Hustle", "Iso", "Box out",
            "bruh", "fam"
        ]

        available_terms = [term for term in all_terms if term not in self.last_picked_terms]

        # If not enough terms are available, reset the set
        if len(available_terms) < 3:
            self.last_picked_terms.clear()
            available_terms = all_terms

        # Pick between 3 and 6 terms
        min_to_pick = random.randint(3, 6)
        selected_terms = random.sample(available_terms, min_to_pick)

        # Update the global state
        self.last_picked_terms = set(selected_terms)
        return selected_terms


