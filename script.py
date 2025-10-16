# ------------------------------------------------------------------------------
# This module flattens a decision tree into a set of conjunctive strategies.

# Key design points:

#     - Parsing supports node/leaf lines, OR groups written as [ ... ||or|| ... ],
#     and operators limited to = and !=.
    
#     - DFS traversal with correct OR semantics:
#     >> YES branch → creates one DFS branch per disjunct condition (A ∨ B becomes
#     separate paths with A, with B).
#     >> NO branch  → adds the conjunction of the negations of all disjuncts (A ∧ B),
#     per De Morgan’s law.
    
#     - Contradiction pruning, impossible states are deleted. Exemple : x=4 with x!=4
#     or x=4 with x=5.

#     - Simplifies constraints by discarding any accumulated x!= once an x=
#     equality is set for the same feature.
    
#     - Low memory footprint with LazyTreeFileScanner by reading the file on demand 
#     and not loading the entire tree into memory, keeping the memory usage below 
#     the input file size constraint.
# ------------------------------------------------------------------------------

import re
from typing import List, Tuple, Dict, Any, Optional
import sys

# ------------------------------------------------------------------------------
# Parsing a line of the tree with regex

NODE_LINE_REGEX = re.compile(r"^\s*(\d+)\s*:\s*(.+?)\s*$")
LEAF_REGEX = re.compile(r"^\s*leaf\s*=\s*([+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)\s*$")
CONDITION_REGEX = re.compile(r"^\[\s*(.*?)\s*\]\s*yes\s*=\s*(\d+)\s*,\s*no\s*=\s*(\d+)\s*$")
OR_SPLITTER_REGEX = re.compile(r"\s*\|\|or\|\|\s*")

def parse_condition_item(condition_text: str) -> Dict[str, Any]:
    """
    Parse a simple condition of the form: <feature> (=|!=) <value>.
    """
    condition_text = condition_text.strip()
    if "!=" in condition_text:
        feature_name, value_text = condition_text.split("!=", 1)
        return {"feature": feature_name.strip(), "op": "!=", "value": value_text.strip()}
    if "=" in condition_text:
        feature_name, value_text = condition_text.split("=", 1)
        return {"feature": feature_name.strip(), "op": "=", "value": value_text.strip()}
    raise ValueError(f"Invalid condition (expected '=' or '!='): {condition_text!r}")

def parse_tree_line(raw_line: str) -> Optional[Dict[str, Any]]:
    """
    Parse one text line describing a tree node and return:
      (node_id, node_object)
    where node_object is either:
      - {"type": "leaf", "value": <float>}
      - {"type": "cond", "conds": [list of OR conditions], "yes": <int>, "no": <int>}
    If the line does not match the expected pattern, return None.
    """
    raw_line = raw_line.strip()
    if not raw_line:
        return None

    node_line = NODE_LINE_REGEX.match(raw_line)
    if not node_line:
        return None

    node_payload = node_line.group(2).strip()

    # Leaf node
    leaf_match = LEAF_REGEX.match(node_payload)
    if leaf_match:
        return {"type": "leaf", "value": float(leaf_match.group(1))}

    # Conditional node
    cond_match = CONDITION_REGEX.match(node_payload)
    if cond_match:
        conds_str, yes_id_str, no_id_str = cond_match.groups()
        or_conditions: List[Dict[str, Any]] = []
        if conds_str:
            for part in OR_SPLITTER_REGEX.split(conds_str):
                part = part.strip()
                if part:
                    or_conditions.append(parse_condition_item(part))
        return  {
            "type": "cond",
            "conds": or_conditions,  
            "yes": int(yes_id_str),
            "no": int(no_id_str),
        }

    return None

# ------------------------------------------------------------------------------
# Memory O(1) node reader, lazy scan by id

class LazyTreeFileScanner:
    """
    Scans a text tree file and finds a node by its id O(1) memory, linear read.
    """
    def __init__(self, file_path: str, encoding: str = "utf-8") -> None:
        self.file_path = file_path
        self.encoding = encoding

    def get_node_by_id(self, node_id: int) -> Dict[str, Any]:
        prefix = f"{node_id}:"
        with open(self.file_path, "r", encoding=self.encoding) as f:
            for line in f:
                if not line.strip():
                    continue
                if line.lstrip().startswith(prefix):
                    parsed = parse_tree_line(line)
                    if parsed is None:
                        break
                    node_obj = parsed
                    return node_obj
        raise KeyError(f"Node id {node_id} not found in {self.file_path}")

# ------------------------------------------------------------------------------
# Compact state representation for pruning contradictions
# feature -> {"eq": value_or_None, "neq": set()}

StateType = Tuple[Dict[str, Dict[str, Any]], List[str]]  # (feature_state_map, feature_order)

