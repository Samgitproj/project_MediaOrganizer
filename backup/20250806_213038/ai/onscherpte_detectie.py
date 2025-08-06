import datetime
import math
import json

import sys
import os

# Algemene helper imports
import logging


class DataProcessor:
    def __init__(self, data):
        logging.info("Initializing DataProcessor")
        self.data = data

    def process(self):
        logging.info("Starting data processing")
        result = [d * 2 for d in self.data]
        logging.info(f"Data processed: {result}")
        return result

    def greet(name):
        print(f"Hello, {name}!")

    def ask_name():
        logging.info("Asking for name")
        name = input("Please enter your name: ")
        return name

    def farewell(name):
        print(f"Goodbye, {name}!")

    def main():
        greet("Tester")
        processor = DataProcessor([1, 2, 3])
        processed = processor.process()
        print(processed)
        farewell("Tester")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
