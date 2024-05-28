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
from nltk.corpus import wordnet as wn
from bson import ObjectId
import os
import sys
import nltk


def download_wordnet(custom_folder: str):
    if not os.path.exists(custom_folder):
        os.makedirs(custom_folder)
    nltk.data.path.append(custom_folder)
    nltk.download("wordnet", download_dir=custom_folder)


def create_wordnet_graph(limit=None):
    G = nx.DiGraph()
    synset_id_map = {}  # Map from synset name to node ID

    # Iterate through all synsets in WordNet
    for synset in wn.all_synsets():
        if limit and len(G) >= limit:
            break

        # Determine the type of the synset
        synset_type = "state"  # Default to 'state' for adjectives and adverbs
        if synset.pos() == "n":
            synset_type = "object"
        elif synset.pos() == "v":
            synset_type = "action"

        if synset_type in ["object", "action"]:
            # Check if the node for the current synset already exists
            if synset.name() not in synset_id_map:
                node_id = str(ObjectId())
                synset_id_map[synset.name()] = node_id
                G.add_node(
                    node_id,
                    accessid=synset.name(),
                    utterances=synset.lemma_names(),
                    type=synset_type,
                    uuid=node_id,
                    memory="ltm",
                )

            # Add edges for 'spec_to' link_type
            for hypernym in synset.hypernyms():
                if hypernym.name() not in synset_id_map:
                    hypernym_id = str(ObjectId())
                    synset_id_map[hypernym.name()] = hypernym_id
                    G.add_node(
                        hypernym_id,
                        accessid=hypernym.name(),
                        utterances=hypernym.lemma_names(),
                        type=synset_type,
                        uuid=hypernym_id,
                        memory="ltm",
                    )
                else:
                    hypernym_id = synset_id_map[hypernym.name()]

                G.add_edge(
                    hypernym_id, synset_id_map[synset.name()], link_type="spec_to"
                )

    return G


custom_nltk_path = os.path.join(sys.path[0], "data")
download_wordnet(custom_nltk_path)
