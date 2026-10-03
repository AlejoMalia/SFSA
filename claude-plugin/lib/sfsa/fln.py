"""
sfsa.fln — Framework Layer Network (FLN) Engine
================================================
Reactive DAG (Directed Acyclic Graph) of scientific framework layers.
Automatically synchronizes, self-corrects, and propagates delta changes across
all theoretical layers whenever any foundational parameter is modified.

Part of SFSA (Standard Framework for Scientific Advancement)
Author & Protocol Creator: Alejo Malia
License: CC BY 4.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set


@dataclass
class LayerDependency:
    """Directed link between a source layer and a dependent target layer."""
    source_layer_id: str
    target_layer_id: str
    transformer: Callable[[Dict[str, Any], Dict[str, Any]], Dict[str, Any]]
    description: str = ""


@dataclass
class FrameworkLayer:
    """An individual conceptual or computational layer in the scientific framework."""
    layer_id: str
    name: str
    state: Dict[str, Any] = field(default_factory=dict)
    version: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)


class FrameworkLayerNetwork:
    """
    Reactive Network coordinating all layers of a scientific model.
    Guarantees cross-layer consistency without manual re-execution.
    """

    def __init__(self) -> None:
        self._layers: Dict[str, FrameworkLayer] = {}
        self._dependencies: List[LayerDependency] = []
        self._subscribers: List[Callable[[str, Dict[str, Any]], None]] = []

    def register_layer(
        self,
        layer_id: str,
        initial_state: Optional[Dict[str, Any]] = None,
        name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> FrameworkLayer:
        """Registers a layer in the scientific framework."""
        layer = FrameworkLayer(
            layer_id=layer_id,
            name=name or layer_id,
            state=initial_state or {},
            metadata=metadata or {},
        )
        self._layers[layer_id] = layer
        return layer

    def get_layer(self, layer_id: str) -> Optional[FrameworkLayer]:
        """Retrieves a layer by its identifier."""
        return self._layers.get(layer_id)

    def connect_layers(
        self,
        source_layer_id: str,
        target_layer_id: str,
        transformer: Callable[[Dict[str, Any], Dict[str, Any]], Dict[str, Any]],
        description: str = "",
    ) -> None:
        """
        Creates a reactive link: when source_layer changes, transformer(source.state, target.state)
        is evaluated to update target_layer.
        """
        if source_layer_id not in self._layers:
            raise KeyError(f"Source layer '{source_layer_id}' is not registered.")
        if target_layer_id not in self._layers:
            raise KeyError(f"Target layer '{target_layer_id}' is not registered.")

        if source_layer_id == target_layer_id or source_layer_id in self._reachable_from(target_layer_id):
            raise ValueError(
                f"Cyclic dependency: connecting '{source_layer_id}' -> '{target_layer_id}' would create a cycle"
            )

        dep = LayerDependency(
            source_layer_id=source_layer_id,
            target_layer_id=target_layer_id,
            transformer=transformer,
            description=description,
        )
        self._dependencies.append(dep)

    def _reachable_from(self, layer_id: str) -> Set[str]:
        """All layers reachable by following dependency edges from layer_id (excluding itself unless in a cycle)."""
        adj: Dict[str, List[str]] = {}
        for d in self._dependencies:
            adj.setdefault(d.source_layer_id, []).append(d.target_layer_id)
        seen: Set[str] = set()
        stack = list(adj.get(layer_id, []))
        while stack:
            node = stack.pop()
            if node not in seen:
                seen.add(node)
                stack.extend(adj.get(node, []))
        return seen

    def disconnect_layers(self, source_layer_id: str, target_layer_id: str) -> int:
        """Removes every dependency edge source -> target. Returns the number of edges removed."""
        before = len(self._dependencies)
        self._dependencies = [
            d for d in self._dependencies
            if not (d.source_layer_id == source_layer_id and d.target_layer_id == target_layer_id)
        ]
        return before - len(self._dependencies)

    def get_downstream(self, layer_id: str) -> List[str]:
        """Returns all layers reachable downstream from layer_id (excluding itself), in topological order."""
        if layer_id not in self._layers:
            raise KeyError(f"Layer '{layer_id}' does not exist.")
        return self._topological_sort_from(layer_id)[1:]

    def export_graph(self) -> Dict[str, Any]:
        """Exports the DAG as plain data: nodes (with version) and edges."""
        return {
            "nodes": [
                {"id": l.layer_id, "name": l.name, "version": l.version, "parameters": sorted(l.state.keys())}
                for l in self._layers.values()
            ],
            "edges": [
                {"source": d.source_layer_id, "target": d.target_layer_id, "description": d.description}
                for d in self._dependencies
            ],
        }

    def _topological_sort_from(self, start_layer_id: str) -> List[str]:
        """Calculates topological execution order for layers downstream from start_layer_id."""
        adj: Dict[str, List[str]] = {lid: [] for lid in self._layers}
        for dep in self._dependencies:
            adj[dep.source_layer_id].append(dep.target_layer_id)

        visited: Set[str] = set()
        order: List[str] = []

        def dfs(node: str, path: Set[str]) -> None:
            if node in path:
                raise ValueError(f"Cyclic dependency detected in FLN at layer '{node}'")
            if node not in visited:
                path.add(node)
                for neighbor in adj.get(node, []):
                    dfs(neighbor, path)
                path.remove(node)
                visited.add(node)
                order.append(node)

        dfs(start_layer_id, set())
        order.reverse()
        return order

    def update_layer(
        self,
        layer_id: str,
        patch: Dict[str, Any],
        propagate: bool = True,
    ) -> Dict[str, int]:
        """
        Updates layer state and reactively cascades corrections through all dependent layers.
        Returns a dictionary of {layer_id: new_version} for all affected layers.
        """
        if layer_id not in self._layers:
            raise KeyError(f"Layer '{layer_id}' does not exist.")

        # Resolve the cascade order first, then apply atomically: if any transformer fails,
        # every affected layer is restored so the network never stays half-updated.
        order = self._topological_sort_from(layer_id) if propagate else [layer_id]
        snapshot = {
            lid: (dict(self._layers[lid].state), self._layers[lid].version) for lid in order
        }
        notifications: List[str] = []
        layer = self._layers[layer_id]
        updated_versions: Dict[str, int] = {}
        try:
            layer.state.update(patch)
            layer.version += 1
            updated_versions[layer_id] = layer.version
            notifications.append(layer_id)

            # Skip the start layer itself as it was already patched
            for current_id in order[1:]:
                incoming = [d for d in self._dependencies if d.target_layer_id == current_id]
                target_layer = self._layers[current_id]
                for dep in incoming:
                    source_layer = self._layers[dep.source_layer_id]
                    delta = dep.transformer(source_layer.state, target_layer.state)
                    if delta:
                        target_layer.state.update(delta)
                target_layer.version += 1
                updated_versions[current_id] = target_layer.version
                notifications.append(current_id)
        except Exception:
            for lid, (state, version) in snapshot.items():
                self._layers[lid].state.clear()
                self._layers[lid].state.update(state)
                self._layers[lid].version = version
            raise

        for lid in notifications:
            self._notify(lid, self._layers[lid].state)
        return updated_versions

    def subscribe(self, callback: Callable[[str, Dict[str, Any]], None]) -> None:
        """Subscribes an event listener to state changes."""
        self._subscribers.append(callback)

    def _notify(self, layer_id: str, state: Dict[str, Any]) -> None:
        for sub in self._subscribers:
            try:
                sub(layer_id, state)
            except Exception:
                pass

    @property
    def layers(self) -> Dict[str, FrameworkLayer]:
        return dict(self._layers)
