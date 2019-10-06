
from boto3.dynamodb.conditions import Attr, ConditionBase, Not
from dataclasses import dataclass, asdict

from techlock.common.config import AuthInfo
from techlock.common.api.jwt_authorization import (
    Claim,
    ClassMatchesClaimFilter,
    DictMatchesClaimFilter,
    get_matching_claims,
    claim_to_dynamodb_condition,
    claims_to_dynamodb_condition,
    filter_by_claims,
)


@dataclass
class Book():
    entity_id: str
    title: str
    author: str


class TestClaims():
    def test_read_all_ids(self):
        current_user = AuthInfo('test_user', 'tenant1')
        claims_to_match = [
            'allow:tenant1:test:read:users:*',
        ]
        expected = [Claim.from_string(x) for x in claims_to_match]

        actual = get_matching_claims('test', current_user, 'read', ['users'], claims_to_match)

        assert actual == expected

    def test_read_all_ids_shorthand(self):
        current_user = AuthInfo('test_user', 'tenant1')
        claims_to_match = [
            'tenant1:test:read:users:*',
        ]
        expected = [Claim.from_string(x) for x in claims_to_match]

        actual = get_matching_claims('test', current_user, 'read', ['users'], claims_to_match)

        assert actual == expected

    def test_all_actions_and_ids(self):
        current_user = AuthInfo('test_user', 'tenant1')
        claims_to_match = [
            'allow:tenant1:test:*:users:*',
        ]
        expected = [Claim.from_string(x) for x in claims_to_match]

        actual = get_matching_claims('test', current_user, 'read', ['users'], claims_to_match)

        assert actual == expected

    def test_read_specific_ids(self):
        current_user = AuthInfo('test_user', 'tenant1')
        claims_to_match = [
            'allow:tenant1:test:read:users:foo',
        ]
        expected = [Claim.from_string(x) for x in claims_to_match]

        actual = get_matching_claims('test', current_user, 'read', ['users'], claims_to_match)

        assert actual == expected

    def test_read_specific_filter(self):
        current_user = AuthInfo('test_user', 'tenant1')
        claims_to_match = [
            'allow:tenant1:test:read:users:foo:bar',
        ]
        allowed_filters = ['foo']
        expected = [Claim.from_string(x) for x in claims_to_match]

        actual = get_matching_claims('test', current_user, 'read', ['users'], claims_to_match, allowed_filters)

        assert actual == expected

    def test_any_action(self):
        current_user = AuthInfo('test_user', 'tenant1')
        claims_to_match = [
            'allow:tenant1:test:read:users:*',
        ]
        expected = [Claim.from_string(x) for x in claims_to_match]

        actual = get_matching_claims('test', current_user, '*', ['users'], claims_to_match)

        assert actual == expected

    def test_any_resource(self):
        current_user = AuthInfo('test_user', 'tenant1')
        claims_to_match = [
            'allow:tenant1:test:read:users:*',
        ]
        expected = [Claim.from_string(x) for x in claims_to_match]

        actual = get_matching_claims('test', current_user, 'read', ['*'], claims_to_match)

        assert actual == expected

    def test_glob_action(self):
        current_user = AuthInfo('test_user', 'tenant1')
        claims_to_match = [
            'allow:tenant1:test:r*:users:*',
        ]
        expected = [Claim.from_string(x) for x in claims_to_match]

        actual = get_matching_claims('test', current_user, 'read', ['users'], claims_to_match)

        assert actual == expected

    def test_glob_resource(self):
        current_user = AuthInfo('test_user', 'tenant1')
        claims_to_match = [
            'allow:tenant1:test:read:user*:*',
        ]
        expected = [Claim.from_string(x) for x in claims_to_match]

        actual = get_matching_claims('test', current_user, 'read', ['users'], claims_to_match)

        assert actual == expected

    def test_deny_all_ids(self):
        current_user = AuthInfo('test_user', 'tenant1')
        claims_to_match = [
            'deny:tenant1:test:read:users:*',
        ]
        expected = []

        actual = get_matching_claims('test', current_user, 'read', ['users'], claims_to_match)

        assert actual == expected

    def test_deny_all_ids_override_allow(self):
        current_user = AuthInfo('test_user', 'tenant1')
        claims_to_match = [
            'allow:tenant1:test:read:users:*',
            'deny:tenant1:test:read:users:*',
        ]
        expected = []

        actual = get_matching_claims('test', current_user, 'read', ['users'], claims_to_match)

        assert actual == expected

    def test_read_wrong_action(self):
        current_user = AuthInfo('test_user', 'tenant1')
        claims_to_match = [
            'allow:tenant1:test:write:users:*',
        ]
        expected = []

        actual = get_matching_claims('test', current_user, 'read', ['users'], claims_to_match)

        assert actual == expected

    def test_read_wrong_resource(self):
        current_user = AuthInfo('test_user', 'tenant1')
        claims_to_match = [
            'allow:tenant1:test:read:roles:*',
        ]
        expected = []

        actual = get_matching_claims('test', current_user, 'read', ['users'], claims_to_match)

        assert actual == expected

    def test_read_wrong_audience(self):
        current_user = AuthInfo('test_user', 'tenant1')
        claims_to_match = [
            'allow:tenant1:fake:read:users:*',
        ]
        expected = []

        actual = get_matching_claims('test', current_user, 'read', ['users'], claims_to_match)

        assert actual == expected

    def test_read_wrong_tenant(self):
        current_user = AuthInfo('test_user', 'tenant1')
        claims_to_match = [
            'allow:tenant2:fake:read:users:*',
        ]
        expected = []

        actual = get_matching_claims('test', current_user, 'read', ['users'], claims_to_match)

        assert actual == expected

    def test_read_deny_all_filter(self):
        current_user = AuthInfo('test_user', 'tenant1')
        claims_to_match = [
            'allow:tenant1:test:read:users:*',
            'allow:tenant1:test:read:users:foo:bar',
        ]
        allowed_filters = None
        expected = [Claim.from_string(claims_to_match[0])]

        actual = get_matching_claims('test', current_user, 'read', ['users'], claims_to_match, allowed_filters)

        assert actual == expected

    def test_read_deny_specific_filter(self):
        current_user = AuthInfo('test_user', 'tenant1')
        claims_to_match = [
            'allow:tenant1:test:read:users:foo:bar',
            'allow:tenant1:test:read:users:bar:foo',
        ]
        allowed_filters = ['foo']
        expected = [Claim.from_string(claims_to_match[0])]

        actual = get_matching_claims('test', current_user, 'read', ['users'], claims_to_match, allowed_filters)

        assert actual == expected


