import csv
import os
import sys

import eolymp.universe
import eolymp.judge
import eolymp.wellknown
import eolymp.core
import eolymp.universe
import eolymp.judge

client = eolymp.core.HttpClient(token=os.getenv("EOLYMP_TOKEN"))
universe = eolymp.universe.UniverseClient(client)


def usage():
    print()
    print("USAGE:")
    print("  {} <space-key> <contest-id> <score-csv-file>".format(sys.argv[0]))
    print()
    print("See more at https://github.com/eolymp/scripts/blob/main/basecamp/import-contest-results/README.md")
    print()


def validate_header(header):
    if "name" not in header:
        raise Exception("CSV file must contain column \"name\"")


# open import file
if len(sys.argv) < 4:
    print("Some parameters are missing")
    usage()
    sys.exit(-1)

space_key = sys.argv[1]
contest_id = sys.argv[2]
score_file = sys.argv[3]

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

    name = data["name"]

    if not name:
        continue

    expr = eolymp.wellknown.ExpressionString(value=name)
    expr.__setattr__('is', eolymp.wellknown.ExpressionString.EQUAL)

    out = judge.ListParticipants(eolymp.judge.ListParticipantsInput(
        contest_id=contest_id,
        filters=eolymp.judge.ListParticipantsInput.Filter(name=[expr]),
    ))

    participant_id = None

    if len(out.items) == 0:
        print("Participant {} does not exists, adding...".format(name))

        out = judge.AssignParticipant(eolymp.judge.AssignParticipantInput(contest_id=contest_id, participant=eolymp.judge.Participant(
            name=name,
            ghost=True,
        )))

        participant_id = out.participant_id

    elif len(out.items) > 1:
        print("Multiple participants named {}, skipping...".format(name))
        continue

    elif len(out.items) == 1:
        if not out.items[0].ghost:
            print("Participant {} is not a ghost, skipping...".format(name))
            continue

        participant_id = out.items[0].id

    score = eolymp.judge.Score(valid_after=int(0), score=int(0))
    for index in problem_index_to_id:
        prefix = "p" + str(index)
        if prefix + "_score" not in data:
            continue

        breakdown = eolymp.judge.Score.Problem(problem_id=problem_index_to_id[index], percentage=float(data[prefix + "_score"])/100, score=float(data[prefix + "_score"]))
        score.breakdown.append(breakdown)
        score.score += breakdown.score

    print("Import total score {} for {}...".format(score.score, participant_id))

    try:
        judge.ImportScore(eolymp.judge.ImportScoreInput(contest_id=contest_id, participant_id=participant_id, scores=[score]))
    except Exception as e:
        print("An error occurred while importing score: {}".format(e))
        sys.exit(-1)

    if "medal" in data:
        medal = eolymp.judge.NO_MEDAL
        if data["medal"] == "GOLD" or  data["medal"] == "Gold":
            medal = eolymp.judge.GOLD_MEDAL
        if data["medal"] == "SILVER" or data["medal"] == "Silver":
            medal = eolymp.judge.SILVER_MEDAL
        if data["medal"] == "BRONZE" or data["medal"] == "Bronze":
            medal = eolymp.judge.BRONZE_MEDAL

        judge.UpdateParticipant(eolymp.judge.UpdateParticipantInput(
            contest_id=contest_id,
            participant_id=participant_id,
            participant=eolymp.judge.Participant(medal=medal, name=name),
            patch=[eolymp.judge.UpdateParticipantInput.MEDAL,eolymp.judge.UpdateParticipantInput.NAME],
        ))
