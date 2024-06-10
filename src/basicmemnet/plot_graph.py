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
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.colors as pltcolors
import math


class PlotGraph:
    def __init__(self):
        self.figsize = (15, 10)
        self.edge_colors = {"ltm": None, "mtm": "darkgray", "stm": "red"}

    def plot(self, graphs, title=None):
        n = len(graphs)
        cols = int(math.ceil(math.sqrt(n)))
        rows = 1 if cols == 0 else int(math.ceil(n / cols))

        fig = plt.figure(figsize=self.figsize)

        def on_key_press(event):
            plt.close(fig)

        fig.canvas.mpl_connect("key_press_event", on_key_press)

        if title:
            fig.suptitle(title, fontsize=16)

        for i, graph in enumerate(graphs, 1):
            ax = plt.subplot(rows, cols, i)

            type_color = {
                "action": "red",
                "object": "blue",
                "tool": "green",
                "state": "gray",
                "lemma": "yellow",
            }

            edge_colors = []
            for node in graph.nodes:
                attr = graph.nodes[node]
                edge_color = None
                if ("memory" in attr) and (attr["memory"] in self.edge_colors.keys()):
                    if self.edge_colors[attr["memory"]] is None:
                        r, g, b, _ = pltcolors.to_rgba(type_color[attr["type"]])
                        edge_color = (r, g, b, 0.2)
                    else:
                        r, g, b, _ = pltcolors.to_rgba(self.edge_colors[attr["memory"]])
                        edge_color = (r, g, b, 1.0)
                else:
                    edge_color = (0.0, 0.0, 0.0, 1.0)
                edge_colors.append(edge_color)

            colors = []
            for node in graph.nodes:
                attr = graph.nodes[node]
                if ("type" in attr) and (attr["type"] in type_color.keys()):
                    node_type = attr["type"]
                    r, g, b, _ = pltcolors.to_rgba(type_color[node_type])
                else:
                    r = g = b = 0.0
                colors.append((r, g, b, 0.2))

                try:
                    # Attempt to use pydot_layout
                    pos = nx.nx_pydot.pydot_layout(graph, prog="dot")
                except:
                    # Fallback to spring_layout if pydot_layout is not available
                    print("pydot_layout failed, using spring_layout instead.")
                    pos = nx.spring_layout(graph)

            labels = dict()
            for n in graph.nodes:
                label = ""
                if "utterances" in graph.nodes[n]:
                    utterances = graph.nodes[n].get("utterances")
                    uuid = graph.nodes[n].get("uuid")
                    accessid = graph.nodes[n].get("accessid")
                    utterance_text = (
                        utterances if isinstance(utterances, str) else utterances[0]
                    )
                    # label = accessid if accessid else f"{utterance_text}\n{uuid[-4:]}"
                    label = accessid if accessid else utterance_text
                labels.update({n: label})

            nx.draw_networkx_nodes(
                graph,
                pos,
                node_color=colors,
                edgecolors=edge_colors,  # Border color
                linewidths=2,  # Width of the border, adjust as needed
            )

            nx.draw_networkx_edges(
                graph,
                pos,
                arrows=True,
                edge_color="black",  # Replace 'edge_colors' with your edge color array
                arrowstyle="->",
            )

            nx.draw_networkx_labels(
                graph,
                pos,
                labels=labels,
                font_size=10,
            )

            edge_labels = nx.get_edge_attributes(graph, "link_type")
            nx.draw_networkx_edge_labels(
                graph, pos, edge_labels=edge_labels, font_color="black", font_size=8
            )

            rect = patches.Rectangle(
                (0, 0),
                1,
                1,
                linewidth=2,
                edgecolor="black",
                facecolor="none",
                transform=ax.transAxes,
            )
            ax.add_patch(rect)

        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        plt.show()
