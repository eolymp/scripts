# Import Contest Results

This script allows to import contest results for the contest archive at https://basecamp.eolymp.com/contests.

It takes an CSV file with official results of the competition, adds contestants as ghosts to contest at Eolymp and sets their final score.

**This script currently only imports IOI results.**

## Install

The script requires latest `eolymp`, `protobuf` and `requests` packages from Python package repository.

Install them using `pip`:

```sh
pip install eolymp protobuf requests
```

## Usage

First, you need to create a CSV file with the results. 

The CSV should have the following columns:
- **name** - contestants name
- **p`<index>`_score** - score for a problem with given `<index>` 
- **medal** - optional medal given to the contestant, possible values are: GOLD, SILVER, BRONZE. 

An example of CSV file for IOI contest with two problems:

| name     | p1_score | p2_score | medal  |
|----------|----------|----------|--------|
| Jane Doe | 100      | 100      | GOLD   |
| John Foe | 100      | 0        | SILVER |
| Mark Moe | 0        | 0        |        |

Once you have prepared CSV file you have to save it and import it using `import-contest-results.py` script. Execute script passing these parameters:

- **space-key** - the key (not ID) for the space where contest and member are created
- **contest-id** - contest where results should be imported. You can copy this value from console URL, for example a contest https://console.eolymp.com/basecamp/contests/123, has contest-id = 123.

The script requires environment variable `EOLYMP_TOKEN` with API key or your access token. To get an API key you can use https://developer.eolymp.com, the key must have all `judge:` scopes. 

Execute script:

```shell
$ export EOLYMP_TOKEN=etkn-... 
$ python import-contest-results.py myscope fhodsfv0ld4ev1dssprh4n8bqs score.scv
```