class TestClaimToDynamoDBCondition():

    def test_read_all_ids(self):
        claim = Claim.from_string(
            'allow:tenant1:test:read:users:*',
        )
        expected = None

        actual = claim_to_dynamodb_condition(claim)

        assert actual == expected

    def test_read_all_ids_shorthand(self):
        claim = Claim.from_string(
            'tenant1:test:read:users:*',
        )
        expected = None

        actual = claim_to_dynamodb_condition(claim)

        assert actual == expected

    def test_all_actions_and_ids(self):
        claim = Claim.from_string(
            'allow:tenant1:test:*:users:*',
        )
        expected = None

        actual = claim_to_dynamodb_condition(claim)

        assert actual == expected

    def test_read_specific_ids(self):
        claim = Claim.from_string(
            'allow:tenant1:test:read:users:foo',
        )
        expected = Attr('entity_id').eq('foo')

        actual = claim_to_dynamodb_condition(claim)

        assert actual == expected

    def test_read_specific_filter(self):
        claim = Claim.from_string(
            'allow:tenant1:test:read:users:foo:bar',
        )
        expected = Attr('foo').eq('bar')

        actual = claim_to_dynamodb_condition(claim)

        assert actual == expected

    def test_read_specific_filter_all(self):
        claim = Claim.from_string(
            'allow:tenant1:test:read:users:foo:*',
        )
        expected = None

        actual = claim_to_dynamodb_condition(claim)

        assert actual == expected

    def test_read_specific_filter_endwith_wildcard(self):
        claim = Claim.from_string(
            'allow:tenant1:test:read:users:foo:start*',
        )
        expected = Attr('foo').begins_with('start')

        actual = claim_to_dynamodb_condition(claim)

        assert actual == expected

    def test_read_specific_filter_beginswith_wildcard(self):
        claim = Claim.from_string(
            'allow:tenant1:test:read:users:foo:*end',
        )
        expected = Attr('foo').contains('end')

        actual = claim_to_dynamodb_condition(claim)

        assert actual == expected

    def test_read_specific_filter_contains_wildcard_left(self):
        claim = Claim.from_string(
            'allow:tenant1:test:read:users:foo:larger*short',
        )
        expected = Attr('foo').contains('larger')

        actual = claim_to_dynamodb_condition(claim)

        assert actual == expected

    def test_read_specific_filter_contains_wildcard_right(self):
        claim = Claim.from_string(
            'allow:tenant1:test:read:users:foo:short*larger',
        )
        expected = Attr('foo').contains('larger')

        actual = claim_to_dynamodb_condition(claim)

        assert actual == expected

    def test_invalid_claim(self):
        claim = Claim.from_string(
            'allow:tenant1:test:read:users:*',
        )
        claim.id = None  # Now id, filter_field, and filter_value will all be None
        expected = None

        actual = claim_to_dynamodb_condition(claim)

        assert actual == expected


