import csv
import os
import argparse

import eolymp.universe
import eolymp.community
import eolymp.cognito
import eolymp.wellknown
import eolymp.core


parser = argparse.ArgumentParser(
    prog='import-members',
    description='Import members from a CSV table',
    epilog='See more at https://github.com/eolymp/scripts/blob/main/import-members/README.md')

parser.add_argument('space_key', help="Space Key")
parser.add_argument('input', help="CSV table with members")

args = parser.parse_args()

client = eolymp.core.HttpClient(token=os.getenv("EOLYMP_TOKEN"))
space_svc = eolymp.universe.SpaceServiceClient(client)
user_svc = eolymp.cognito.UserServiceClient(client)
lookup = space_svc.LookupSpace(eolymp.universe.LookupSpaceInput(key=args.space_key))
member_svc = eolymp.community.MemberServiceClient(client, lookup.space.url)
attribute_svc = eolymp.community.AttributeServiceClient(client, lookup.space.url)

# load existing members into a map indexed by nickname
def get_members_map():
    mm = {}
    offset = 0

    while True:
        listing = member_svc.ListMembers(eolymp.community.ListMembersInput(offset=offset, size=100))
        for item in listing.items:
            if not item.user:
                continue

            print("Reading existing member \"{}\" with ID {}".format(item.user.nickname, item.id))
            mm[item.user.nickname] = item

        offset += len(listing.items)
        if offset >= listing.total:
            break

    return mm

# load existing attributes into a map indexed by key
def get_attribute_map():
    mm = {}
    offset = 0

    while True:
        listing = attribute_svc.ListAttributes(eolymp.community.ListAttributesInput(offset=offset, size=100))
        for item in listing.items:
            print("Reading attribute \"{}\"".format(item.key))
            mm[item.key] = item

        offset += len(listing.items)
        if offset >= listing.total:
            break

    return mm

# resolve Eolymp username to ID
def resolve_username(username):
    expr = eolymp.wellknown.ExpressionString(value=username)
    setattr(expr, 'is', eolymp.wellknown.ExpressionString.EQUAL)

    out = user_svc.ListUsers(eolymp.cognito.ListUsersInput(filters=eolymp.cognito.ListUsersInput.Filter(
        username=[expr]
    )))

    if len(out.items) == 0:
        raise Exception("Eolymp user with username \"{}\" does not exist".format(username))

    print("Username \"{}\" resolved to ID {}".format(username, out.items[0].id))

    return out.items[0]

def to_bool(value):
    return value.lower() in ["true", "1", "yes"]

def to_values(attributes, row):
    values = []

    for key in attributes:
        attr = attributes[key]
        column = "attr_" + attr.key

        if column not in row:
            continue

        if attr.type == eolymp.community.Attribute.Type.NUMBER:
            values.append(eolymp.community.Attribute.Value(attribute_key=attr.key, number=int(row[column])))
        else:
            values.append(eolymp.community.Attribute.Value(attribute_key=attr.key, string=row[column]))

    return values

def to_user(row):
    if "password" in row and row["password"]:
        return eolymp.community.User(
            issuer=lookup.space.issuer_url,
            nickname=row["nickname"] if "nickname" in row else "",
            password=row["password"] if "password" in row else "",
            name=row["name"] if "name" in row else "",
            country=row["country"] if "country" in row else "",
            email=row["email"] if "email" in row else "",
            # birthday=row["birthday"], todo: parse date into timestamp
        )

    if "eolymp_user_id" in row and row["eolymp_user_id"]:
        return eolymp.community.User(
            issuer="https://accounts.eolymp.com",
            subject=row["eolymp_user_id"],
        )

    if "eolymp_username" in row and row["eolymp_username"]:
        acc = resolve_username(row["eolymp_username"])
        return eolymp.community.User(
            issuer=lookup.space.issuer_url,
            subject=acc.id,
            nickname=acc.username,
            name=acc.name,
        )

    return None


# Open import file
file = open(args.input)
reader = csv.reader(file)
header = next(reader)

print("Load attributes...")
attributes = get_attribute_map()

print("Load existing members...")
members = get_members_map()

print("Importing file...")
for row in reader:
    data = dict(zip(header, row))

    user = to_user(data)
    if not user:
        print("User is not specified in the row, skipping")
        continue

    member = eolymp.community.Member(
        user=user,
        inactive=to_bool(data["inactive"]) if "inactive" in data else False,
        rating=int(data["rating"]) if "rating" in data else 0,
        groups=data["groups"].split(" ") if "groups" in data else [],
        unofficial=to_bool(data["unofficial"]) if "unofficial" in data else False,
        attributes=to_values(attributes, data),
    )

    if user.nickname in members:
        ex = members[user.nickname]
        patch = [eolymp.community.UpdateMemberInput.ACCOUNT]

        if "unofficial" in data:
            patch.append(eolymp.community.UpdateMemberInput.UNOFFICIAL)

        if "rating" in data:
            patch.append(eolymp.community.UpdateMemberInput.RATING)

        if "inactive" in data:
            patch.append(eolymp.community.UpdateMemberInput.INACTIVE)

        if "groups" in data:
            patch.append(eolymp.community.UpdateMemberInput.GROUPS)

        if member.attributes:
            patch.append(eolymp.community.UpdateMemberInput.ATTRIBUTES)

        member_svc.UpdateMember(eolymp.community.UpdateMemberInput(member_id=ex.id, patch=patch, member=member))

        print("Member {} ({}) has been updated".format(ex.id, member.user.nickname))
    else:
        out = member_svc.CreateMember(eolymp.community.CreateMemberInput(member=member))

        print("Member {} ({}) has been added".format(out.member_id, member.user.nickname))
