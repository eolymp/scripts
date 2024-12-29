import argparse
import os
import sys
import time

import eolymp.wellknown
import eolymp.core
import eolymp.universe
import eolymp.judge

parser = argparse.ArgumentParser(
    prog='submission-rejudge',
    description='Trigger rejudge on the contest submissions',
    epilog='See more at https://github.com/eolymp/scripts/blob/main/submission-rejudge/README.md')

parser.add_argument('-p', metavar="PROBLEM-ID", help="Only rejudge submissions for a given problem")
parser.add_argument('-u', metavar="PARTICIPANT-ID", help="Only rejudge submissions for a given participant")
parser.add_argument('-s', metavar="STATUS",
                    help="Only rejudge submissions in a given status: 'PENDING', 'TESTING', 'TIMEOUT', 'ERROR', 'FAILURE', 'COMPLETE'",
                    choices=['PENDING', 'TESTING', 'TIMEOUT', 'ERROR', 'FAILURE', 'COMPLETE'])

parser.add_argument('space_key', help="Space Key")
parser.add_argument('contest_id', help="Contest ID")

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
try:
    out = judge.DescribeContest(eolymp.judge.DescribeContestInput(contest_id=args.contest_id))
    contest = out.contest
    print("Found contest \"{}\"".format(contest.name))
except Exception as e:
    print("An error occurred while loading contest with ID \"{}\": {}".format(args.contest_id, e))
    sys.exit(-1)

# rejudge
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
            "  Rejudging submission #{}: problem {}, participant {}, status {}, score: {}".
            format(item.id, item.problem_id, item.participant_id, item.status, item.score)
        )

        try:
            judge.RetestSubmission(eolymp.judge.RetestSubmissionInput(contest_id=contest.id, submission_id=item.id))

            # waiting a little not to overwhelm system with too many submissions
            time.sleep(1)

        except Exception as e:
            print("  ERROR: Rejudge failed {}".format(e))

    offset += size

    if out.total < offset:
        break


print("Rejudge on {} submissions has been started".format(count))