class TestMultipleClaimsToDynamoDBCondition():

    def test_allow_all_ids(self):
        claims = list(map(Claim.from_string, [
            'allow:tenant1:test:read:users:*',
        ]))

        expected = None

        actual = claims_to_dynamodb_condition(claims)

        assert actual == expected

    def test_deny_specific_ids(self):
        claims = list(map(Claim.from_string, [
            'deny:tenant1:test:read:users:A',
        ]))

        expected = Not(Attr('entity_id').eq('A'))

        actual = claims_to_dynamodb_condition(claims)

        assert actual == expected

    def test_all_ids_should_override_other_allows(self):
        claims = list(map(Claim.from_string, [
            'allow:tenant1:test:read:users:A',
            'allow:tenant1:test:read:users:B',
            'tenant1:test:read:users:*',
        ]))

        expected = None

        actual = claims_to_dynamodb_condition(claims)

        assert actual == expected

    def test_all_ids_should_override_other_allows_and_only_have_denies(self):
        claims = list(map(Claim.from_string, [
            'allow:tenant1:test:read:users:A',
            'allow:tenant1:test:read:users:B',
            'tenant1:test:read:users:*',
            'deny:tenant1:test:read:users:C',
        ]))

        expected = Not(Attr('entity_id').eq('C'))

        actual = claims_to_dynamodb_condition(claims)

        assert actual == expected

    def test_allow_ids_and_deny_ids(self):
        claims = list(map(Claim.from_string, [
            'allow:tenant1:test:read:users:A',
            'allow:tenant1:test:read:users:foo:bar',
            'deny:tenant1:test:read:users:C',
            'deny:tenant1:test:read:users:bar:foo',
        ]))

        expected = (
            (
                Attr('entity_id').eq('A')
                | Attr('foo').eq('bar')
            ) & (
                Not(
                    Attr('entity_id').eq('C')
                    | Attr('bar').eq('foo')
                )
            )
        )

        actual = claims_to_dynamodb_condition(claims)

        assert actual == expected


class TestClassMatchesClaimFilter():

    def test_all_id(self):
        obj = Book('myid', 'mytitle', 'myauthor')
        claim = Claim.from_string(
            'allow:tenant1:test:read:users:*'
        )

        expected = True
        actual = ClassMatchesClaimFilter(claim)(obj)

        assert actual == expected

    def test_specific_id(self):
        obj = Book('myid', 'mytitle', 'myauthor')
        claim = Claim.from_string(
            'allow:tenant1:test:read:users:myid'
        )

        expected = True
        actual = ClassMatchesClaimFilter(claim)(obj)

        assert actual == expected

    def test_specific_field(self):
        obj = Book('myid', 'mytitle', 'myauthor')
        claim = Claim.from_string(
            'allow:tenant1:test:read:users:title:mytitle'
        )

        expected = True
        actual = ClassMatchesClaimFilter(claim)(obj)

        assert actual == expected

    def test_all_ids_deny(self):
        obj = Book('myid', 'mytitle', 'myauthor')
        claim = Claim.from_string(
            'deny:tenant1:test:read:users:*'
        )

        expected = False
        actual = ClassMatchesClaimFilter(claim)(obj)

        assert actual == expected

    def test_specific_id_deny(self):
        obj = Book('myid', 'mytitle', 'myauthor')
        claim = Claim.from_string(
            'deny:tenant1:test:read:users:myid'
        )

        expected = False
        actual = ClassMatchesClaimFilter(claim)(obj)

        assert actual == expected

    def test_specific_field_deny(self):
        obj = Book('myid', 'mytitle', 'myauthor')
        claim = Claim.from_string(
            'deny:tenant1:test:read:users:title:mytitle'
        )

        expected = False
        actual = ClassMatchesClaimFilter(claim)(obj)

        assert actual == expected


