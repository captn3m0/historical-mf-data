# Historical Mutual Funds Data

An archive of historical mutual fund pricing information in India. This repository contains the raw data as well as the scripts used to generate it.

The data in the `data/` directory is in the same format as AMFI exports it, without any changes. This notably includes a few errors:

1. A few invalid ISINs (such as `NOTAPP` or `NA` for "Not Applied"), and a few with invalid prefixes (`IINF` instead of `INF`) or lowercase ISINs.
2. Lots of invalid NAVs, such as `"#N/A",'#DIV/0!','N.A.', 'NA', 'B.C.', 'B. C.'`

## Get Data

You can get the latest dataset at <https://github.com/captn3m0/historical-mf-data/releases/latest/funds.db>. Each dataset includes all historical NAVs at all known times for a given mutual fund.

To get NAV for a given ISIN, use the following query:

```

```

## Data Format

The output dataset is a SQLite Database, with the following schema:

### schemes

```sql
scheme_code INTEGER PRIMARY_KEY
scheme_name TEXT
```

### funds

```sql
days_since_epoch INTEGER
scheme_code INTEGER
nav FLOAT
FOREIGN KEY (scheme_code) REFERENCES schemes(scheme_code));
```

### securities

```sql
isin TEXT UNIQUE
type INTEGER
scheme_code INTEGER
FOREIGN KEY (scheme_code) REFERENCES schemes(scheme_code));
```

## License

Licensed under the [MIT License](https://nemo.mit-license.org/). See LICENSE file for details.