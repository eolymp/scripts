import csv
import os

import eolymp.universe.universe_pb2 as universe_pb2
import eolymp.community.member_pb2 as member_pb2
import eolymp.community.community_pb2 as community_pb2
import eolymp.cognito.cognito_pb2 as cognito_pb2
import eolymp.wellknown.expression_pb2 as expression_pb2
from eolymp.core.http_client import HttpClient
from eolymp.universe.universe_http import UniverseClient
from eolymp.community.community_http import CommunityClient
from eolymp.cognito.cognito_http import CognitoClient

client = HttpClient(token=os.getenv("EOLYMP_TOKEN"))
universe = UniverseClient(client)
cognito = CognitoClient(client)
lookup = universe.LookupSpace(universe_pb2.LookupSpaceInput(key=os.getenv("EOLYMP_SPACE")))
community = CommunityClient(client, lookup.space.url)


def get_members_map():
    mm = {}
    offset = 0

    while True:
        listing = community.ListMembers(community_pb2.ListMembersInput(offset=offset, size=100))
        for item in listing.items:
            print("Reading existing member \"{}\" with ID {}".format(item.name, item.id))
            mm[item.name] = item

        offset += len(listing.items)
        if offset >= listing.total:
            break

    return mm


def identity_with_password(name, password):
    return member_pb2.Member.Identity(
        issuer=lookup.space.url,
        nickname=name,
        password=password
    )


def identity_with_user_id(name, user_id):
    return member_pb2.Member.Identity(
        issuer="https://accounts.eolymp.com",
        subject=user_id,
    )


def identity_with_username(name, username):
    expr = expression_pb2.ExpressionString(value=username)
    setattr(expr, 'is', expression_pb2.ExpressionString.EQUAL)

    out = cognito.ListUsers(cognito_pb2.ListUsersInput(filters=cognito_pb2.ListUsersInput.Filter(
        username=[expr]
    )))

    if len(out.items) == 0:
        raise Exception("Eolymp user with username \"{}\" does not exist".format(username))

    print("Username \"{}\" resolved to ID {}".format(username, out.items[0].id))

    return identity_with_user_id(name, out.items[0].id)


# open import file
file = open("members.csv")
reader = csv.reader(file)
header = next(reader)

# validate header
if "name" not in header:
    raise Exception("CSV file must contain column \"name\" with member's name")

if "password" not in header and "eolymp_user_id" not in header and "eolymp_username" not in header:
    raise Exception(
        "CSV file must contain one of columns identifying user: \"password\", \"eolymp_username\" or \"eolymp_user_id\"")

members = get_members_map()

for row in reader:
    data = dict(zip(header, row))

    # define identity
    if "password" in data and data["password"]:
        identity = identity_with_password(data["name"], data["password"])
    elif "eolymp_user_id" in data and data["eolymp_user_id"]:
        identity = identity_with_user_id(data["name"], data["eolymp_user_id"])
    elif "eolymp_username" in data and data["eolymp_username"]:
        identity = identity_with_username(data["name"], data["eolymp_username"])
    else:
        raise Exception("Unable to create identity for member \"{}\"".format(data["name"]))

    # member with given name already exists, updating...
    if data["name"] in members:
        member = members[data["name"]]
        community.UpdateMember(community_pb2.UpdateMemberInput(
            member_id=member.id,  # member to update
            patch=[community_pb2.UpdateMemberInput.IDENTITIES],  # only update identities
            member=member_pb2.Member(identities=[identity])  # changes
        ))

        print("Member {} has been updated".format(member.id))
    else:
        out = community.AddMember(community_pb2.AddMemberInput(
            member=member_pb2.Member(name=data["name"], identities=[identity])
        ))

        print("Member {} has been added".format(out.member_id))