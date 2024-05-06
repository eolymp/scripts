import argparse
import os
from datetime import datetime
import sys

import eolymp.core
import eolymp.universe
import eolymp.judge


def timestamp(ts: int):
    return datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')


parser = argparse.ArgumentParser(
    prog='plagiarism-check',
    description='Plagiarism check',
    epilog='See more at https://github.com/eolymp/scripts/blob/main/plagiarism-check/README.md')

parser.add_argument('space_key', help="Space Key")
parser.add_argument('contest_id', help="Contest ID")

args = parser.parse_args()
client = eolymp.core.HttpClient(token=os.getenv("EOLYMP_TOKEN"))

# lookup space
spaces = eolymp.universe.SpaceServiceClient(client)
try:
    out = spaces.LookupSpace(eolymp.universe.LookupSpaceInput(key=args.space_key))
    space = out.space
    print("Found space \"{}\"".format(space.name))
except Exception as e:
    print("An error occurred while loading space with key \"{}\": {}".format(args.space_key, e))
    sys.exit(-1)

# export submissions
count = 0
offset = 0
size = 25
while True:
    out = eolymp.judge.SubmissionServiceClient(client, space.url).ListSubmissions(eolymp.judge.ListSubmissionsInput(
        size=size,
        offset=offset,
        contest_id=args.contest_id,
        filters=eolymp.judge.ListSubmissionsInput.Filter()
    ))

    count += len(out.items)

    for item in out.items:
        print(
            "  Exporting submission #{}: problem {}, participant {}, status {}, score: {}".
            format(item.id, item.problem_id, item.participant_id, item.status, item.score)
        )

    offset += size

    if out.total < offset:
        break
