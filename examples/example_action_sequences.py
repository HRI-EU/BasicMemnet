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
import copy
import json
from basicmemnet import memnet
from basicmemnet import plot_graph

md_train = memnet.DSL()
md_test = memnet.DSL()
md_train.import_gml(os.path.join(sys.path[0], "data", "action_sequences", "train_graph.gml"))
md_test.import_gml(os.path.join(sys.path[0], "data", "action_sequences", "test_graph.gml"))
pg = plot_graph.PlotGraph()

train_sub_graphs = md_train.get_stm_actions(action_attributes={"type": "action"})
test_sub_graphs = md_test.get_stm_actions(action_attributes={"type": "action"})

results = {"train_samples": len(train_sub_graphs), "test_samples": len(test_sub_graphs), "matches": []}
true_positives = 0
false_positives = 0
iter_count = 0

for test_sub_graph in test_sub_graphs:
    with open(os.path.join(sys.path[0], "data", "action_sequences", "results.json"), 'w') as f:
        json.dump(results, f)
    best_matching_score = 0
    best_matching_graphs = None
    for train_sub_graph in train_sub_graphs:
        score = md_train.find_best_matching_path(sub_graph_1=test_sub_graph,
                                                 sub_graph_2=train_sub_graph, link_type="has_next")
        if score > best_matching_score:
            best_matching_score = score
            best_matching_graphs = [copy.deepcopy(test_sub_graph), copy.deepcopy(train_sub_graph)]
    train_parent = test_parent = log = None
    if best_matching_graphs:
        parent_test_paths = md_test.get_parents(sub_graph=best_matching_graphs[0], link_type="has_element")
        parent_train_paths = md_train.get_parents(sub_graph=best_matching_graphs[1], link_type="has_element")
        if (len(parent_test_paths) == 1) and (len(parent_train_paths) == 1):
            test_parent = parent_test_paths[0][0]["utterances"][0]
            train_parent = parent_train_paths[0][0]["utterances"][0]
        else:
            log = "parent is ambiguous"
    match = False
    if train_parent and test_parent:
        if train_parent.split("_")[3] == test_parent.split("_")[3]:
            match = True
    if match:
        true_positives += 1
    else:
        false_positives += 1
    iter_count += 1
    result = {"count": f"{iter_count}/{len(test_sub_graphs)}",
              "accuracy": (true_positives/(true_positives+false_positives)), "match": match,
              "samples": (train_parent, test_parent), "score": score, "log": log}
    print(result)
    results["matches"].append(result)







