import sqlite3
import os
import time
import datetime
import sys
# create a new sqlite database
# with a table called funds
# which has 2 columns - date (stored as a JULIAN day REAL)
# a scheme code (integer)
# nav (FLOAT)
# repurchase price (FLOAT)
# sale price (FLOAT)
# and a unique index on scheme code

def setup_db(file):
    conn = sqlite3.connect(file)
    c = conn.cursor()
    c.executescript(
        """
        CREATE TABLE schemes (scheme_code INTEGER PRIMARY_KEY, scheme_name TEXT);
        CREATE TABLE funds (days_since_epoch INTEGER, scheme_code INTEGER, nav FLOAT, FOREIGN KEY (scheme_code) REFERENCES schemes(scheme_code));
        CREATE TABLE securities (isin TEXT UNIQUE, type INTEGER, scheme_code INTEGER, FOREIGN KEY (scheme_code) REFERENCES schemes(scheme_code));
        """
    )
    conn.commit()
    conn.close()


"""
The directory structure for data directory is
data/YEAR/MM/DD.csv

This method iterates through every CSV file, and parses it with the following rules:
1. Ignore the first line
2. Ignore any empty lines
3. Ignore any lines without a semi-colon
4. Extract the first column as the scheme code
5. Extract the second column as the scheme name
6. Extract the fifth column as the NAV
7. Extract the sixth column as the repurchase price
8. Extract the seventh column as the sale price
9. Extract the last column as the date (DD-MMM-YYYY)
 where MMM is the month in 3 letter format
"""

schemes = {}
# A map of scheme code to ISIN from column 2
# ISIN Div Payout/ISIN Growth
# contains (scheme_code, type) as a tuple
isin_list = {}


def progressbar(it, prefix="", size=60, out=sys.stdout): # Python3.6+
    count = len(it)
    def show(j):
        x = int(size*j/count)
        print(f"{prefix}[{u'█'*x}{('.'*(size-x))}] {j}/{count}", end='\r', file=out, flush=True)
    show(0)
    for i, item in enumerate(it):
        yield item
        show(i+1)
    print("", flush=True, file=out)

def get_data(conn):
    # Julian Date Equivalent = 2453737.25
    epoch_date = datetime.datetime(2006, 1,1)
    for root, dirs, files in os.walk("data"):
        # This is needed to avoid calling progressbar with an empty list
        if len(files) == 0:
            continue

        for file in progressbar(files, "Month: %s " % root[5:], 30):
            if file.endswith(".csv"):
                with open(os.path.join(root, file), "r") as f:
                    date = datetime.datetime.fromisoformat(f"{root[5:9]}-{root[10:12]}-{file[0:2]}")
                    days_since = int((date - epoch_date).days)
                    lines = f.readlines()[1:]
                    for line in lines:
                        if line == "" or ";" not in line:
                            continue
                        else:
                            line = line.split(";")
                            scheme_code = int(line[0])
                            if scheme_code not in schemes:
                                schemes[scheme_code] = line[1].strip()

                            isin_1 = line[2].strip()
                            isin_2 = line[3].strip()

                            if isin_1 != "" and isin_1 not in isin_list:
                                isin_list[isin_1] = (scheme_code, 0)
                            if isin_2 != "" and isin_2 not in isin_list:
                                isin_list[isin_2] = (scheme_code, 1)

                            if line[4] not in ['-',"#N/A",'#DIV/0!','N.A.', 'NA', 'B.C.', 'B. C.']:
                                try:
                                    nav = float(line[4].strip().replace(",", "").replace('`', '').replace("-", ""))
                                except ValueError as e:
                                    # TODO: Save to an error log
                                    nav = False
                                if nav:
                                    yield (days_since, scheme_code-100000, nav)

def insert_securities(conn, isins):
    c = conn.cursor()
    try:
        for isin, (scheme_code, t) in isins.items():
            c.execute(
                "INSERT INTO securities VALUES (?, ?, ?)",
                (scheme_code, isin, t),
            )
    except sqlite3.IntegrityError as e:
        print((scheme_code, isin, t))
    conn.commit()

def insert_schemes(conn, schemes):
    c = conn.cursor()
    for scheme_code, scheme_name in schemes.items():
        c.execute(
            "INSERT INTO schemes VALUES (?, ?)",
            (scheme_code, scheme_name),
        )

def insert_data(conn):
    c = conn.cursor()
    for data in get_data(conn):
        # Insert data[0] as a julian date calling the julianday() function in sqlite
        # and data[1] as scheme code, and data[2] as nav
        c.execute(
            "INSERT INTO funds VALUES (?, ?, ?)",
            (data[0], data[1], data[2]),
        )

if __name__ == "__main__":
    # delete file funds.db
    if os.path.exists("funds.db"):
        os.remove("funds.db")
    setup_db("funds.db")
    conn = sqlite3.connect("funds.db")
    insert_data(conn)
    insert_schemes(conn, schemes)
    insert_securities(conn, isin_list)
    conn.commit()
    conn.close()
