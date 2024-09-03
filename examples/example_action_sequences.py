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
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS"" AND ANY EXPRESS OR
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

import os
import sys
from basicmemnet import memnet
from basicmemnet import plot_graph

md = memnet.DSL()
md.import_gml(os.path.join(sys.path[0], "data", "sequence_action_patterns.gml"))
pg = plot_graph.PlotGraph()

sub_graphs = md.get_stm_actions(
    action_attributes={"type": "action"}
)

paths1_utterances = ["approach", "lift", "approach", "pour", "place"]
best_match_score = 0
best_match_graph = None

for sub_graph in sub_graphs:
    score = md.find_best_matching_path(paths1_utterances=paths1_utterances, sub_graph_2=sub_graph, link_type="has_next")
    if score > best_match_score:
        best_match_score = score
        best_match_graph = sub_graph
        print(f"currently best score: {score}")

hub_node_1 = md.get_hub_nodes([best_match_graph])[0]
parent_sub_graphs = md.get_parents(action_attributes={"uuid": hub_node_1})
hub_node_2 = md.get_hub_nodes(parent_sub_graphs)[0]
print(hub_node_1, hub_node_2)
pg.plot(parent_sub_graphs)




