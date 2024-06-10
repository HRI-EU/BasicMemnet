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

import unittest
import sys
import os
from basicmemnet import memnet


class TestMemNet(unittest.TestCase):
    def test_wordnet(self):
        md = memnet.DSL(use_wordnet=True, json_file=os.path.join(sys.path[0], "data", "action_patterns.json"))
        sub_graphs = md.get_ltm_objects(object_attributes={"utterances": ["glass"]})
        self.assertEqual(len(sub_graphs), 7)

    def test_mtm_action(self):
        md = memnet.DSL(use_wordnet=False, json_file=os.path.join(sys.path[0], "data", "action_patterns.json"))
        sub_graphs = md.get_stm_actions(action_attributes={"utterances": ["hand over"]},
                                        object_attributes={"utterances": ["glass"]})
        self.assertEqual(len(sub_graphs), 1)

    def test_stm_objects(self):
        md = memnet.DSL(use_wordnet=False, json_file=os.path.join(sys.path[0], "data", "action_patterns.json"))
        sub_graphs = md.get_stm_objects(object_attributes={"utterances": ["glass"]})
        self.assertEqual(len(sub_graphs), 1)


if __name__ == "__main__":
    unittest.main()
