/**
 * sfsa.fln — Framework Layer Network (FLN) Engine
 * ================================================
 * Reactive DAG of scientific framework layers for JavaScript.
 * Automatically synchronizes, self-corrects, and propagates delta updates across
 * all layers whenever any foundational parameter changes.
 *
 * Part of SFSA (Standard Framework for Scientific Advancement)
 * Author & Protocol Creator: Alejo Malia
 * License: CC BY 4.0
 */

export class LayerDependency {
  constructor({ sourceLayerId, targetLayerId, transformer, description = "" }) {
    this.sourceLayerId = sourceLayerId;
    this.targetLayerId = targetLayerId;
    this.transformer = transformer;
    this.description = description;
  }
}

export class FrameworkLayer {
  constructor({ layerId, name = null, state = {}, version = 1, metadata = {} }) {
    this.layerId = layerId;
    this.name = name || layerId;
    this.state = state;
    this.version = version;
    this.metadata = metadata;
  }
}

export class FrameworkLayerNetwork {
  constructor() {
    this._layers = new Map();
    this._dependencies = [];
    this._subscribers = [];
  }

  registerLayer(layerId, initialState = {}, name = null, metadata = {}) {
    const layer = new FrameworkLayer({
      layerId,
      name,
      state: { ...initialState },
      metadata,
    });
    this._layers.set(layerId, layer);
    return layer;
  }

  getLayer(layerId) {
    return this._layers.get(layerId);
  }

  connectLayers(sourceLayerId, targetLayerId, transformer, description = "") {
    if (!this._layers.has(sourceLayerId)) {
      throw new Error(`Source layer '${sourceLayerId}' is not registered.`);
    }
    if (!this._layers.has(targetLayerId)) {
      throw new Error(`Target layer '${targetLayerId}' is not registered.`);
    }

    if (sourceLayerId === targetLayerId || this._reachableFrom(targetLayerId).has(sourceLayerId)) {
      throw new Error(
        `Cyclic dependency: connecting '${sourceLayerId}' -> '${targetLayerId}' would create a cycle`
      );
    }

    const dep = new LayerDependency({
      sourceLayerId,
      targetLayerId,
      transformer,
      description,
    });
    this._dependencies.push(dep);
  }

  _reachableFrom(layerId) {
    const adj = new Map();
    for (const d of this._dependencies) {
      if (!adj.has(d.sourceLayerId)) adj.set(d.sourceLayerId, []);
      adj.get(d.sourceLayerId).push(d.targetLayerId);
    }
    const seen = new Set();
    const stack = [...(adj.get(layerId) || [])];
    while (stack.length > 0) {
      const node = stack.pop();
      if (!seen.has(node)) {
        seen.add(node);
        stack.push(...(adj.get(node) || []));
      }
    }
    return seen;
  }

  disconnectLayers(sourceLayerId, targetLayerId) {
    const before = this._dependencies.length;
    this._dependencies = this._dependencies.filter(
      (d) => !(d.sourceLayerId === sourceLayerId && d.targetLayerId === targetLayerId)
    );
    return before - this._dependencies.length;
  }

  getDownstream(layerId) {
    if (!this._layers.has(layerId)) {
      throw new Error(`Layer '${layerId}' does not exist.`);
    }
    return this._topologicalSortFrom(layerId).slice(1);
  }

  exportGraph() {
    return {
      nodes: [...this._layers.values()].map((l) => ({
        id: l.layerId, name: l.name, version: l.version, parameters: Object.keys(l.state).sort(),
      })),
      edges: this._dependencies.map((d) => ({
        source: d.sourceLayerId, target: d.targetLayerId, description: d.description,
      })),
    };
  }

  _topologicalSortFrom(startLayerId) {
    const adj = new Map();
    for (const lid of this._layers.keys()) {
      adj.set(lid, []);
    }
    for (const dep of this._dependencies) {
      adj.get(dep.sourceLayerId).push(dep.targetLayerId);
    }

    const visited = new Set();
    const order = [];

    const dfs = (node, path) => {
      if (path.has(node)) {
        throw new Error(`Cyclic dependency detected in FLN at layer '${node}'`);
      }
      if (!visited.has(node)) {
        path.add(node);
        for (const neighbor of adj.get(node) || []) {
          dfs(neighbor, path);
        }
        path.delete(node);
        visited.add(node);
        order.push(node);
      }
    };

    dfs(startLayerId, new Set());
    order.reverse();
    return order;
  }

  updateLayer(layerId, patch, propagate = true) {
    if (!this._layers.has(layerId)) {
      throw new Error(`Layer '${layerId}' does not exist.`);
    }

    // Resolve the cascade order first, then apply atomically: on any failure restore every affected layer.
    const order = propagate ? this._topologicalSortFrom(layerId) : [layerId];
    const snapshot = new Map(order.map((id) => {
      const l = this._layers.get(id);
      return [id, { state: { ...l.state }, version: l.version }];
    }));
    const notifications = [];
    const updatedVersions = {};
    const layer = this._layers.get(layerId);
    try {
      Object.assign(layer.state, patch);
      layer.version += 1;
      updatedVersions[layerId] = layer.version;
      notifications.push(layerId);

      for (const currentId of order.slice(1)) {
        const incoming = this._dependencies.filter((d) => d.targetLayerId === currentId);
        const targetLayer = this._layers.get(currentId);
        for (const dep of incoming) {
          const sourceLayer = this._layers.get(dep.sourceLayerId);
          const delta = dep.transformer(sourceLayer.state, targetLayer.state);
          if (delta && typeof delta === 'object') {
            Object.assign(targetLayer.state, delta);
          }
        }
        targetLayer.version += 1;
        updatedVersions[currentId] = targetLayer.version;
        notifications.push(currentId);
      }
    } catch (err) {
      for (const [id, snap] of snapshot) {
        const l = this._layers.get(id);
        for (const k of Object.keys(l.state)) delete l.state[k];
        Object.assign(l.state, snap.state);
        l.version = snap.version;
      }
      throw err;
    }

    for (const id of notifications) this._notify(id, this._layers.get(id).state);
    return updatedVersions;
  }

  subscribe(callback) {
    this._subscribers.push(callback);
  }

  _notify(layerId, state) {
    for (const sub of this._subscribers) {
      try {
        sub(layerId, state);
      } catch {
        // ignore subscriber errors
      }
    }
  }

  get layers() {
    return new Map(this._layers);
  }
}
