# DynamoDB ORM

## Default fields

A PersistedObject automatically has the following non-modifyable fields:

* tenant_id
* version
* previous_version
* is_latest
* is_active
* created_on
* created_by
* changed_on
* changed_by

This allows us to audit changes to an object and soft delete objects.

The CachedPersistedObject behaves the same except that it uses a redis cache in between which may result in faster lookups

## Public functions

### Instance functions

asdict() | Returns the instance as a dictionary
asjson() | Returns the instance as a json string
from_json(..) | Returns an instance created from a json \string
 |
save(..) | Saves the instance. Used for creating and updating.
delete(..) | Soft deletes the instance.
get_previous_versions(..) | Get previous versions of the instance

### Class functions

validate(..) | Validates that the dictionary object matches the model's schema
get(..) | Get an instance by id
get_all(..) | Get all instances by criteria

## Example

### Models

User:

```python
@dataclass
class User(PersistedObject):
    table: ClassVar[str] = 'users'
    # User is defined by the actual username itself.
    # We'll use that as the entityID
    is_entity_id_required: ClassVar[bool] = True

    description: str = None

    office_ids: List[str] = None

    def get_offices(self, auth_info: AuthInfo):
        '''Lazy load Offices'''
        data = PageableResponse()
        if self.office_ids:
            data = Office.get_all(auth_info, ids=self.office_ids)
        return data

    @classmethod
    def get_by_office_id(cls, auth_info: AuthInfo, office_id):
        attrs = [
            Attr('office_ids').contains(office_id)
        ]

        data = User.get_all(auth_info, additional_attrs=attrs)
        return data
```

Office:

```python
@dataclass
class Office(PersistedObject):
    table: ClassVar[str] = 'offices'

    # name is a required field. NO_DEFAULT will trigger a TypeError(f"__init__ missing 1 required argument: '{key}'")
    name: str = NO_DEFAULT
    description: str = None
    street1: str = None
    street2: str = None
    street3: str = None
    city: str = None
    state: str = None
    country: str = None
    postal_code: str = None
    latitude: Decimal = None
    longitude: Decimal = None


    def __post_init__(self):
        super(Office, self).__post_init__()
        if self.latitude and not isinstance(self.latitude, Decimal):
            self.latitude = Decimal("{}".format(self.latitude))
        if self.longitude and not isinstance(self.longitude, Decimal):
            self.longitude = Decimal("{}".format(self.longitude))
```

### API

```python
@users_route_v1.route('', methods=["GET"])
@provide_auth_info
def get_users(auth_info=None):
    ids =       request.args.getlist('ids',     type=str)                # noqa
    limit =     request.args.get('limit',       type=int, default=100)   # noqa
    start_key = request.args.get('start_key',   type=str, default=None)  # noqa

    resp = User.get_all(auth_info, ids=ids, limit=limit, start_key=start_key)
    return jsonify(resp), 200


@users_route_v1.route('', methods=["POST"])
@provide_auth_info
def create_user(auth_info=None):
    data = request.get_json(force=True, silent=False)

    for x in User.protected_fields():
        data.pop(x, None)

    User.validate(data)
    user = User.get(auth_info, data['entity_id'])
    if user is not None:
        raise ConflictException('User with id = {} already exists.'.format(id))

    user = User(**data)
    user.save(auth_info)

    return jsonify(user.asdict()), 201


@users_route_v1.route('/<id>', methods=["GET"])
@provide_auth_info
def get_user(id, auth_info=None):
    user = User.get(auth_info, id)
    if user is None:
        raise NotFoundException('No user found for id = {}'.format(id))

    return jsonify(user.asdict()), 200


@users_route_v1.route('/<id>/offices', methods=["GET"])
@provide_auth_info
def get_user_offices(id, auth_info=None):
    user = User.get(auth_info, id)
    if user is None:
        raise NotFoundException('No user found for id = {}'.format(id))

    resp = user.get_offices(auth_info)
    return jsonify(resp), 200


@users_route_v1.route('/<id>', methods=["PUT"])
@provide_auth_info
def update_user(id, auth_info=None):
    data = request.get_json(force=True, silent=False)

    for x in User.protected_fields():
        data.pop(x, None)

    User.validate(data, validate_required_fields=False)
    user = User.get(auth_info, id)
    if user is None:
        raise NotFoundException('No user found for id = {}'.format(id))

    for k, v in data.items():
        if hasattr(user, k):
            setattr(user, k, v)
        else:
            raise BadRequestException('User has no attribute: %s' % k)
    user.save(auth_info)
    return jsonify(user.asdict()), 200


@users_route_v1.route('/<id>', methods=["DELETE"])
@provide_auth_info
def delete_user(id, auth_info=None):

    user = User.get(auth_info, id)
    if user is None:
        raise NotFoundException('No user found for id = {}'.format(id))

    user.delete(auth_info)
    return jsonify(user.asdict()), 200

```
