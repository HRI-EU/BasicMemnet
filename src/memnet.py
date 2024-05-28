#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Custom package settings
#
# Copyright (C) 2023, Honda Research Institute Europe GmbH.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
#     (1) Redistributions of source code must retain the above copyright
#     notice, this list of conditions and the following disclaimer.
#
#     (2) Redistributions in binary form must reproduce the above copyright
#     notice, this list of conditions and the following disclaimer in
#     the documentation and/or other materials provided with the
#     distribution.
#
#     (3)The name of the author may not be used to
#     endorse or promote products derived from this software without
#     specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT,
# INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
# STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING
# IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import networkx as nx
from networkx.algorithms import isomorphism
from src import word2memnet
from bson import ObjectId
import json
import copy

# TODO: _find_isomorphic_subgraphs including has_tool / has_object ... links


class DSL:
    def __init__(self, use_wordnet=False, json_file="action_patterns.json"):
        #  define role and memory types
        self.role_types = ["action", "object", "tool", "location", "time", "agent"]
        self.memory_types = ["stm", "ltm", "mtm", None]
        # create interface function for all possible combinations above with pattern
        # get_<memory_type>_<role_type>
        self._add_dynamic_methods()

        # create either an empty graph or initialized from installed WordNet python package
        if use_wordnet:
            self.graph = word2memnet.create_wordnet_graph()
        else:
            self.graph = nx.DiGraph()
        # optionally load predefined action patterns
        if json_file:
            self.load_from_json(json_file)

    def load_from_json(self, file_path):
        with open(file_path, "r") as file:
            nodes = json.load(file)
            for node in nodes:
                node_attributes = node["node_attributes"]
                parent_attributes = node.get("parent_attributes", {})
                self.create_linked_node(parent_attributes, node_attributes, link_type=node["link"])

    def get_graphs(self):
        return [self.graph]

    def _find_sub_graphs(self, return_type="action", memory=None, **attributes):
        attributes_copy = copy.deepcopy(attributes)
        for type_name in attributes_copy:
            if (
                    not type_name.endswith("_attributes")
                    or type_name.split("_attributes")[0] not in self.role_types
            ):
                raise ValueError("Invalid attribute name: " + type_name)
            attributes_copy[type_name].update({"memory": memory})
        sub_graphs = self._find_isomorphic_subgraphs(**attributes_copy)
        expanded_sub_graphs = self._expand_to_full_pattern(sub_graphs, return_type)

        return expanded_sub_graphs

    @staticmethod
    def get_hub_nodes(sub_graphs):
        hub_nodes = []
        for sub_graph in sub_graphs:
            for node in sub_graph.nodes():
                if sub_graph.in_degree(node) == 0:
                    hub_nodes.append(node)
        return hub_nodes

    def get_uuid(self, node_attributes):
        # Iterate through all nodes in the graph
        for node, attributes in self.graph.nodes(data=True):
            # Check if the node's attributes match the given node_attributes
            if all(
                attributes.get(key) == value for key, value in node_attributes.items()
            ):
                # Return the UUID of the matching node
                return node  # Assuming the node's UUID is its identifier
        # Return None if no matching node is found
        return None

    def create_linked_node(self, parent_attributes, node_attributes, link_type=""):
        parent_uuid = None
        if parent_attributes is not None:
            parent_uuid = self.get_uuid(node_attributes=parent_attributes)

        uuid = (
            str(ObjectId())
            if "uuid" not in node_attributes
            else node_attributes["uuid"]
        )
        node_attributes["uuid"] = uuid
        self.graph.add_node(uuid, **node_attributes)
        if parent_uuid:
            self.graph.add_edge(parent_uuid, uuid, link_type=link_type)
        return node_attributes

    def get_nodes(self, **attributes):
        sub_graphs = self._find_isomorphic_subgraphs(**attributes)
        return sub_graphs

    def get_parents(self, **attributes):
        sub_graphs = self._find_isomorphic_subgraphs(**attributes)
        hub_nodes = self.get_hub_nodes(sub_graphs)

        def traverse_upwards(node, path=None):
            if path is None:
                path = []
            path.append(node)
            for predecessor in self.graph.predecessors(node):
                if self.graph.edges[predecessor, node].get("link_type") == "spec_to":
                    traverse_upwards(predecessor, path)
            return path

        all_paths = []
        for node in hub_nodes:
            paths = traverse_upwards(node)
            all_paths.append(paths)

        # Convert paths to subgraphs
        sub_graph_list = []
        for path in all_paths:
            sub_graph = self.graph.subgraph(path).copy()
            sub_graph_list.append(sub_graph)

        return sub_graph_list

    def _find_isomorphic_subgraphs(self, **attributes):
        pattern_graph = nx.DiGraph()

        for attr_type, attr_values in attributes.items():
            type_name = attr_type.split("_attributes")[0]
            if attr_values:
                if type_name in self.role_types:
                    attr_values = {"type": type_name, **attr_values}
                else:
                    attr_values = {**attr_values}
                pattern_graph.add_node(f"{type_name}_node", **attr_values)
                if type_name != "action" and "action_attributes" in attributes:
                    pattern_graph.add_edge(
                        "action_node", f"{type_name}_node", link_type="has_part"
                    )

        def match_func(node1, node2):
            if ("type" in node1) and ("type" in node2):
                if node1.get("type") != node2.get("type"):
                    return False
            if ("memory" in node1) and ("memory" in node2):
                if node1.get("memory") != node2.get("memory"):
                    return False
            for key in node1:
                if key != "type" and key in node2:
                    set1 = (
                        set(node1[key])
                        if isinstance(node1[key], list)
                        else set([node1[key]])
                    )
                    set2 = (
                        set(node2[key])
                        if isinstance(node2[key], list)
                        else set([node2[key]])
                    )
                    return not set1.isdisjoint(set2)
            return False

        matcher = isomorphism.DiGraphMatcher(
            self.graph, pattern_graph, node_match=match_func
        )

        sub_graphs = []
        for sub_graph in matcher.subgraph_isomorphisms_iter():
            matched_nodes = list(sub_graph)
            if matched_nodes:
                sg = self.graph.subgraph(matched_nodes).copy()
                sub_graphs.append(sg)

        return sub_graphs

    def _expand_to_full_pattern(self, sub_graphs, hub_type=None):
        def expand_upwards(node_id, visited=None):
            if visited is None:
                visited = set()
            if node_id not in visited:
                visited.add(node_id)
                for predecessor in self.graph.predecessors(node_id):
                    edge_type = self.graph.edges[predecessor, node_id].get("link_type")
                    if edge_type != "spec_to":
                        expand_upwards(predecessor, visited)
            return visited

        def expand_downwards(node, hub_type, return_type_found=False, visited=None):
            if visited is None:
                visited = set()
            if node not in visited:
                node_type = self.graph.nodes[node].get("type")
                if hub_type == node_type:
                    return_type_found = True
                if return_type_found:
                    visited.add(node)
                for successor in self.graph.successors(node):
                    expand_downwards(successor, hub_type, return_type_found, visited)
            return visited

        expanded_sub_graphs = []
        for sub_graph in sub_graphs:
            all_nodes_in_pattern = set()
            for node_data in sub_graph.nodes(data=True):
                node_id = node_data[0]
                node_type = node_data[1]["type"]
                if hub_type == node_type:
                    action_root_nodes = [node_id]
                else:
                    action_root_nodes = expand_upwards(node_id)
                for action_root in action_root_nodes:
                    nodes_in_pattern = expand_downwards(action_root, hub_type)
                    all_nodes_in_pattern.update(nodes_in_pattern)

            if all_nodes_in_pattern:
                expanded_sub_graph = self.graph.subgraph(all_nodes_in_pattern).copy()
                expanded_sub_graphs.append(expanded_sub_graph)

        return expanded_sub_graphs

    def _generic_get_memory_method(self, return_type, memory_type, **kwargs):
        return self._find_sub_graphs(
            return_type=return_type, memory=memory_type, **kwargs
        )

    def _add_dynamic_methods(self):
        for memory_type in self.memory_types:
            for role_type in self.role_types:
                method_name = (
                    f"get_{role_type}s"
                    if memory_type is None
                    else f"get_{memory_type}_{role_type}s"
                )
                setattr(
                    self.__class__,
                    method_name,
                    (
                        lambda self, vt=role_type, mt=memory_type, **kwargs: self._generic_get_memory_method(
                            return_type=vt, memory_type=mt, **kwargs
                        )
                    ),
                )