class TestDictMatchesClaimFilter():

    def test_all_id(self):
        obj = asdict(Book('myid', 'mytitle', 'myauthor'))
        claim = Claim.from_string(
            'allow:tenant1:test:read:users:*'
        )

        expected = True
        actual = DictMatchesClaimFilter(claim)(obj)

        assert actual == expected

    def test_specific_id(self):
        obj = asdict(Book('myid', 'mytitle', 'myauthor'))
        claim = Claim.from_string(
            'allow:tenant1:test:read:users:myid'
        )

        expected = True
        actual = DictMatchesClaimFilter(claim)(obj)

        assert actual == expected

    def test_specific_field(self):
        obj = asdict(Book('myid', 'mytitle', 'myauthor'))
        claim = Claim.from_string(
            'allow:tenant1:test:read:users:title:mytitle'
        )

        expected = True
        actual = DictMatchesClaimFilter(claim)(obj)

        assert actual == expected

    def test_specific_field_that_doesnt_exists(self):
        obj = asdict(Book('myid', 'mytitle', 'myauthor'))
        claim = Claim.from_string(
            'allow:tenant1:test:read:users:fake:mytitle'
        )

        expected = False
        actual = DictMatchesClaimFilter(claim)(obj)

        assert actual == expected

    def test_all_ids_deny(self):
        obj = asdict(Book('myid', 'mytitle', 'myauthor'))
        claim = Claim.from_string(
            'deny:tenant1:test:read:users:*'
        )

        expected = False
        actual = DictMatchesClaimFilter(claim)(obj)

        assert actual == expected

    def test_specific_id_deny(self):
        obj = asdict(Book('myid', 'mytitle', 'myauthor'))
        claim = Claim.from_string(
            'deny:tenant1:test:read:users:myid'
        )

        expected = False
        actual = DictMatchesClaimFilter(claim)(obj)

        assert actual == expected

    def test_specific_field_deny(self):
        obj = asdict(Book('myid', 'mytitle', 'myauthor'))
        claim = Claim.from_string(
            'deny:tenant1:test:read:users:title:mytitle'
        )

        expected = False
        actual = DictMatchesClaimFilter(claim)(obj)

        assert actual == expected

    def test_specific_field_that_doesnt_exists_deny(self):
        obj = asdict(Book('myid', 'mytitle', 'myauthor'))
        claim = Claim.from_string(
            'deny:tenant1:test:read:users:fake:mytitle'
        )

        expected = True
        actual = DictMatchesClaimFilter(claim)(obj)

        assert actual == expected


class TestFilterClassesByClaims():

    def test_allow_all_ids(self):
        books = [
            Book('myid', 'mytitle', 'myauthor'),
            Book('myid2', 'mytitle2', 'myauthor'),
        ]
        claims = list(map(Claim.from_string, [
            'allow:tenant1:test:read:users:*',
        ]))

        expected = books
        actual = filter_by_claims(books, claims)

        assert actual == expected

    def test_deny_all_ids(self):
        books = [
            Book('myid', 'mytitle', 'myauthor'),
            Book('myid2', 'mytitle2', 'myauthor'),
        ]
        claims = list(map(Claim.from_string, [
            'allow:tenant1:test:read:users:*',
            'deny:tenant1:test:read:users:*',
        ]))

        expected = list()
        actual = filter_by_claims(books, claims)

        assert actual == expected

    def test_deny_specific_ids(self):
        books = [
            Book('myid', 'mytitle', 'myauthor'),
            Book('myid2', 'mytitle2', 'myauthor'),
        ]
        claims = list(map(Claim.from_string, [
            'allow:tenant1:test:read:users:*',
            'deny:tenant1:test:read:users:myid2',
        ]))

        expected = [books[0]]
        actual = filter_by_claims(books, claims)

        assert actual == expected

    def test_allow_specific_ids(self):
        books = [
            Book('myid', 'mytitle', 'myauthor'),
            Book('myid2', 'mytitle2', 'myauthor'),
        ]
        claims = list(map(Claim.from_string, [
            'allow:tenant1:test:read:users:myid',
            'deny:tenant1:test:read:users:myid2',
        ]))

        expected = [books[0]]
        actual = filter_by_claims(books, claims)

        assert actual == expected

    def test_allow_specific_ids_without_deny(self):
        books = [
            Book('myid', 'mytitle', 'myauthor'),
            Book('myid2', 'mytitle2', 'myauthor'),
        ]
        claims = list(map(Claim.from_string, [
            'allow:tenant1:test:read:users:myid2'
        ]))

        expected = [books[1]]
        actual = filter_by_claims(books, claims)

        assert actual == expected
