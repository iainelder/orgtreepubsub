# Spec sketch (incomplete)

```
org.management_account_id -> OrganizationTypeDef["MasterAccountId"]
org.management_account_arn -> OrganizationTypeDef["MasterAccountArn"]
org.management_account_email -> OrganizationTypeDef["MasterAccountEmail"]

org.management_account -> AccountNode
org.management_account.id -> str
org.management_account.email -> str
org.management_account.arn -> str
org.management

org.organization_id -> OrganizationTypeDef["OrganizationId"]
org.list_roots() -> List[RootTypeDef]
org.root (list_roots[0]) -> RootTypeDef
org.root.describe() -> 

org.list_accounts() -> 

org.root.list_descendants()
org.root.name
org.root.tags["Contact Person"]

org.ac("111111111111") -> AccountNode
org.ac("111111111111").id -> str
org.ac("111111111111").arn -> str
org.ac("111111111111").name -> str
org.ac("111111111111").email -> str
org.ac("111111111111").joined_date -> datetime
org.ac("111111111111").joined_method -> datetime
org.ac("111111111111").describe() -> AccountTypeDef

org.ac("111111111111").parent() -> ParentNode

org.ou("ou-xxxx-yyyyyyyy") -> OrganizationalUnitNode
org.ou("ou-xxxx-yyyyyyyy").id -> str
org.ou("ou-xxxx-yyyyyyyy").arn -> str
org.ou("ou-xxxx-yyyyyyyy").arn -> str
```

OrgGraph:

- id
- management_account
- root
- ac (random access account)
- ou (random access OU)

Resource:

- id
- arn
- name
- path_from_root -> Path
- attached_policies

Root(Resource):

- enabled_policies (out of scope for version 1)

Account(Resource):

- email
- joined_date
- joined_method
- parent
- ancestors

OrganizationalUnit(Resource):

- children
- descendants

Path:

- ou_level(int) -> OrgUnitNode
- account -> `Optional[AccountNode]`
- id_str -> str
- name_str -> str

## Use cases

Get the level 1 OU for an account.

```python
org.ac("111111111111").path_from_root.ou_level(1).id -> str

"ou-xxxx-yyyyyyyy"
```

Get the ID path for an account.

```python
org.ac("111111111111").path_from_root.id_str -> str

"/r-xxxx/ou-xxxx-yyyyyyy1/ou-xxxx-yyyyyyy2/111111111111"
```

Get the name path for an account.

```python
org.ac("111111111111").path_from_root.id_str -> str

"/Root/Level 1 OU/Level 2 OU/Account 1"
```
