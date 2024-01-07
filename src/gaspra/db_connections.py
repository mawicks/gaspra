import sqlite3

DATABASE = ":memory:"
DATABASE = "/tmp/foo.db"

connection = None


def connection_factory():
    global connection
    if connection is None:
        connection = sqlite3.connect(DATABASE)
    return connection
