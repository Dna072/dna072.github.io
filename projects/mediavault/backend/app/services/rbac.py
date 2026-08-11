"""Role-based access-control helpers scoped to a workspace.

Every workspace-scoped request resolves a :class:`WorkspaceContext` that binds
the current user to their membership role. Handlers then call ``require`` to
assert the minimum role for an action, keeping authorization logic in one place.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.core.exceptions import PermissionDeniedError
from app.models.enums import Role
from app.models.user import User
from app.models.workspace import Membership, Workspace


@dataclass
class WorkspaceContext:
    user: User
    workspace: Workspace
    membership: Membership

    @property
    def role(self) -> Role:
        return self.membership.role

    def require(self, minimum: Role) -> None:
        """Raise if the member's role is below ``minimum``."""
        if self.user.is_superuser:
            return
        if not self.role.at_least(minimum):
            raise PermissionDeniedError(
                f"This action requires the {minimum.value} role; you have {self.role.value}."
            )

    def require_admin(self) -> None:
        self.require(Role.ADMIN)

    def can_write(self) -> bool:
        return self.user.is_superuser or self.role.at_least(Role.MEMBER)
