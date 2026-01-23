from fastapi import APIRouter, HTTPException, status, Query, Depends
from typing import Optional, Dict
from math import ceil

from app.models.container import ContainerCreate, ContainerUpdate, ContainerResponse
from app.models.pagination import PaginatedResponse
from app.services.ldap_service import ldap_service
from app.services.audit_service import audit_service
from app.core.security import get_current_user

router = APIRouter(prefix="/containers", tags=["Контейнеры"])


@router.get("", response_model=PaginatedResponse[ContainerResponse])
def list_containers(
    search: Optional[str] = Query(None, description="Поиск по имени контейнера"),
    skip: int = Query(0, ge=0, description="Количество пропускаемых элементов"),
    limit: int = Query(
        10, ge=1, le=100, description="Максимально 100 элементов на странице"
    ),
) -> PaginatedResponse[ContainerResponse]:
    """Получить список всех контейнеров с пагинацией."""
    try:
        search_filter = "(objectClass=container)"
        if search:
            search_filter = f"(&(objectClass=container)(cn=*{search}*))"

        results = ldap_service.search(search_filter=search_filter)
        containers = []
        for entry in results:
            containers.append(
                {
                    "dn": entry.get("distinguishedName", [""])[0],
                    "cn": entry.get("cn", [""])[0],
                    "description": entry.get("description", [None])[0],
                }
            )

        total = len(containers)
        paginated_containers = containers[skip : skip + limit]
        pages = ceil(total / limit) if limit > 0 else 0

        return PaginatedResponse(
            items=paginated_containers, total=total, skip=skip, limit=limit, pages=pages
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Ошибка получения контейнеров: {str(e)}"
        ) from e


@router.get("/{cn}", response_model=ContainerResponse)
def get_container(cn: str, parent_dn: Optional[str] = None) -> ContainerResponse:
    """Получить контейнер по имени."""
    try:
        search_base = parent_dn if parent_dn else ldap_service.base_dn
        search_filter = f"(&(objectClass=container)(cn={cn}))"
        results = ldap_service.search(
            search_filter=search_filter, search_base=search_base
        )

        if not results:
            raise HTTPException(status_code=404, detail=f"Контейнер '{cn}' не найден")

        entry = results[0]
        return ContainerResponse(
            dn=entry.get("distinguishedName", [""])[0],
            cn=entry.get("cn", [""])[0],
            description=entry.get("description", [None])[0],
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Ошибка получения контейнера: {str(e)}"
        ) from e


@router.post("", response_model=ContainerResponse, status_code=status.HTTP_201_CREATED)
def create_container(
    container: ContainerCreate, current_user: Dict = Depends(get_current_user)
) -> ContainerResponse:
    """Создать новый контейнер."""
    try:
        container_dn = f"CN={container.cn},{container.parent_dn}"

        attributes = {}
        if container.description:
            attributes["description"] = container.description

        success = ldap_service.add_entry(
            dn=container_dn,
            object_class=["top", "container"],
            attributes=attributes,
        )

        if not success:
            raise HTTPException(status_code=400, detail="Не удалось создать контейнер")

        result = get_container(container.cn, container.parent_dn)
        audit_service.log(
            actor=current_user.get("username", "anonymous"),
            action="create_container",
            resource_type="container",
            resource_id=container.cn,
            status="success",
            details={
                "parent_dn": container.parent_dn,
                "description": container.description,
            },
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Ошибка создания контейнера: {str(e)}"
        ) from e


@router.patch("/{cn}", response_model=ContainerResponse)
def update_container(
    cn: str,
    container_update: ContainerUpdate,
    parent_dn: Optional[str] = None,
    current_user: Dict = Depends(get_current_user),
) -> ContainerResponse:
    """Обновить атрибуты контейнера (включая перемещение)."""
    try:
        current_container = get_container(cn, parent_dn)
        container_data = container_update.model_dump(exclude_none=True)

        # Handle move operation
        new_parent_dn = container_data.pop("parent_dn", None)
        if new_parent_dn:
            success = ldap_service.move_entry(current_container.dn, new_parent_dn)
            if not success:
                raise HTTPException(
                    status_code=400, detail="Не удалось переместить контейнер"
                )

        # Update other attributes
        if container_data:
            success = ldap_service.modify_entry(current_container.dn, container_data)
            if not success:
                raise HTTPException(
                    status_code=400, detail="Не удалось обновить контейнер"
                )

        result = get_container(cn, new_parent_dn if new_parent_dn else parent_dn)
        audit_service.log(
            actor=current_user.get("username", "anonymous"),
            action="update_container",
            resource_type="container",
            resource_id=cn,
            status="success",
            details=container_update.model_dump(exclude_none=True),
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Ошибка обновления контейнера: {str(e)}"
        ) from e


@router.delete("/{cn}", status_code=status.HTTP_204_NO_CONTENT)
def delete_container(
    cn: str,
    parent_dn: Optional[str] = None,
    current_user: Dict = Depends(get_current_user),
):
    """Удалить контейнер (должен быть пустым)."""
    try:
        current_container = get_container(cn, parent_dn)
        success = ldap_service.delete_entry(current_container.dn)

        if not success:
            raise HTTPException(
                status_code=400,
                detail="Не удалось удалить контейнер (должен быть пустым)",
            )

        audit_service.log(
            actor=current_user.get("username", "anonymous"),
            action="delete_container",
            resource_type="container",
            resource_id=cn,
            status="success",
        )
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Ошибка удаления контейнера: {str(e)}"
        ) from e