def add_condition_to_state(current_state: StateType,
                           cond: Dict[str, Any]) -> Optional[StateType]:
    """
    Add one condition (= or !=) into the current state.
    - If a contradiction is found -> return None (branch is pruned).
    - Otherwise, return a NEW state (shallow copy).
   
    Example of current_state ({'A': {'eq': '1', 'neq': set()}}, ['A']) :
    (
        {
            "browser": {"eq": "7", "neq": {"8", "9"}},
            "os": {"eq": None, "neq": {"linux"}}
        },
        ["browser", "os"]  
    )
    Example of cond= {'feature': 'A', 'op': '=', 'value': '1'} :
    """
    feature_name = cond["feature"]
    operator_str = cond["op"]
    value_text = cond["value"]

    feature_state_map, feature_order = current_state

    new_feature_state_map = feature_state_map.copy()
    if feature_name in new_feature_state_map:
        entry = new_feature_state_map[feature_name].copy()
        current_eq_value = entry["eq"]
        current_neq_values = set(entry["neq"])
    else:
        entry = {"eq": None, "neq": set()}
        current_eq_value = None
        current_neq_values = set()

    if operator_str == "=":
        if current_eq_value is not None and current_eq_value != value_text:
            return None
        if value_text in current_neq_values:
            return None
        entry["eq"] = value_text
        entry["neq"] = set()  
    else:  
        if current_eq_value is not None and current_eq_value == value_text:
            return None
        current_neq_values.add(value_text)
        entry["eq"] = current_eq_value
        entry["neq"] = current_neq_values

    new_feature_state_map[feature_name] = entry

    if feature_name not in feature_state_map:
        new_feature_order = feature_order + [feature_name]
    else:
        new_feature_order = feature_order

    return new_feature_state_map, new_feature_order

def add_all_conditions_to_state(current_state: StateType,
                                 conds: List[Dict[str, Any]]) -> Optional[StateType]:
    """
    Add a list conditions to a state, returns None if any contradiction occurs.
    """
    updated_state: Optional[StateType] = current_state
    for cond in conds:
        updated_state = add_condition_to_state(updated_state, cond)
        if updated_state is None:
            return None
    return updated_state

def negate_condition(cond: Dict[str, Any]) -> Dict[str, Any]:
    """
    Negate a simple condition (= <-> !=) for the NO branch.
    """
    return {
        "feature": cond["feature"],
        "op": "=" if cond["op"] == "!=" else "!=",
        "value": cond["value"],
    }

def format_state_as_strategy(state: StateType) -> str:
    """
    Format the current state into a readable conjunction: feat=val & feat!=val2 & ...
    """
    feature_state_map, feature_order = state
    parts: List[str] = []
    for feature_name in feature_order:
        entry = feature_state_map[feature_name]
        if entry["eq"] is not None:
            parts.append(f"{feature_name}={entry['eq']}")
        else:
            for forbidden_value in entry["neq"]:
                parts.append(f"{feature_name}!={forbidden_value}")
    return " & ".join(parts)

# ------------------------------------------------------------------------------
# Flatten tree into strategies with contradiction pruning

def flatten_tree_file(input_path: str, output_path: str, root_node_id: int = 0) -> None:
    """
    Read a binary tree with OR between conditions using '=' and '!=',
    and generate all AND only strategies, writing them to output_path.

    - YES branch: one branch for each individual OR condition.
    - NO branch: all OR conditions are negated and combined.
    - Any contradiction like browser=7 then browser=8 > branch is skipped.

    Memory complexity: O(1) outside of depth first search stack and current path state.
    """
    scanner = LazyTreeFileScanner(input_path)

    initial_state: StateType = ({}, [])
    dfs_stack: List[Tuple[int, StateType]] = [(root_node_id, initial_state)]

    with open(output_path, "w", encoding="utf-8") as out:
        while dfs_stack:
            current_node_id, current_state = dfs_stack.pop()
            node_obj = scanner.get_node_by_id(current_node_id)

            if node_obj["type"] == "leaf":
                strategy_text = format_state_as_strategy(current_state)
                line = f"{strategy_text} : {node_obj['value']}".strip()
                out.write(line + "\n")
                continue

            or_conditions: List[Dict[str, Any]] = node_obj["conds"]

            # NO branch: add all negated conditions; skip if contradiction
            negated_conds = [negate_condition(c) for c in or_conditions]
            no_branch_state = add_all_conditions_to_state(current_state, negated_conds)
            if no_branch_state is not None:
                dfs_stack.append((node_obj["no"], no_branch_state))

            # YES branch: one branch per cond, each with that cond added
            for cond in or_conditions:
                yes_branch_state = add_condition_to_state(current_state, cond)
                if yes_branch_state is not None:
                    dfs_stack.append((node_obj["yes"], yes_branch_state))

# ------------------------------------------------------------------------------
# CLI entry point

if __name__ == "__main__":

    if len(sys.argv) == 3:
        flatten_tree_file(sys.argv[1], sys.argv[2], root_node_id=0)
    else:
        print("Please use the command below: python script.py <tree_to_convert.txt> <strategies.txt>")


