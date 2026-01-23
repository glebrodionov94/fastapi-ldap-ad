from fastapi import APIRouter, HTTPException, status, Query, Depends
from typing import Optional, Dict
from math import ceil

from app.models.user import UserCreate, UserUpdate, UserResponse
from app.models.pagination import PaginatedResponse
from app.services.ldap_service import ldap_service
from app.services.audit_service import audit_service
from app.core.security import get_current_user

router = APIRouter(prefix="/users", tags=["Пользователи"])


@router.get("", response_model=PaginatedResponse[UserResponse])
def list_users(
    search: Optional[str] = Query(
        None, description="Поиск по имени, username или email"
    ),
    skip: int = Query(0, ge=0, description="Количество пропускаемых элементов"),
    limit: int = Query(
        10, ge=1, le=100, description="Максимально 100 элементов на странице"
    ),
) -> PaginatedResponse[UserResponse]:
    """Получить список всех пользователей с пагинацией."""
    try:
        search_filter = "(objectClass=user)"
        if search:
            search_filter = f"(&(objectClass=user)(|(cn=*{search}*)(sAMAccountName=*{search}*)(mail=*{search}*)))"

        results = ldap_service.search(
            search_filter=search_filter, attributes=["*", "memberOf"]
        )
        users = []
        for entry in results:
            if entry.get("sAMAccountName"):
                users.append(
                    {
                        "dn": entry.get("distinguishedName", [""])[0],
                        "cn": entry.get("cn", [""])[0],
                        "sAMAccountName": entry.get("sAMAccountName", [""])[0],
                        "givenName": entry.get("givenName", [None])[0],
                        "sn": entry.get("sn", [None])[0],
                        "mail": entry.get("mail", [None])[0],
                        "telephoneNumber": entry.get("telephoneNumber", [None])[0],
                        "title": entry.get("title", [None])[0],
                        "department": entry.get("department", [None])[0],
                        "description": entry.get("description", [None])[0],
                        "userAccountControl": entry.get("userAccountControl", [None])[
                            0
                        ],
                        "memberOf": entry.get("memberOf", []),
                    }
                )

        total = len(users)
        paginated_users = users[skip : skip + limit]
        pages = ceil(total / limit) if limit > 0 else 0

        return PaginatedResponse(
            items=paginated_users, total=total, skip=skip, limit=limit, pages=pages
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Ошибка получения пользователей: {str(e)}"
        ) from e


@router.get("/{username}", response_model=UserResponse)
def get_user(username: str) -> UserResponse:
    """Get user by username."""
    try:
        search_filter = f"(&(objectClass=user)(sAMAccountName={username}))"
        results = ldap_service.search(
            search_filter=search_filter, attributes=["*", "memberOf"]
        )

        if not results:
            raise HTTPException(status_code=404, detail=f"User '{username}' not found")

        entry = results[0]
        return UserResponse(
            dn=entry.get("distinguishedName", [""])[0],
            cn=entry.get("cn", [""])[0],
            sAMAccountName=entry.get("sAMAccountName", [""])[0],
            givenName=entry.get("givenName", [None])[0],
            sn=entry.get("sn", [None])[0],
            mail=entry.get("mail", [None])[0],
            telephoneNumber=entry.get("telephoneNumber", [None])[0],
            title=entry.get("title", [None])[0],
            department=entry.get("department", [None])[0],
            description=entry.get("description", [None])[0],
            userAccountControl=entry.get("userAccountControl", [None])[0],
            memberOf=entry.get("memberOf", []),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get user: {str(e)}"
        ) from e


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    user: UserCreate, current_user: Dict = Depends(get_current_user)
) -> UserResponse:
    """Create a new user."""
    try:
        user_dn = f"CN={user.cn},{user.ou}"

        attributes = {
            "sAMAccountName": user.sAMAccountName,
            "userPrincipalName": f"{user.sAMAccountName}@{(ldap_service.base_dn or '').replace('DC=', '').replace(',', '.')}",
            "userAccountControl": 512,  # Normal account
        }

        if user.givenName:
            attributes["givenName"] = user.givenName
        if user.sn:
            attributes["sn"] = user.sn
        if user.mail:
            attributes["mail"] = user.mail
        if user.telephoneNumber:
            attributes["telephoneNumber"] = user.telephoneNumber
        if user.title:
            attributes["title"] = user.title
        if user.department:
            attributes["department"] = user.department
        if user.description:
            attributes["description"] = user.description

        success = ldap_service.add_entry(
            dn=user_dn,
            object_class=["top", "person", "organizationalPerson", "user"],
            attributes=attributes,
        )

        if not success:
            raise HTTPException(status_code=400, detail="Failed to create user")

        # Set password
        ldap_service.reset_password(user_dn, user.password)

        result = get_user(user.sAMAccountName)
        audit_service.log(
            actor=current_user.get("username", "anonymous"),
            action="create_user",
            resource_type="user",
            resource_id=user.sAMAccountName,
            status="success",
            details={"ou": user.ou, "cn": user.cn},
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}") from e


