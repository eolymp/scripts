import argparse
import os
from datetime import datetime
import sys
import time
import csv

import eolymp.core
import eolymp.universe
import eolymp.judge
import eolymp.wellknown


def timestamp(ts: int):
    return datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')


def verdict(status, percentage):
    if status == eolymp.judge.Submission.PENDING:
        return 'PENDING'
    if status == eolymp.judge.Submission.TESTING:
        return 'TESTING'
    if status == eolymp.judge.Submission.TIMEOUT:
        return 'TIMEOUT'
    if status == eolymp.judge.Submission.COMPLETE:
        return 'AC' if percentage == 1 else 'WA'
    if status == eolymp.judge.Submission.ERROR:
        return 'CE'
    if status == eolymp.judge.Submission.FAILURE:
        return 'FAILURE'


parser = argparse.ArgumentParser(
    prog='submission-export',
    description='Export contest submissions in a CSV table',
    epilog='See more at https://github.com/eolymp/scripts/blob/main/submission-export/README.md')

parser.add_argument('-p', metavar="PROBLEM-ID", help="Only export submissions for a given problem")
parser.add_argument('-u', metavar="PARTICIPANT-ID", help="Only export submissions for a given participant")
parser.add_argument('-s', metavar="STATUS",
                    help="Only export submissions in a given status: 'PENDING', 'TESTING', 'TIMEOUT', 'ERROR', 'FAILURE', 'COMPLETE'",
                    choices=['PENDING', 'TESTING', 'TIMEOUT', 'ERROR', 'FAILURE', 'COMPLETE'])

parser.add_argument('space_key', help="Space Key")
parser.add_argument('contest_id', help="Contest ID")
parser.add_argument('output', help="Output file")

args = parser.parse_args()
client = eolymp.core.HttpClient(token=os.getenv("EOLYMP_TOKEN"))

# lookup space
universe = eolymp.universe.UniverseClient(client)
try:
    out = universe.LookupSpace(eolymp.universe.LookupSpaceInput(key=args.space_key))
    space = out.space
    print("Found space \"{}\"".format(space.name))
except Exception as e:
    print("An error occurred while loading space with key \"{}\": {}".format(args.space_key, e))
    sys.exit(-1)

judge = eolymp.judge.JudgeClient(client, space.url)

# lookup contest
problems = {}
try:
    out = judge.DescribeContest(eolymp.judge.DescribeContestInput(contest_id=args.contest_id))
    contest = out.contest
    print("Found contest \"{}\"".format(contest.name))
    out = judge.ListProblems(eolymp.judge.ListProblemsInput(contest_id=args.contest_id))
    for item in out.items:
        print("  - Found problem #{}".format(item.id))
        problems[item.id] = item
except Exception as e:
    print("An error occurred while loading contest with ID \"{}\": {}".format(args.contest_id, e))
    sys.exit(-1)

# load participants
participants = {}

offset = 0
size = 100
while True:
    out = judge.ListParticipants(eolymp.judge.ListParticipantsInput(contest_id=contest.id, size=size, offset=offset))
    for item in out.items:
        participants[item.id] = item

    offset += size

    if out.total < offset:
        break

# open export file
file = open(args.output, 'w', encoding='UTF8', newline='\n')
writer = csv.writer(file)

# compose submission filters
filters = {}
if args.p:
    exp = eolymp.wellknown.ExpressionID(value=args.p)
    setattr(exp, "is", eolymp.wellknown.ExpressionID.EQUAL)
    filters['problem_id'] = [exp]

if args.s:
    exp = eolymp.wellknown.ExpressionEnum(value=args.s)
    setattr(exp, "is", eolymp.wellknown.ExpressionEnum.EQUAL)
    filters['status'] = [exp]

if args.u:
    exp = eolymp.wellknown.ExpressionID(value=args.u)
    setattr(exp, "is", eolymp.wellknown.ExpressionID.EQUAL)
    filters['participant_id'] = [exp]

# write header row
writer.writerow(['id', 'participant', 'problem', 'submit_time', 'status', 'score'])

# export submissions
count = 0
offset = 0
size = 25
while True:
    out = judge.ListSubmissions(eolymp.judge.ListSubmissionsInput(
        size=size,
        offset=offset,
        contest_id=args.contest_id,
        filters=eolymp.judge.ListSubmissionsInput.Filter(**filters)
    ))

    count += len(out.items)

    for item in out.items:
        print(
            "  Exporting submission #{}: problem {}, participant {}, status {}, score: {}".
            format(item.id, item.problem_id, item.participant_id, item.status, item.score)
        )

        writer.writerow([
            item.id,
            participants[item.participant_id].name if item.participant_id in participants else item.participant_id,
            chr(ord('A') + problems[item.problem_id].index - 1) if item.problem_id in problems else '?',
            timestamp(item.submitted_at.seconds),
            verdict(item.status, item.percentage),
            item.score,
        ])

    offset += size

    if out.total < offset:
        break

file.close()
print("{} submissions has been exported to {}".format(count, args.output))
