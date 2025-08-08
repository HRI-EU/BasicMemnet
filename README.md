### Introduction

This is a simplified graph implementation of Memory Nets [1], a high-level knowledge representation for intelligent 
agents. The main intention using this memory is to store observations from a physical environment in a situational 
framing. On an abstract level, such a framing always consists of _subjects_, that execute a certain _action_ on 
_objects_ and through this, change _states_ of the involved participants. These four types are called Concept 
Domains which are represented as four independent inheritance hierarchies, as depicted in Figure 1 upper part. As 
Concept Domains are assumed to be long time stable and generally valid, they are indicated as Long Term Memory (LTM),
similar to the TBox.

Each observation is encapsulated into an Action Pattern, that extends the basic Concept Domains by further situational 
roles. For example, imagine we have a person 1 (which is of type _Subject_) that hands over (_Action_) a glass (_Object_) to 
another person 2. As person 1 executes the action, it jumps into the role of an actor, while 
it also remains of type _Subject_. Person 2, also of type _Subject_, is now in the role of a receiver, as it is the target 
location of the handed over glass. In this implementation of Memory Nets, such a role is indicated by a dedicated link 
"has_recipient". In the lower part of Figure 1, the resulting Memory Nets graph is illustrated. Currrently, following roles are supported:
"object", "tool", "location", "time" and "agent", which you can also find in the code [Memory Nets Roles](https://github.com/HRI-EU/BasicMemnet/blob/78dc00f11ba088b9b7608831632773dedd4cae45/src/basicmemnet/memnet.py#L50C1-L50C84).

<figure>
    <img src="data/memnet.png" alt="Memory Nets Concept Domains" style="width:800px;">
    <figcaption>Figure 1: The four Memory Nets Concept Domains according to [1].</figcaption>
</figure>

### Creating an initial graph

The following sample JSON-file shows how to create an initial Memory Nets Graph as list of dictionaries. Each single dictionary is represents
a node in the graph. Nodes can be linked by specifying the parent node attributes. It is necessary to use a unique identifier,
like an uuid or synset - if WordNet is used.
). You can assign any attributes to the node providing ```node_attributes``` as dictionary.
To ensure a proper reasoning, you **must** use at least the node attributes provided below. Optionally you can attach ```states```
in natural language, like "green" or "tall". 

```json
[{
"link": "spec_to",
"parent_attributes": {"accessid": ["glass.n.01"]},
"node_attributes": {
  "type": "object",
  "utterances": ["glass"],
  "timestamp": 1714741106.3516276,
  "memory": "stm",
  "uuid": "658190c06eccd77ab5dc84d4"
}
}]
```

The minimum set of attributes must contain following values:


- **type**: Fixed string value. Allowed values are: "action", "object", "tool", "location", "time", "agent"
- **utterances**: Array of strings. Represents spoken or intended phrases, such as ["glass", "cup", "bottle"]. 
- **timestamp**: Numeric value representing the Unix epoch time of the inserted node, e.g. using _time.time()_.
- **memory**: String. Specifies the type of memory storage to use. Allowed values are: "stm", "ltm" or "mtm"
- **uuid**: String formatted as a universally unique identifier (UUID). Used for unique identification a node.


UUIDs allow for a proper ID management and it is highly recommended to make use of it for linking nodes. You can easiliy create a UUID by 

```python 
from bson import ObjetID
uuid = str(ObjectID())
``` 

### Installation

```bash
git clone https://github.com/HRI-EU/BasicMemnet.git
cd BasicMemnet
python -m venv venv
```

1. If you use **Linux**:
```bash
    source venv/bin/activate 
```

2. If you use **Windows**, it is additionally recommended to download GraphViz from https://graphviz.org/download, locate the Graphviz\bin folder and add it to the PATH variable in your system variables. Otherwise you will use the built-in graph layout from networkX.
```bash
    call venv\Scripts\activate # Windows
```

```bash
pip install -e .
```

### Examples

You can find a simple example script that loads an action pattern example json file in examples/example.py. In the constructor, you 
can switch between making use of WordNet or not. By default, it is switched off for a fast initial run, which you can find here (cf. [Memory Nets Example](https://github.com/HRI-EU/BasicMemnet/blob/master/examples/example.py#L42).

```bash
python -m examples.simple
```

For a more complex example published at [5], predicting actions on the KIT Bimanual Action Dataset [4], run:

```bash
python -m examples.semantics25
```

#### References

1. Eggert, J., Deigmoeller, J., Fischer, L., and Richter, A. (2019). Memory Nets: Knowledge representation
for intelligent agent operations in real world. International Joint Conference on Knowledge Discovery, Knowledge 
Engineering, and Knowledge Management.
2. Eggert, J., Deigmoeller, J., Fischer, L., and Richter, A. (2020). Action representation for intelligent agents
using Memory Nets. In Communications in Computer and Information Science.
3. Deigmoeller, J., Smirnov, P., Wang, C., Takeuchi, J., and Eggert, J. (2022). Situational question answering using 
memory nets. International Joint Conference on Knowledge Discovery, Knowledge Engineering, and Knowledge Management.
4. F. Krebs, A. Meixner, I. Patzer and T. Asfour. “The KIT Bimanual Manipulation Dataset” 20th International Conference on Humanoid Robots, 2020.
5. M. Arustashvili, J. Deigmoeller, H. Paulheim. "Knowledge Graph Completion for Action Prediction on Situational Graphs – A Case Study on Household Tasks" 21st International Conference on Semantic Systems, 2025 
