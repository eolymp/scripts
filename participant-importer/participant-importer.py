import csv
import argparse
import os
import sys

import eolymp.core
import eolymp.universe
import eolymp.judge
import eolymp.community
import eolymp.wellknown

parser = argparse.ArgumentParser(
    prog='participant-importer',
    description='Add space members as participants to a contest from a CSV list of display names',
    epilog='See more at https://github.com/eolymp/scripts/blob/main/participant-importer/README.md')

parser.add_argument('--unofficial', action='store_true', help="Add participants as unofficial")
parser.add_argument('--inactive', action='store_true', help="Add participants as inactive")

parser.add_argument('space_key', help="Space Key")
parser.add_argument('contest_id', help="Contest ID")
parser.add_argument('input', help="CSV file with a 'display_name' column")

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

# lookup contest
contests = eolymp.judge.ContestServiceClient(client, space.url)
try:
    out = contests.DescribeContest(eolymp.judge.DescribeContestInput(contest_id=args.contest_id))
    contest = out.contest
    print("Found contest \"{}\"".format(contest.name))
except Exception as e:
    print("An error occurred while loading contest with ID \"{}\": {}".format(args.contest_id, e))
    sys.exit(-1)

participants_svc = eolymp.judge.ParticipantServiceClient(client, contest.url)
member_svc = eolymp.community.MemberServiceClient(client, space.url)

# load all members into a map indexed by display name
print("Loading space members...")
members_by_name = {}
offset = 0
size = 100
while True:
    listing = member_svc.ListMembers(eolymp.community.ListMembersInput(size=size, offset=offset))
    for m in listing.items:
        members_by_name[m.display_name.strip()] = m
    offset += size
    if listing.total <= offset:
        break

print("Loaded {} member(s) from space".format(len(members_by_name)))


# read CSV
file = open(args.input)
reader = csv.DictReader(file)

rows = list(reader)
print("Loaded {} row(s) from CSV".format(len(rows)))

count = 0
for row in rows:
    display_name = row.get("display_name", "").strip()
    if not display_name:
        print("  WARNING: empty display_name, skipping")
        continue

    try:
        member = members_by_name.get(display_name)
        if member is None:
            print("  ERROR: Member \"{}\" not found in space".format(display_name))
            continue

        participants_svc.AssignParticipant(eolymp.judge.AssignParticipantInput(
            member_id=member.id,
            unofficial=args.unofficial,
            inactive=args.inactive,
        ))
        print("  Added \"{}\" (member #{}) as participant".format(display_name, member.id))
        count += 1
    except Exception as e:
        if "409" in str(e):
            print("  Skipped \"{}\" (already a participant)".format(display_name))
        else:
            print("  ERROR: Failed to add \"{}\": {}".format(display_name, e))

print("{} participant(s) added".format(count))
