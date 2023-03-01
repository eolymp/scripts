# Submission Exporter

This script allows to automatically export contest submissions. Using additional command line arguments you can filter submissions by problem, status or participant.

## Usage

This script requires environment variable `EOLYMP_TOKEN` with an API key or your access token.

Execute script with `space-key`, `contest-id` and `output-filename` arguments.

```shell
$ EOLYMP_TOKEN=etkn-... python submission-export.py myspace top8k2v97t2rt02qudo17jnu9o submissions.csv
```

The script will produce file `submissions.csv` with a list of submissions in the following format (spaces are added for readability):

```
id,                        participant,problem,submit_time,        status,score
24jt39fb891d182tkg9785t27c,sergey     ,A      ,2022-12-28 19:11:49,WA,    0.0
6qtutrt5a14snceb2i8ba8cthc,sergey     ,A      ,2022-12-28 19:11:31,AC,    100.0
```

Additionally, you can filter submissions by providing additional arguments:

- `-p` - only export submissions for a given problem
- `-u` - only export submissions for a given participant
- `-s` - only export submissions with a given status
  - `PENDING` - submission is pending to be judged
  - `TESTING` - submission is being judged
  - `TIMEOUT` - submission judging took too long and has been interrupted
  - `ERROR`- compilation error (or other user caused error)
  - `FAILURE` - system error (for example, checker failure)
  - `COMPLETE` - submission judged successfully (this includes both Accepted and Wrong Answer verdicts)

Execute script with additional arguments:

```shell
$ EOLYMP_TOKEN=etkn-... python submission-export.py myspace top8k2v97t2rt02qudo17jnu9o submissions.csv \
  -p be0te2e9md1an67n62oooumsms \
  -u 1dsdhgcesl1jfeucf7fiu923i6 \
  -s FAILURE
```
