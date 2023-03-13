import sqlite3
import os
import time
import datetime
import sys

def setup_db(file):
    conn = sqlite3.connect(file)
    c = conn.cursor()
    c.executescript(
        """
        CREATE TABLE schemes (scheme_code INTEGER PRIMARY_KEY, scheme_name TEXT);
        CREATE TABLE nav (scheme_code INTEGER, date, nav FLOAT, FOREIGN KEY (scheme_code) REFERENCES schemes(scheme_code));
        CREATE TABLE securities (isin TEXT UNIQUE, type INTEGER, scheme_code INTEGER, FOREIGN KEY (scheme_code) REFERENCES schemes(scheme_code));
        CREATE VIEW nav_by_isin (isin, date, nav) as 
            SELECT isin,date,nav from nav N
            JOIN securities S ON N.scheme_code = S.scheme_code
            ORDER BY date DESC
        """
    )
    conn.commit()
    conn.close()

schemes = {}
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
    epoch_date = datetime.datetime(2006, 1,1)
    for root, dirs, files in os.walk("data"):
        # This is needed to avoid calling progressbar with an empty list
        if len(files) == 0:
            continue

        for file in progressbar(files, "Month: %s " % root[5:], 30):
            if file.endswith(".csv"):
                with open(os.path.join(root, file), "r") as f:
                    date = f"{root[5:9]}-{root[10:12]}-{file[0:2]}"
                    lines = f.readlines()[1:]
                    for line in lines:
                        if line == "" or ";" not in line:
                            continue
                        else:
                            line = line.split(";")
                            scheme_code = int(line[0])
                            if scheme_code not in schemes:
                                schemes[scheme_code] = line[1].strip()

                            isin_1 = line[2].strip().upper()
                            isin_2 = line[3].strip().upper()

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
                                    yield (scheme_code, date, nav)

def insert_securities(conn, isins):
    c = conn.cursor()
    for isin, (scheme_code, t) in isins.items():
        # Common issues with ISINs
        # 1. Extra I at the start
        if isin[0:3] == 'IIN':
            isin = isin[1:]
        # Missing I
        if isin[0:2] == 'NF':
            isin = 'I' + isin
        # Missing F
        if isin[0:3] == 'IN9':
            isin = "INF9" + isin[3:]
        if isin[0:3] != 'INF' or len(isin) != 12:
            print(f"Invalid ISIN: {isin}")
        else:
            c.execute(
                "INSERT INTO securities VALUES (?, ?, ?)",
                (isin, t, scheme_code),
            )
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
    # scheme, date, nav
    for data in get_data(conn):
        c.execute(
            "INSERT INTO nav VALUES (?, date(?), ?)",
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
