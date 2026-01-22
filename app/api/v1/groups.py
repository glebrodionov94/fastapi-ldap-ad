from fastapi import APIRouter, HTTPException, status, Query
from typing import Optional
from math import ceil

from app.models.group import GroupCreate, GroupUpdate, GroupResponse
from app.models.pagination import PaginatedResponse
from app.services.ldap_service import ldap_service

router = APIRouter(prefix="/groups", tags=["Группы"])


@router.get("", response_model=PaginatedResponse[GroupResponse])
def list_groups(
    search: Optional[str] = Query(None, description="Поиск по имени группы"),
    skip: int = Query(0, ge=0, description="Количество пропускаемых элементов"),
    limit: int = Query(
        10, ge=1, le=100, description="Максимально 100 элементов на странице"
    ),
) -> PaginatedResponse[GroupResponse]:
    """Получить список всех групп с пагинацией."""
    try:
        search_filter = "(objectClass=group)"
        if search:
            search_filter = f"(&(objectClass=group)(cn=*{search}*))"

        results = ldap_service.search(search_filter=search_filter)
        groups = []
        for entry in results:
            groups.append(
                {
                    "dn": entry.get("distinguishedName", [""])[0],
                    "cn": entry.get("cn", [""])[0],
                    "description": entry.get("description", [None])[0],
                    "member": entry.get("member", []),
                }
            )

        total = len(groups)
        paginated_groups = groups[skip : skip + limit]
        pages = ceil(total / limit) if limit > 0 else 0

        return PaginatedResponse(
            items=paginated_groups, total=total, skip=skip, limit=limit, pages=pages
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения групп: {str(e)}")


@router.get("/{group_name}", response_model=GroupResponse)
def get_group(group_name: str) -> GroupResponse:
    """Get group by name."""
    try:
        search_filter = f"(&(objectClass=group)(cn={group_name}))"
        results = ldap_service.search(search_filter=search_filter)

        if not results:
            raise HTTPException(
                status_code=404, detail=f"Group '{group_name}' not found"
            )

        entry = results[0]
        return {
            "dn": entry.get("distinguishedName", [""])[0],
            "cn": entry.get("cn", [""])[0],
            "description": entry.get("description", [None])[0],
            "member": entry.get("member", []),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get group: {str(e)}")


@router.post("", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
def create_group(group: GroupCreate) -> GroupResponse:
    """Create a new group."""
    try:
        group_dn = f"CN={group.cn},{group.ou}"

        attributes = {
            "sAMAccountName": group.cn,
            "groupType": group.groupType,
        }

        if group.description:
            attributes["description"] = group.description

        success = ldap_service.add_entry(
            dn=group_dn,
            object_class=["top", "group"],
            attributes=attributes,
        )

        if not success:
            raise HTTPException(status_code=400, detail="Failed to create group")

        return get_group(group.cn)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create group: {str(e)}")


@router.patch("/{group_name}", response_model=GroupResponse)
def update_group(group_name: str, group_update: GroupUpdate) -> GroupResponse:
    """Обновить атрибуты группы (включая перемещение)."""
    try:
        current_group = get_group(group_name)
        group_data = group_update.model_dump(exclude_none=True)

        # Handle move operation
        parent_dn = group_data.pop("parent_dn", None)
        if parent_dn:
            success = ldap_service.move_entry(current_group["dn"], parent_dn)
            if not success:
                raise HTTPException(
                    status_code=400, detail="Не удалось переместить группу"
                )

        # Update other attributes
        if group_data:
            success = ldap_service.modify_entry(current_group["dn"], group_data)
            if not success:
                raise HTTPException(
                    status_code=400, detail="Не удалось обновить группу"
                )

        return get_group(group_name)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Ошибка обновления группы: {str(e)}"
        )


@router.delete("/{group_name}", status_code=status.HTTP_204_NO_CONTENT)
def delete_group(group_name: str):
    """Delete a group."""
    try:
        current_group = get_group(group_name)
        success = ldap_service.delete_entry(current_group["dn"])

        if not success:
            raise HTTPException(status_code=400, detail="Failed to delete group")

        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete group: {str(e)}")


@router.post(
    "/{group_name}/members/{username}",
    response_model=GroupResponse,
    status_code=status.HTTP_200_OK,
)
def add_member_to_group_route(group_name: str, username: str) -> GroupResponse:
    """Добавить пользователя в группу через роут группы."""
    try:
        from app.api.v1.users import get_user as get_user_by_username

        group = get_group(group_name)
        user = get_user_by_username(username)

        # Add user to group
        success = ldap_service.add_member_to_group(group["dn"], user["dn"])
        if not success:
            raise HTTPException(status_code=400, detail="Failed to add member to group")

        return get_group(group_name)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to add member to group: {str(e)}"
        )


@router.delete(
    "/{group_name}/members/{username}", status_code=status.HTTP_204_NO_CONTENT
)
def remove_member_from_group_route(group_name: str, username: str):
    """Удалить пользователя из группы через роут группы."""
    try:
        from app.api.v1.users import get_user as get_user_by_username

        group = get_group(group_name)
        user = get_user_by_username(username)

        # Remove user from group
        success = ldap_service.remove_member_from_group(group["dn"], user["dn"])
        if not success:
            raise HTTPException(
                status_code=400, detail="Failed to remove member from group"
            )

        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to remove member from group: {str(e)}"
        )
