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
from basicmemnet import word2memnet
from bson import ObjectId
import json
import copy

# TODO: _find_isomorphic_subgraphs including has_tool / has_object ... links


class DSL:
    def __init__(self, use_wordnet=False, json_file=None):
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
        print(f"loading {file_path} ...")
        with open(file_path, "r") as file:
            nodes = json.load(file)
            for node_ix in range(len(nodes)):
                print(f"{node_ix} / {len(nodes)} nodes inserted", end="\r")
                node_attributes = nodes[node_ix]["node_attributes"]
                parent_attributes = nodes[node_ix].get("parent_attributes", {})
                self.create_linked_node(
                    parent_attributes, node_attributes, link_type=nodes[node_ix]["link"]
                )
        print("loading finished", end="\n")

    # export graph in gml format
    def export_gml(self, graph_file):
        nx.write_gml(self.graph, graph_file)

    # import graph from gml format
    def import_gml(self, graph_file):
        self.graph = nx.read_gml(graph_file)

    def __extract_longest_paths(self, sub_graph, edge_attribute, filter_attribute=None):
        subgraph = nx.DiGraph([(u, v) for u, v, d in
                               sub_graph.edges(data=True) if d.get('link_type') == edge_attribute])
        starting_nodes = [node for node in subgraph.nodes() if subgraph.in_degree(node) == 0]

        all_longest_paths = []
        for source in starting_nodes:
            # Get all nodes reachable from the source
            reachable_nodes = nx.descendants(subgraph, source)
            for target in reachable_nodes:
                try:
                    path = nx.dag_longest_path(subgraph)
                    all_longest_paths.append(path)
                except nx.NetworkXNoPath:
                    continue  # No path from source to target

        filtered_paths = self.__filter_redundant_paths(all_longest_paths)
        all_longest_paths = []
        for filtered_path in filtered_paths:
            filtered_nodes_data = []
            for filtered_node_id in filtered_path:
                node_data = sub_graph.nodes[filtered_node_id]
                if filter_attribute in node_data:
                    filtered_nodes_data.append(node_data[filter_attribute])
                else:
                    filtered_nodes_data.append(sub_graph.nodes[filtered_node_id])
            all_longest_paths.append(filtered_nodes_data)
        return all_longest_paths

    @staticmethod
    def __filter_redundant_paths(paths):
        # Remove paths that are subpaths of any other path
        filtered_paths = []
        sorted_paths = sorted(paths, key=len, reverse=True)  # Sort paths by length, longest first
        for path in sorted_paths:
            if not any(set(path).issubset(set(other_path)) for other_path in filtered_paths):
                filtered_paths.append(path)
        return filtered_paths

    @staticmethod
    def __compute_longest_common_subsequence(sequence1, sequence2):
        # Create a 2D array to store lengths of longest common subsequence.
        m = len(sequence1)
        n = len(sequence2)
        L = [[0] * (n + 1) for i in range(m + 1)]

        # Building the matrix in bottom-up fashion
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if sequence1[i - 1] == sequence2[j - 1]:
                    L[i][j] = L[i - 1][j - 1] + 1
                else:
                    L[i][j] = max(L[i - 1][j], L[i][j - 1])

        return L[m][n]

    def get_node_attributes(self, node_id, filter_attributes=None):
        filtered_node_attributes = {}
        if filter_attributes:
            node_attributes = self.graph.nodes[node_id]
            for filter_attribute in filter_attributes:
                if filter_attribute in node_attributes:
                    filtered_node_attributes.update({filter_attribute: node_attributes[filter_attribute]})
        else:
            filtered_node_attributes = self.graph.nodes[node_id]
        return filtered_node_attributes

    def find_best_matching_path(self, sub_graph_1=None, sub_graph_2=None, link_type="has_next"):
        paths1 = self.__extract_longest_paths(sub_graph_1, link_type, filter_attribute="utterances")
        paths2 = self.__extract_longest_paths(sub_graph_2, link_type, filter_attribute="utterances")
        paths1_utterances = [utterance[0] for path1 in paths1 for utterance in path1]
        paths2_utterances = [utterance[0] for path2 in paths2 for utterance in path2]
        longest_matching_path = self.__compute_longest_common_subsequence(paths1_utterances, paths2_utterances)
        max_length = max(len(paths1_utterances), len(paths2_utterances))
        score = 0 if max_length == 0 else (longest_matching_path / max_length)
        return score

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
    
    def get_graph(self):
        return self.graph

    def delete_sub_graphs(self, sub_graphs):
        for sub_graph in sub_graphs:
            sub_graph_nodes = list(sub_graph.nodes())
            self.graph.remove_nodes_from(sub_graph_nodes)

    def insert_sub_graphs(self, sub_graphs):
        inserted_sub_graphs = []
        for sub_graph in sub_graphs:
            self.graph.add_nodes_from(sub_graph.nodes(data=True))
            self.graph.add_edges_from(sub_graph.edges(data=True))
            inserted_sub_graphs.append()
        return self.graph.subgraph(sub_graph.nodes()).copy()

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

    def get_parents(self, sub_graph, link_type="spec_to"):
        all_paths = []
        hub_nodes = self.get_hub_nodes([sub_graph])
        def traverse_upwards(node, path=None):
            if path is None:
                path = []
            path.append(node)
            for predecessor in self.graph.predecessors(node):
                if self.graph.edges[predecessor, node].get("link_type") == link_type:
                    traverse_upwards(predecessor, path)
            return path

        for node in hub_nodes:
            path = traverse_upwards(node)
            all_paths.append([self.graph.nodes[path[-1]]])

        return all_paths

    def _find_isomorphic_subgraphs(self, sub_graph=None, **attributes):
        if sub_graph is None:
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
        else:
            pattern_graph = sub_graph

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
