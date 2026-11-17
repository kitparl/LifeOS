from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError, ConflictError, PayloadTooLargeError, get_or_404
from app.modules.planner.models import PlannerNode
from app.modules.planner.repository import PlannerRepository
from app.modules.planner.schemas import (
    NAME_MAX_LENGTH,
    PlannerContentResponse,
    PlannerContentUpdate,
    PlannerNodeCreate,
    PlannerNodeResponse,
    PlannerNodeUpdate,
)

EMPTY_DIAGRAM_XML = (
    '<mxfile><diagram id="page-1" name="Page-1">'
    '<mxGraphModel><root><mxCell id="0"/><mxCell id="1" parent="0"/></root></mxGraphModel>'
    "</diagram></mxfile>"
)

CONTENT_MAX_BYTES = 5 * 1024 * 1024

_NOT_FOUND = "Planner node not found"
# Which parent kind each kind requires; None = must be top level.
_PARENT_KINDS: dict[str, tuple[str, ...] | None] = {
    "project": None,
    "folder": ("project", "folder"),
    "diagram": ("project", "folder"),
}


class PlannerService:
    def __init__(self, db: AsyncSession):
        self.repo = PlannerRepository(db)

    async def list_nodes(self, user_id: str) -> list[PlannerNodeResponse]:
        return [PlannerNodeResponse.model_validate(n) for n in await self.repo.list_nodes(user_id)]

    async def create_node(self, user_id: str, data: PlannerNodeCreate) -> PlannerNodeResponse:
        parent = await self._resolve_parent(user_id, data.kind, data.parent_id)
        await self._ensure_name_free(user_id, data.parent_id, data.name)
        node = PlannerNode(
            user_id=user_id,
            parent_id=parent.id if parent else None,
            kind=data.kind,
            name=data.name,
            order_index=await self.repo.count_children(user_id, data.parent_id),
            content=EMPTY_DIAGRAM_XML if data.kind == "diagram" else None,
            revision=1,
        )
        return PlannerNodeResponse.model_validate(await self.repo.add(node))

    async def update_node(self, user_id: str, node_id: str, data: PlannerNodeUpdate) -> PlannerNodeResponse:
        node = get_or_404(await self.repo.get_by_id(user_id, node_id), _NOT_FOUND)
        fields = data.model_fields_set
        moving = "parent_id" in fields
        new_parent_id = data.parent_id if moving else node.parent_id
        new_name = data.name if data.name is not None else node.name

        if moving and new_parent_id != node.parent_id:
            await self._resolve_parent(user_id, node.kind, new_parent_id)
            await self._reject_cycle(user_id, node, new_parent_id)
        if new_parent_id != node.parent_id or new_name.lower() != node.name.lower():
            await self._ensure_name_free(user_id, new_parent_id, new_name, exclude_id=node.id)
        node.name = new_name

        if moving or data.order_index is not None:
            await self._reposition(user_id, node, new_parent_id, data.order_index)
        await self.repo.flush()
        return PlannerNodeResponse.model_validate(node)

    async def get_content(self, user_id: str, node_id: str) -> PlannerContentResponse:
        node = await self._get_diagram(user_id, node_id)
        return PlannerContentResponse(content=node.content or EMPTY_DIAGRAM_XML, revision=node.revision)

    async def save_content(
        self, user_id: str, node_id: str, data: PlannerContentUpdate
    ) -> PlannerContentResponse:
        node = await self._get_diagram(user_id, node_id)
        if len(data.content.encode("utf-8")) > CONTENT_MAX_BYTES:
            raise PayloadTooLargeError("Diagram is larger than 5 MB")
        if not await self.repo.save_content_if_revision(user_id, node.id, data.content, data.base_revision):
            raise ConflictError("Diagram was changed elsewhere; reload to get the latest version")
        return PlannerContentResponse(content=data.content, revision=data.base_revision + 1)

    async def duplicate_node(self, user_id: str, node_id: str) -> PlannerNodeResponse:
        source = get_or_404(await self.repo.get_by_id(user_id, node_id), _NOT_FOUND)
        siblings = await self.repo.list_children(user_id, source.parent_id)
        name = self._copy_name(source.name, {s.name.lower() for s in siblings})

        root = await self._copy_subtree(user_id, source, source.parent_id, name)
        # Place the copy right after the original, then renumber.
        siblings = [s for s in siblings if s.id != root.id]
        siblings.insert(siblings.index(source) + 1, root)
        for index, sibling in enumerate(siblings):
            sibling.order_index = index
        await self.repo.flush()
        return PlannerNodeResponse.model_validate(root)

    async def delete_node(self, user_id: str, node_id: str) -> None:
        node = get_or_404(await self.repo.get_by_id(user_id, node_id), _NOT_FOUND)
        doomed = [node]
        for current in doomed:  # grows while iterating: breadth-first walk of the subtree
            doomed.extend(await self.repo.list_children(user_id, current.id))
        await self.repo.soft_delete(doomed)
        for position, sibling in enumerate(await self.repo.list_children(user_id, node.parent_id)):
            sibling.order_index = position
        await self.repo.flush()

    async def _get_diagram(self, user_id: str, node_id: str) -> PlannerNode:
        node = get_or_404(await self.repo.get_by_id(user_id, node_id), _NOT_FOUND)
        if node.kind != "diagram":
            raise BadRequestError("Only diagrams have content")
        return node

    async def _resolve_parent(self, user_id: str, kind: str, parent_id: str | None) -> PlannerNode | None:
        allowed = _PARENT_KINDS[kind]
        if allowed is None:
            if parent_id is not None:
                raise BadRequestError("Projects must be top-level")
            return None
        if parent_id is None:
            raise BadRequestError(f"A {kind} needs a project or folder parent")
        parent = get_or_404(await self.repo.get_by_id(user_id, parent_id), _NOT_FOUND)
        if parent.kind not in allowed:
            raise BadRequestError(f"A {kind} cannot be placed inside a {parent.kind}")
        return parent

    async def _reject_cycle(self, user_id: str, node: PlannerNode, new_parent_id: str | None) -> None:
        current_id = new_parent_id
        while current_id is not None:
            if current_id == node.id:
                raise BadRequestError("Cannot move a node into itself or its own descendant")
            current = await self.repo.get_by_id(user_id, current_id)
            current_id = current.parent_id if current else None

    async def _ensure_name_free(
        self, user_id: str, parent_id: str | None, name: str, exclude_id: str | None = None
    ) -> None:
        taken = {s.name.lower() for s in await self.repo.list_children(user_id, parent_id) if s.id != exclude_id}
        if name.lower() in taken:
            raise ConflictError("A node with this name already exists here")

    async def _reposition(
        self, user_id: str, node: PlannerNode, new_parent_id: str | None, order_index: int | None
    ) -> None:
        old_parent_id = node.parent_id
        new_siblings = [s for s in await self.repo.list_children(user_id, new_parent_id) if s.id != node.id]
        index = len(new_siblings) if order_index is None else min(order_index, len(new_siblings))
        new_siblings.insert(index, node)
        node.parent_id = new_parent_id
        for position, sibling in enumerate(new_siblings):
            sibling.order_index = position
        if old_parent_id != new_parent_id:
            old_siblings = [s for s in await self.repo.list_children(user_id, old_parent_id) if s.id != node.id]
            for position, sibling in enumerate(old_siblings):
                sibling.order_index = position

    @staticmethod
    def _copy_name(name: str, taken: set[str]) -> str:
        base = name[: NAME_MAX_LENGTH - 10]
        candidate = f"{base} copy"
        counter = 2
        while candidate.lower() in taken:
            candidate = f"{base} copy {counter}"
            counter += 1
        return candidate

    async def _copy_subtree(
        self, user_id: str, source: PlannerNode, parent_id: str | None, name: str
    ) -> PlannerNode:
        copy = await self.repo.add(
            PlannerNode(
                user_id=user_id,
                parent_id=parent_id,
                kind=source.kind,
                name=name,
                order_index=source.order_index,
                content=source.content,
                revision=1,
            )
        )
        for child in await self.repo.list_children(user_id, source.id):
            await self._copy_subtree(user_id, child, copy.id, child.name)
        return copy
