from typing import Any, Optional
import logging

from ldap3 import Server, Connection, ALL, MODIFY_REPLACE, MODIFY_ADD, MODIFY_DELETE
from ldap3.core.exceptions import LDAPException

from app.core.config import settings

logger = logging.getLogger(__name__)


class LDAPService:
    """Service for interacting with Active Directory via LDAP."""

    def __init__(self):
        if not settings.ldap_server:
            logger.warning("LDAP server not configured. Service will not be available.")
            self.server = None
            self.bind_dn = None
            self.bind_password = None
            self.base_dn = None
            return

        self.server = Server(
            settings.ldap_server,
            port=settings.ldap_port,
            use_ssl=settings.ldap_use_ssl,
            get_info=ALL,
        )
        self.bind_dn = settings.ldap_bind_dn
        self.bind_password = settings.ldap_bind_password
        self.base_dn = settings.ldap_base_dn

    def _check_configured(self):
        """Check if LDAP is properly configured."""
        if not self.server:
            raise RuntimeError(
                "LDAP service not configured. Please set LDAP_* environment variables."
            )

    def _get_connection(self) -> Connection:
        """Create and bind LDAP connection."""
        self._check_configured()
        conn = Connection(
            self.server,
            user=self.bind_dn,
            password=self.bind_password,
            auto_bind=True,
        )
        return conn

    def search(
        self,
        search_filter: str,
        search_base: Optional[str] = None,
        attributes: Optional[list[str]] = None,
    ) -> list[dict[str, Any]]:
        """Search for entries in LDAP."""
        if search_base is None:
            search_base = self.base_dn
        if attributes is None:
            attributes = ["*"]

        try:
            conn = self._get_connection()
            conn.search(
                search_base=search_base,
                search_filter=search_filter,
                attributes=attributes,
            )
            results = []
            for entry in conn.entries:
                results.append(entry.entry_attributes_as_dict)
            conn.unbind()
            return results
        except LDAPException as e:
            logger.error(f"LDAP search error: {e}")
            raise

    def add_entry(
        self, dn: str, object_class: list[str], attributes: dict[str, Any]
    ) -> bool:
        """Add a new entry to LDAP."""
        try:
            conn = self._get_connection()
            success = conn.add(dn, object_class, attributes)
            conn.unbind()
            if not success:
                logger.error(f"Failed to add entry: {conn.result}")
            return success
        except LDAPException as e:
            logger.error(f"LDAP add error: {e}")
            raise

    def modify_entry(self, dn: str, changes: dict[str, Any]) -> bool:
        """Modify an existing LDAP entry."""
        try:
            conn = self._get_connection()
            modify_dict = {
                attr: [(MODIFY_REPLACE, [value])] for attr, value in changes.items()
            }
            success = conn.modify(dn, modify_dict)
            conn.unbind()
            if not success:
                logger.error(f"Failed to modify entry: {conn.result}")
            return success
        except LDAPException as e:
            logger.error(f"LDAP modify error: {e}")
            raise

    def delete_entry(self, dn: str) -> bool:
        """Delete an LDAP entry."""
        try:
            conn = self._get_connection()
            success = conn.delete(dn)
            conn.unbind()
            if not success:
                logger.error(f"Failed to delete entry: {conn.result}")
            return success
        except LDAPException as e:
            logger.error(f"LDAP delete error: {e}")
            raise

    def move_entry(self, dn: str, new_parent_dn: str) -> bool:
        """Move an LDAP entry to a new parent container."""
        try:
            # Extract RDN (relative distinguished name) from the full DN
            rdn = dn.split(",")[0]
            conn = self._get_connection()
            success = conn.modify_dn(dn, rdn, new_superior=new_parent_dn)
            conn.unbind()
            if not success:
                logger.error(f"Failed to move entry: {conn.result}")
            return success
        except LDAPException as e:
            logger.error(f"LDAP move error: {e}")
            raise

    def add_member_to_group(self, group_dn: str, member_dn: str) -> bool:
        """Add a member to a group."""
        try:
            conn = self._get_connection()
            success = conn.modify(group_dn, {"member": [(MODIFY_ADD, [member_dn])]})
            conn.unbind()
            if not success:
                logger.error(f"Failed to add member to group: {conn.result}")
            return success
        except LDAPException as e:
            logger.error(f"LDAP add member error: {e}")
            raise

    def remove_member_from_group(self, group_dn: str, member_dn: str) -> bool:
        """Remove a member from a group."""
        try:
            conn = self._get_connection()
            success = conn.modify(group_dn, {"member": [(MODIFY_DELETE, [member_dn])]})
            conn.unbind()
            if not success:
                logger.error(f"Failed to remove member from group: {conn.result}")
            return success
        except LDAPException as e:
            logger.error(f"LDAP remove member error: {e}")
            raise

    def reset_password(self, user_dn: str, new_password: str) -> bool:
        """Reset user password (requires SSL/TLS for AD)."""
        try:
            # AD requires password in specific format
            password_value = f'"{new_password}"'.encode("utf-16-le")
            conn = self._get_connection()
            success = conn.modify(
                user_dn, {"unicodePwd": [(MODIFY_REPLACE, [password_value])]}
            )
            conn.unbind()
            if not success:
                logger.error(f"Failed to reset password: {conn.result}")
            return success
        except LDAPException as e:
            logger.error(f"LDAP password reset error: {e}")
            raise


# Singleton instance
ldap_service = LDAPService()
