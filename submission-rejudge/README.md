# Rejudge submissions

This script allows to automatically trigger rejudge on contest submissions. Using additional command line arguments you can rejudge submissions by problem, status or participant.

The script only triggers rejudge, after it finishes it will take some time for system to perform rejudge and report new verdict. Be patient, on large contests rejudge can take long time.

After rejudge you may want to rebuild contest scoreboard and any additional scoreboards to get them up-to-date.

## Usage

This script requires environment variable `EOLYMP_TOKEN` with an API key or your access token.

Execute script with `space-key` and `contest-id` arguments to rejudge all submissions in the contest.

```shell
$ EOLYMP_TOKEN=etkn-... python submission-rejudge.py myspace top8k2v97t2rt02qudo17jnu9o
```

You can reduce number of submissions to rejudge (thus making things faster) by providing additional arguments:

- `-p` - only rejudge submissions for a given problem
- `-u` - only rejudge submissions for a given participant
- `-s` - only rejudge submissions with a given status
  - `PENDING` - submission is pending to be judged
  - `TESTING` - submission is being judged
  - `TIMEOUT` - submission judging took too long and has been interrupted
  - `ERROR`- compilation error (or other user caused error)
  - `FAILURE` - system error (for example, checker failure)
  - `COMPLETE` - submission judged successfully (this includes both Accepted and Wrong Answer verdicts)

Execute script with additional arguments:

```shell
$ EOLYMP_TOKEN=etkn-... python submission-rejudge.py myspace top8k2v97t2rt02qudo17jnu9o \
  -p be0te2e9md1an67n62oooumsms \
  -u 1dsdhgcesl1jfeucf7fiu923i6 \
  -s FAILURE
```
