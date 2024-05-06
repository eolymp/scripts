import csv
import os
import sys

import eolymp.core
import eolymp.universe
import eolymp.community
import eolymp.judge
import eolymp.wellknown

client = eolymp.core.HttpClient(token=os.getenv("EOLYMP_TOKEN"))
universe = eolymp.universe.UniverseClient(client)


def usage():
    print()
    print("USAGE:")
    print("  {} <space-key> <member-id> <contest-id> <score-csv-file>".format(sys.argv[0]))
    print()
    print("See more at https://github.com/eolymp/scripts/blob/main/import-ghost-score/README.md")
    print()


def validate_header(header):
    if "time_offset" not in header:
        raise Exception("CSV file must contain column \"time_offset\" with time when score was set, time should be "
                        "set in number of seconds since the beginning of the contest")

    if "total_score" not in header:
        raise Exception("CSV file must contain column \"total_score\" with total number of points scored by "
                        "participant (for ICPC, equals to number of problems)")


# open import file
if len(sys.argv) < 5:
    print("Some parameters are missing")
    usage()
    sys.exit(-1)

space_key = sys.argv[1]
member_id = sys.argv[2]
contest_id = sys.argv[3]
score_file = sys.argv[4]

# lookup space
try:
    out = universe.LookupSpace(eolymp.universe.LookupSpaceInput(key=space_key))
    space = out.space
    print("Found space \"{}\"".format(space.name))
except Exception as e:
    print("An error occurred while loading space with key \"{}\": {}".format(space_key, e))
    usage()
    sys.exit(-1)

judge = eolymp.judge.JudgeClient(client, space.url)
community = eolymp.community.MemberServiceClient(client, space.url)

# lookup contest
problem_index_to_id = {}

try:
    out = judge.DescribeContest(eolymp.judge.DescribeContestInput(contest_id=contest_id))
    contest = out.contest
    print("Found contest \"{}\"".format(contest.name))

    out = judge.ListProblems(eolymp.judge.ListProblemsInput(contest_id=contest_id))
    for item in out.items:
        print("  - Found problem #{} with index \"{}\"".format(item.id, item.index))
        problem_index_to_id[item.index] = item.id
except Exception as e:
    print("An error occurred while loading contest with ID \"{}\": {}".format(contest_id, e))
    usage()
    sys.exit(-1)


# lookup member
try:
    out = community.DescribeMember(eolymp.community.DescribeMemberInput(member_id=member_id))
    member = out.member
    print("Found member \"{}\"".format(member.name))
except Exception as e:
    print("An error occurred while loading member with ID \"{}\": {}".format(member_id, e))
    usage()
    sys.exit(-1)


# lookup participant
try:
    match = eolymp.wellknown.ExpressionID(value=member_id)
    setattr(match, "is", eolymp.wellknown.ExpressionID.EQUAL)

    out = judge.ListParticipants(eolymp.judge.ListParticipantsInput(contest_id=contest_id, filters=eolymp.judge.ListParticipantsInput.Filter(member_id=[match])))
    if len(out.items) > 0:
        participant = out.items[0]
        print("Found participant \"{}\"".format(participant.name))
        participant_id = participant.id
    else:
        print("Member is not participating in the contest, adding...")
        out = judge.AddParticipant(eolymp.judge.AddParticipantInput(contest_id=contest_id, participant=eolymp.judge.Participant(member_id=member_id)))
        print("Participant #{} created".format(out.participant_id))
        participant_id = out.participant_id

except Exception as e:
    print("An error occurred while loading contest with ID \"{}\": {}".format(contest_id, e))
    usage()
    sys.exit(-1)


# open score file
try:
    file = open(score_file)
    reader = csv.reader(file)
except Exception as e:
    print("An error occurred while reading score file \"{}\": {}".format(score_file, e))
    usage()
    sys.exit(-1)

# validate header
header = next(reader)
try:
    validate_header(header)
except Exception as e:
    print("Score file \"{}\" has invalid format: {}".format(score_file, e))
    usage()
    sys.exit(-1)


# read scores
scores = []

for row in reader:
    data = dict(zip(header, row))

    if "total_score" not in data:
        continue

    score = eolymp.judge.Score(valid_after=int(data["time_offset"]), score=int(data["total_score"]))
    if "total_penalty" in data:
        score.penalty = int(data["total_penalty"])

    for index in problem_index_to_id:
        prefix = "p" + str(index)
        if prefix + "_score" not in data:
            continue

        breakdown = eolymp.judge.Score.Problem(problem_id=problem_index_to_id[index], score=int(data[prefix + "_score"]))
        if prefix + "_penalty" in data:
            breakdown.penalty = int(data[prefix + "_penalty"])
        if prefix + "_percentage" in data:
            breakdown.percentage = float(data[prefix + "_percentage"])
        if prefix + "_attempts" in data:
            breakdown.attempts = int(data[prefix + "_attempts"])
        if prefix + "_solved_in" in data:
            breakdown.solved_in = int(data[prefix + "_solved_in"])

        score.breakdown.append(breakdown)

    scores.append(score)

# import score
try:
    judge.ImportScore(eolymp.judge.ImportScoreInput(contest_id=contest_id, participant_id=participant_id, scores=scores))
except Exception as e:
    print("An error occurred while importing score: {}".format(e))
    sys.exit(-1)

print("{} score records are imported".format(len(scores)))
