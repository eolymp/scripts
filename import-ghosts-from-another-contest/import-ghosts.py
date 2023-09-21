import csv
import os
import sys

import eolymp.universe.universe_pb2 as universe_pb2
import eolymp.judge.judge_pb2 as judge_pb2
import eolymp.judge.score_pb2 as score_pb2
import eolymp.community.member_pb2 as member_pb2
from eolymp.community.member_ghost_pb2 import Ghost
from eolymp.community.member_service_http import MemberServiceClient
from eolymp.community.member_service_pb2 import CreateMemberInput
from eolymp.core.http_client import HttpClient
from eolymp.universe.universe_http import UniverseClient
from eolymp.judge.judge_http import JudgeClient

client = HttpClient(token=os.getenv("EOLYMP_TOKEN"))
universe = UniverseClient(client)


def usage():
    print()
    print("USAGE:")
    print("  {} <space-key-from> <space-key-to> <contest-id-from> <contest-id-to>".format(sys.argv[0]))
    print()


def load_space(key):
    try:
        out = universe.LookupSpace(universe_pb2.LookupSpaceInput(key=key))
        space = out.space
        print("Found space \"{}\"".format(space.name))
        return space
    except Exception as e:
        print("An error occurred while loading space with key \"{}\": {}".format(key, e))
        usage()
        sys.exit(-1)


def load_contest(judge, contest_id, mode):
    try:
        problem_dict = {}
        out = judge.DescribeContest(judge_pb2.DescribeContestInput(contest_id=contest_id))
        contest = out.contest
        print("Found contest \"{}\"".format(contest.name))

        out = judge.ListProblems(judge_pb2.ListProblemsInput(contest_id=contest_id))
        for item in out.items:
            print("  - Found problem #{} with index \"{}\"".format(item.id, item.index))
            if mode:
                problem_dict[item.id] = item.index
            else:
                problem_dict[item.index] = item.id
        return contest, problem_dict
    except Exception as e:
        print("An error occurred while loading contest with ID \"{}\": {}".format(contest_id, e))
        usage()
        sys.exit(-1)


def load_participants(judge, contest_id):
    participants = []
    offset = 0
    all_participants = []
    while len(participants) > 0 or offset == 0:
        participants = list(judge.ListParticipants(judge_pb2.ListParticipantsInput(contest_id=contest_id, offset=offset,
                                                                                   size=100)).items)
        offset += 100
        for p in participants:
            all_participants += [(p.id, p.name)]
    return all_participants


# open import file
if len(sys.argv) < 5:
    print("Some parameters are missing")
    usage()
    sys.exit(-1)

space_key_from = sys.argv[1]
space_key_to = sys.argv[2]
contest_id_from = sys.argv[3]
contest_id_to = sys.argv[4]

space_from = load_space(space_key_from)
space_to = load_space(space_key_to)

judge_from = JudgeClient(client, space_from.url)
judge_to = JudgeClient(client, space_to.url)

community_from = MemberServiceClient(client, space_from.url)
community_to = MemberServiceClient(client, space_to.url)

contest_from, problems_from = load_contest(judge_from, contest_id_from, True)
contest_to, problems_to = load_contest(judge_to, contest_id_to, False)

participants = load_participants(judge_from, contest_id_from)

for participant in participants:
    score = judge_from.DescribeScore(judge_pb2.DescribeScoreInput(contest_id=contest_id_from,
                                                                  participant_id=participant[0],
                                                                  mode=score_pb2.Score.LATEST)).score
    scores = []
    problems = []
    for b in score.breakdown:
        if b and b.percentage == 1.0:
            problem = score_pb2.Score.Problem(problem_id=problems_to[problems_from[b.problem_id]], score=b.score,
                                              percentage=b.percentage, attempts=b.attempts, penalty=b.penalty,
                                              solved_in=b.solved_in, solved=True)
            problems += [(b.solved_in, b.problem_id, problem, b)]
    if len(problems) == 0:
        continue
    new_member = member_pb2.Member(ghost=Ghost(name=participant[1]))
    member_id = community_to.CreateMember(CreateMemberInput(member=new_member)).member_id
    participant_id = judge_to.AddParticipant(judge_pb2.AddParticipantInput(contest_id=contest_id_to,
                                                                           member_id=member_id,
                                                                           name=participant[1])).participant_id
    problems.sort()
    problem_list = []
    total_score = 0
    total_penalty = 0
    for p in problems:
        b = p[3]
        problem_list += [p[2]]
        total_score += b.score
        total_penalty += b.penalty
        scores += [score_pb2.Score(valid_after=b.solved_in, score=total_score, penalty=total_penalty,
                                   breakdown=problem_list)]

    result = judge_to.ImportScore(judge_pb2.ImportScoreInput(contest_id=contest_id_to, participant_id=participant_id,
                                                             scores=scores))
    print(participant[1], "was added")