@router.patch("/{username}", response_model=UserResponse)
def update_user(
    username: str,
    user_update: UserUpdate,
    current_user: Dict = Depends(get_current_user),
) -> UserResponse:
    """Обновить атрибуты пользователя (включая пароль и перемещение)."""
    try:
        existing_user = get_user(username)
        user_data = user_update.model_dump(exclude_none=True)

        # Handle password reset
        new_password = user_data.pop("password", None)
        if new_password:
            success = ldap_service.reset_password(existing_user.dn, new_password)
            if not success:
                raise HTTPException(
                    status_code=400, detail="Не удалось сбросить пароль"
                )

        # Handle move operation
        new_parent_dn = user_data.pop("parent_dn", None)
        if new_parent_dn:
            success = ldap_service.move_entry(existing_user.dn, new_parent_dn)
            if not success:
                raise HTTPException(
                    status_code=400, detail="Не удалось переместить пользователя"
                )

        # Update other attributes
        if user_data:
            success = ldap_service.modify_entry(existing_user.dn, user_data)
            if not success:
                raise HTTPException(
                    status_code=400, detail="Не удалось обновить пользователя"
                )

        result = get_user(username)
        audit_service.log(
            actor=current_user.get("username", "anonymous"),
            action="update_user",
            resource_type="user",
            resource_id=username,
            status="success",
            details=user_update.model_dump(exclude_none=True),
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Ошибка обновления пользователя: {str(e)}"
        ) from e


@router.delete("/{username}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(username: str, current_user: Dict = Depends(get_current_user)):
    """Delete a user."""
    try:
        current_user_obj = get_user(username)
        success = ldap_service.delete_entry(current_user_obj.dn)

        if not success:
            raise HTTPException(status_code=400, detail="Failed to delete user")

        audit_service.log(
            actor=current_user.get("username", "anonymous"),
            action="delete_user",
            resource_type="user",
            resource_id=username,
            status="success",
        )
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete user: {str(e)}") from e


@router.post(
    "/{username}/groups/{group_name}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
)
def add_user_to_group(
    username: str, group_name: str, current_user: Dict = Depends(get_current_user)
) -> UserResponse:
    """Добавить пользователя в группу."""
    try:
        user = get_user(username)

        # Find group
        search_filter = f"(&(objectClass=group)(cn={group_name}))"
        group_results = ldap_service.search(search_filter=search_filter)

        if not group_results:
            raise HTTPException(
                status_code=404, detail=f"Group '{group_name}' not found"
            )

        group_dn = group_results[0].get("distinguishedName", [""])[0]

        # Add user to group
        success = ldap_service.add_member_to_group(group_dn, user.dn)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to add user to group")

        result = get_user(username)
        audit_service.log(
            actor=current_user.get("username", "anonymous"),
            action="add_user_to_group",
            resource_type="user",
            resource_id=username,
            status="success",
            details={"group": group_name},
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to add user to group: {str(e)}"
        ) from e


@router.delete(
    "/{username}/groups/{group_name}", status_code=status.HTTP_204_NO_CONTENT
)
def remove_user_from_group(
    username: str, group_name: str, current_user: Dict = Depends(get_current_user)
):
    """Удалить пользователя из группы."""
    try:
        user = get_user(username)

        # Find group
        search_filter = f"(&(objectClass=group)(cn={group_name}))"
        group_results = ldap_service.search(search_filter=search_filter)

        if not group_results:
            raise HTTPException(
                status_code=404, detail=f"Group '{group_name}' not found"
            )

        group_dn = group_results[0].get("distinguishedName", [""])[0]

        # Remove user from group
        success = ldap_service.remove_member_from_group(group_dn, user.dn)
        if not success:
            raise HTTPException(
                status_code=400, detail="Failed to remove user from group"
            )

        audit_service.log(
            actor=current_user.get("username", "anonymous"),
            action="remove_user_from_group",
            resource_type="user",
            resource_id=username,
            status="success",
            details={"group": group_name},
        )
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to remove user from group: {str(e)}"
        ) from e
