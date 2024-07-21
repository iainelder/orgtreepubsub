# type: ignore

class organization:
    """
    An organization exists.
    """

    def msgDataSpec(org):
        """
        - org: organization description
        """


class root:
    """
    An organization has a root.
    """

    def msgDataSpec(org, resource):
        """
        - org: organization description
        - resource: root description
        """

class parent:
    """
    A parent may contain organizational units or accounts.
    """

    def msgDataSpec(parent):
        """
        - parent: description of root or organizational unit
        """

class organizational_unit:
    """
    A parent has an organizational unit.
    """

    def msgDataSpec(parent, resource):
        """
        - parent: description of root or organizational unit
        - resource: description of child organizational unit
        """


class account:
    """
    A parent has an account.
    """

    def msgDataSpec(parent, resource):
        """
        - parent: description of root or organizational unit
        - resource: acccount description
        """


class tag:
    """
    An organization resource has a tag.
    """

    def msgDataSpec(resource, tag):
        """
        - resource: tagged resource description
        - tag: key-value pair
        """
