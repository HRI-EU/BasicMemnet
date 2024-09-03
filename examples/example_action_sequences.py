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

md_train = memnet.DSL()
md_test = memnet.DSL()
md_train.import_gml(os.path.join(sys.path[0], "data", "action_sequences", "train_graph.gml"))
md_test.import_gml(os.path.join(sys.path[0], "data", "action_sequences", "test_graph.gml"))
pg = plot_graph.PlotGraph()

train_sub_graphs = md_train.get_stm_actions(action_attributes={"type": "action"})
test_sub_graphs = md_test.get_stm_actions(action_attributes={"type": "action"})

best_match_score = 0
best_match_graph = None

for test_sub_graph in test_sub_graphs:
    for train_sub_graph in train_sub_graphs:
        score = md_train.find_best_matching_path(sub_graph_1=test_sub_graph,
                                                 sub_graph_2=train_sub_graph, link_type="has_next")
        if score > best_match_score:
            best_match_score = score
            best_matching_graphs = [test_sub_graph, train_sub_graph]
    best_matching_train_uuids = md_train.get_hub_nodes([train_sub_graph])
    best_matching_test_uuids = md_test.get_hub_nodes([test_sub_graph])
    parent_test_subgraphs = md_test.get_parents(action_attributes={"uuid": best_matching_test_uuids[0]})
    parent_train_subgraphs = md_train.get_parents(action_attributes={"uuid": best_matching_train_uuids[0]})
    parent_test_subgraph = list(parent_test_subgraphs[0].nodes(data=True))
    parent_train_subgraph = list(parent_train_subgraphs[0].nodes(data=True))
    print(parent_test_subgraph[0][1]["utterances"], parent_train_subgraph[0][1]["utterances"])
    print(100*"=")




