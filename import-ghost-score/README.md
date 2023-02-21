# Ghost Score Import

This script allows to import score records for "Ghost" members.

Ghosts are special member accounts which do not allow to login or participate in competitions but appear on the scoreboards. These are useful in the upsolve or mirrored competitions to display results of actual participants and allow others to compete with them. 

You can create ghost member at Eolymp Console: https://console.eolymp.com. When adding a new member to the space check "This member is a ghost" toggle and follow process as usual.

Once you have Ghost account you can import score for each competition using this script. 

## Usage

First, you need to create a CSV file with the score for each Ghost account. The score can be imported as historical data, ie. you can specify different score during each moment in competition to reflect progress. If you don't want to import historical data, you can simply import a single record with time offset equal to 0.

The CSV should have the following columns:
- **time_offset** - time when the score was recorded, specified in seconds since beginning of the competition (for example, 600 means the records reflects score at 00:10:00 of participation)
- **total_score** - total score at the moment in time (suppose to be sum of scores in the breakdown, but not enforced)
- **total_penalty** - total penalty at the moment in time (suppose to be sum of penalty in the breakdown, but not enforced)

Additionally, you have to specify score breakdown by problem using these columns:
- **p`<index>`_score** - score as defined by contest format (for IOI: from 0 to 100, for ICPC 0 or 1). **This column is required for each problem**
- **p`<index>`_penalty** - penalty as defined by contest format (for ICPC: `solved_in/60 + attempts*20`)
- **p`<index>`_percentage** - percentage of scored points from 0 to 1 (1 means 100% or fully solved), this value does not depend on contest format
- **p`<index>`_attempts** - number of attempts to solve problem before successful attempt
- **p`<index>`_solved_in** - time in second to solve problem, since participant started contest, leave as 0 if not solved

The porting marked as `<index>` should be replaced with problem index in the contest.

An example of CSV file for IOI contest with two problems:

```csv
time_offset,total_score,p1_score,p1_percentage,p2_score,p2_percentage
0,0,0,0,0,0
300,50,50,0.5,0,0
600,100,100,1,0,0
900,200,100,1,100,1
```

In this example, participant solved first problem at 50% at 00:05:00, then at 00:10:00 she solved the problem fully (100%) and at 00:15:00 solved second problem, getting final result of 200 points.

An example of CSV file for ICPC contest with two problems:

```csv
time_offset,total_score,total_penalty,p1_score,p1_penalty,p1_percentage,p1_attempts,p1_solved_in,p2_score,p2_penalty,p2_percentage,p2_attempts,p2_solved_in
300,0, 0,0, 0,0.5,1,0,0,0,0,0,0
600,1,30,1,30,1,1,600,0,0,0,0,0
900,2,45,1,30,1,1,600,1,15,1,0,900
```

In this example, participant solved first problem at 50% at 00:05:00, then at 00:10:00 she solved the problem fully (100%) and at 00:15:00 solved second problem, getting final result of 2 points with penalty of 45.

Once you have prepared CSV file you have to save it and import it using `import-members.py` script. Execute script passing these parameters:

- **space-key** - the key (not ID) for the space where contest and member are created
- **contest-id** - contest where results should be imported
- **member-id** - Ghost's member ID
- **score-file** - path to the CSV file with score

The script requires environment variable `EOLYMP_TOKEN` with API key or your access token.

Execute script:

```shell
$ EOLYMP_TOKEN=etkn-... python import-ghost-score.py myscope uipaf4h3n17518piqm2l627k2o fhodsfv0ld4ev1dssprh4n8bqs score.scv
Found space "Eolymp"
Found contest "Round A"
  - Found problem #8dm3sdtn5l70f7fp49gem5p9d8 with index "1"
  - Found problem #4m0ma824rt6vp9o6q1ffjadg0o with index "2"
Found member "ghoster"
Found participant "ghoster"
141 score records are imported
```
