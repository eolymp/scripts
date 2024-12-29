import argparse
import os
from datetime import datetime
import sys
import csv
import requests

import eolymp.core
import eolymp.universe
import eolymp.judge
import eolymp.wellknown


def timestamp(ts: int):
    return datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')


def verdict_label(status, verdict):
    if status == eolymp.atlas.Submission.PENDING:
        return 'PENDING'
    if status == eolymp.atlas.Submission.TESTING:
        return 'TESTING'
    if status == eolymp.atlas.Submission.TIMEOUT:
        return 'TIMEOUT'
    if status == eolymp.atlas.Submission.COMPLETE:
        if verdict == eolymp.atlas.Submission.ACCEPTED:
            return 'AC'
        if verdict == eolymp.atlas.Submission.WRONG_ANSWER:
            return 'WA'
        if verdict == eolymp.atlas.Submission.TIME_LIMIT_EXCEEDED:
            return 'TL'
        if verdict == eolymp.atlas.Submission.CPU_EXHAUSTED:
            return 'TL'
        if verdict == eolymp.atlas.Submission.MEMORY_OVERFLOW:
            return 'MO'
        if verdict == eolymp.atlas.Submission.RUNTIME_ERROR:
            return 'RE'
        return 'UNKNOWN'
    if status == eolymp.atlas.Submission.ERROR:
        return 'CE'
    if status == eolymp.atlas.Submission.FAILURE:
        return 'FAILURE'

def download_source(url, path):
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)

        resp = requests.get(url)
        resp.raise_for_status()  # Raise an error for bad responses (4xx or 5xx)

        with open(path, 'wb') as f:
            f.write(resp.content)

    except requests.exceptions.RequestException as e:
        print(f"Error downloading the file: {e}")

def runtime_ext(runtime):
    lang = runtime.split(':')[0]
    if lang == 'python':
        return 'py'
    if lang == 'pascal':
        return 'pas'
    if lang == 'csharp':
        return 'cs'
    if lang == 'haskell':
        return 'hs'
    if lang == 'javascript':
        return 'js'
    if lang == 'kotlin':
        return 'kt'
    if lang == 'mysql':
        return 'sql'
    if lang == 'plain':
        return 'txt'
    if lang == 'ruby':
        return 'rb'
    if lang == 'rust':
        return 'rs'
    return lang


parser = argparse.ArgumentParser(
    prog='submission-export',
    description='Export contest submissions in a CSV table',
    epilog='See more at https://github.com/eolymp/scripts/blob/main/submission-export/README.md')

parser.add_argument('-x', '--source', help="Download source files to a given path", dest='source')
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
universe = eolymp.universe.SpaceServiceClient(client)
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
    index = 0
    for item in out.items:
        print("  - Found problem #{}".format(item.id))
        index = index+1
        item.index = index
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
        filters=eolymp.judge.ListSubmissionsInput.Filter(**filters),
        extra=[eolymp.judge.Submission.SOURCE]
    ))

    count += len(out.items)

    for item in out.items:
        print(
            "  Exporting submission #{}: problem {}, participant {}, status {}, score: {}".
            format(item.id, item.problem_id, item.participant_id, item.status, item.score)
        )

        letter = chr(ord('A') + problems[item.problem_id].index - 1) if item.problem_id in problems else '?'

        writer.writerow([
            item.id,
            participants[item.participant_id].display_name if item.participant_id in participants else item.participant_id,
            letter,
            timestamp(item.submitted_at.seconds),
            verdict_label(item.status, item.verdict),
            item.score,
        ])

        if args.source:
            dest = args.source + "/" + participants[item.participant_id].display_name + "/" + letter +"_" + item.id + "." + runtime_ext(item.lang)
            print("  Downloading source {} to {}".format(item.source_url, dest))
            download_source(item.source_url, dest)


    offset += size

    if out.total < offset:
        break

file.close()

print("{} submissions has been exported to {}".format(count, args.output))
