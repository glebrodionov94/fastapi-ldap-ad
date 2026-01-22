from fastapi import APIRouter, HTTPException, status, Query
from typing import Optional
from math import ceil

from app.models.ou import OUCreate, OUUpdate, OUResponse
from app.models.pagination import PaginatedResponse
from app.services.ldap_service import ldap_service

router = APIRouter(prefix="/ous", tags=["Подразделения"])


@router.get("", response_model=PaginatedResponse[OUResponse])
def list_ous(
    search: Optional[str] = Query(None, description="Поиск по имени подразделения"),
    skip: int = Query(0, ge=0, description="Количество пропускаемых элементов"),
    limit: int = Query(
        10, ge=1, le=100, description="Максимально 100 элементов на странице"
    ),
) -> PaginatedResponse[OUResponse]:
    """Получить список всех подразделений с пагинацией."""
    try:
        search_filter = "(objectClass=organizationalUnit)"
        if search:
            search_filter = f"(&(objectClass=organizationalUnit)(ou=*{search}*))"

        results = ldap_service.search(search_filter=search_filter)
        ous = []
        for entry in results:
            ous.append(
                {
                    "dn": entry.get("distinguishedName", [""])[0],
                    "ou": entry.get("ou", [""])[0],
                    "description": entry.get("description", [None])[0],
                }
            )

        total = len(ous)
        paginated_ous = ous[skip : skip + limit]
        pages = ceil(total / limit) if limit > 0 else 0

        return PaginatedResponse(
            items=paginated_ous, total=total, skip=skip, limit=limit, pages=pages
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Ошибка получения подразделений: {str(e)}"
        )


@router.get("/{ou_name}", response_model=OUResponse)
def get_ou(ou_name: str, parent_dn: Optional[str] = None) -> OUResponse:
    """Get OU by name."""
    try:
        search_base = parent_dn if parent_dn else ldap_service.base_dn
        search_filter = f"(&(objectClass=organizationalUnit)(ou={ou_name}))"
        results = ldap_service.search(
            search_filter=search_filter, search_base=search_base
        )

        if not results:
            raise HTTPException(status_code=404, detail=f"OU '{ou_name}' not found")

        entry = results[0]
        return {
            "dn": entry.get("distinguishedName", [""])[0],
            "ou": entry.get("ou", [""])[0],
            "description": entry.get("description", [None])[0],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get OU: {str(e)}")


@router.post("", response_model=OUResponse, status_code=status.HTTP_201_CREATED)
def create_ou(ou: OUCreate) -> OUResponse:
    """Create a new Organizational Unit."""
    try:
        ou_dn = f"OU={ou.ou},{ou.parent_dn}"

        attributes = {}
        if ou.description:
            attributes["description"] = ou.description

        success = ldap_service.add_entry(
            dn=ou_dn,
            object_class=["top", "organizationalUnit"],
            attributes=attributes,
        )

        if not success:
            raise HTTPException(status_code=400, detail="Failed to create OU")

        return get_ou(ou.ou, ou.parent_dn)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create OU: {str(e)}")


@router.patch("/{ou_name}", response_model=OUResponse)
def update_ou(
    ou_name: str, ou_update: OUUpdate, parent_dn: Optional[str] = None
) -> OUResponse:
    """Обновить атрибуты подразделения (включая перемещение)."""
    try:
        current_ou = get_ou(ou_name, parent_dn)
        ou_data = ou_update.model_dump(exclude_none=True)

        # Handle move operation
        new_parent_dn = ou_data.pop("parent_dn", None)
        if new_parent_dn:
            success = ldap_service.move_entry(current_ou["dn"], new_parent_dn)
            if not success:
                raise HTTPException(
                    status_code=400, detail="Не удалось переместить подразделение"
                )

        # Update other attributes
        if ou_data:
            success = ldap_service.modify_entry(current_ou["dn"], ou_data)
            if not success:
                raise HTTPException(
                    status_code=400, detail="Не удалось обновить подразделение"
                )

        return get_ou(ou_name, new_parent_dn if new_parent_dn else parent_dn)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Ошибка обновления подразделения: {str(e)}"
        )


@router.delete("/{ou_name}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ou(ou_name: str, parent_dn: Optional[str] = None):
    """Delete an OU (must be empty)."""
    try:
        current_ou = get_ou(ou_name, parent_dn)
        success = ldap_service.delete_entry(current_ou["dn"])

        if not success:
            raise HTTPException(
                status_code=400, detail="Failed to delete OU (must be empty)"
            )

        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete OU: {str(e)}")
