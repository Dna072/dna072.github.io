"""Role-based access control helpers.

Role hierarchy (each role inherits the permissions of the ones below it):

    ADMIN > MEMBER > VIEWER

- VIEWER: read-only access to workspace assets, folders, tags, search, shares.
- MEMBER: VIEWER + create/update/delete their own assets, folders, tags, shares.
- ADMIN:  MEMBER + manage workspace settings, manage memberships, and act on
          any asset/folder/tag regardless of ownership.
"""

from app.models.membership import WorkspaceRole

_ROLE_RANK = {
    WorkspaceRole.VIEWER: 0,
    WorkspaceRole.MEMBER: 1,
    WorkspaceRole.ADMIN: 2,
}


def role_at_least(role: WorkspaceRole, minimum: WorkspaceRole) -> bool:
    return _ROLE_RANK[role] >= _ROLE_RANK[minimum]


def can_write(role: WorkspaceRole) -> bool:
    return role_at_least(role, WorkspaceRole.MEMBER)


def can_administer(role: WorkspaceRole) -> bool:
    return role_at_least(role, WorkspaceRole.ADMIN)


def can_manage_resource(role: WorkspaceRole, is_owner: bool) -> bool:
    """MEMBERs can manage resources they own; ADMINs can manage anything."""
    if can_administer(role):
        return True
    return can_write(role) and is_owner
