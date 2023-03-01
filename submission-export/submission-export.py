import argparse
import os
from datetime import datetime
import sys
import time
import csv

import eolymp.universe.universe_pb2 as universe_pb2
import eolymp.judge.judge_pb2 as judge_pb2
import eolymp.judge.submission_pb2 as submission_pb2
import eolymp.wellknown.expression_pb2 as expression_pb2
from eolymp.core.http_client import HttpClient
from eolymp.universe.universe_http import UniverseClient
from eolymp.judge.judge_http import JudgeClient


def timestamp(ts: int):
    return datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')


def verdict(status, percentage):
    if status == submission_pb2.Submission.PENDING:
        return 'PENDING'
    if status == submission_pb2.Submission.TESTING:
        return 'TESTING'
    if status == submission_pb2.Submission.TIMEOUT:
        return 'TIMEOUT'
    if status == submission_pb2.Submission.COMPLETE:
        return 'AC' if percentage == 1 else 'WA'
    if status == submission_pb2.Submission.ERROR:
        return 'CE'
    if status == submission_pb2.Submission.FAILURE:
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
client = HttpClient(token=os.getenv("EOLYMP_TOKEN"))

# lookup space
universe = UniverseClient(client)
try:
    out = universe.LookupSpace(universe_pb2.LookupSpaceInput(key=args.space_key))
    space = out.space
    print("Found space \"{}\"".format(space.name))
except Exception as e:
    print("An error occurred while loading space with key \"{}\": {}".format(args.space_key, e))
    sys.exit(-1)

judge = JudgeClient(client, space.url)

# lookup contest
problems = {}
try:
    out = judge.DescribeContest(judge_pb2.DescribeContestInput(contest_id=args.contest_id))
    contest = out.contest
    print("Found contest \"{}\"".format(contest.name))
    out = judge.ListProblems(judge_pb2.ListProblemsInput(contest_id=args.contest_id))
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
    out = judge.ListParticipants(judge_pb2.ListParticipantsInput(contest_id=contest.id, size=size, offset=offset))
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
    exp = expression_pb2.ExpressionID(value=args.p)
    setattr(exp, "is", expression_pb2.ExpressionID.EQUAL)
    filters['problem_id'] = [exp]

if args.s:
    exp = expression_pb2.ExpressionEnum(value=args.s)
    setattr(exp, "is", expression_pb2.ExpressionEnum.EQUAL)
    filters['status'] = [exp]

if args.u:
    exp = expression_pb2.ExpressionID(value=args.u)
    setattr(exp, "is", expression_pb2.ExpressionID.EQUAL)
    filters['participant_id'] = [exp]

# write header row
writer.writerow(['id', 'participant', 'problem', 'submit_time', 'status', 'score'])

# export submissions
count = 0
offset = 0
size = 25
while True:
    out = judge.ListSubmissions(judge_pb2.ListSubmissionsInput(
        size=size,
        offset=offset,
        contest_id=args.contest_id,
        filters=judge_pb2.ListSubmissionsInput.Filter(**filters)
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
