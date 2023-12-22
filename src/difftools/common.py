import os

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data"))

if __name__ == "__main__":
    print(DATA_DIR)
