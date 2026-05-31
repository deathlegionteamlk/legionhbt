import json
import time
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from collections import defaultdict
import random


@dataclass
class Thought:
    content: str
    thought_type: str
    parent_id: Optional[str] = None
    children: List[str] = field(default_factory=list)
    score: float = 0.0
    depth: int = 0
    visited: bool = False
    id: str = field(default_factory=lambda: str(int(time.time() * 1000000)))


@dataclass
class Action:
    action_type: str
    params: Dict[str, Any]
    result: Optional[str] = None
    success: bool = False
    timestamp: float = field(default_factory=time.time)


class ReActPattern:
    def __init__(self, max_iterations: int = 10):
        self.max_iterations = max_iterations
        self.thoughts: List[Thought] = []
        self.actions: List[Action] = []
        self.observations: List[str] = []

    def reason(self, context: str, question: str, available_tools: List[str]) -> Thought:
        thought_content = f"Given: {context}\nQuestion: {question}\n"
        thought_content += f"Available tools: {', '.join(available_tools)}\n"
        thought_content += "I need to break this down into steps..."

        thought = Thought(
            content=thought_content,
            thought_type="reasoning"
        )
        self.thoughts.append(thought)
        return thought

    def act(self, thought: Thought, tool_executor: Callable[[str, Dict], str],
            tool_name: str, params: Dict[str, Any]) -> Action:
        try:
            result = tool_executor(tool_name, params)
            action = Action(
                action_type=tool_name,
                params=params,
                result=result,
                success=True
            )
        except Exception as e:
            action = Action(
                action_type=tool_name,
                params=params,
                result=str(e),
                success=False
            )

        self.actions.append(action)
        return action

    def observe(self, action: Action) -> str:
        observation = f"Action '{action.action_type}' completed with result: {action.result}"
        self.observations.append(observation)
        return observation

    def run(self, question: str, context: str, available_tools: List[str],
            tool_executor: Callable[[str, Dict], str]) -> Dict[str, Any]:
        iteration = 0
        final_answer = None

        while iteration < self.max_iterations and not final_answer:
            thought = self.reason(context, question, available_tools)

            if "answer" in thought.content.lower() or iteration == self.max_iterations - 1:
                final_answer = thought.content
                break

            tool_name = self._select_tool(thought.content, available_tools)
            if tool_name:
                params = self._extract_params(thought.content)
                action = self.act(thought, tool_executor, tool_name, params)
                observation = self.observe(action)
                context += f"\nObservation: {observation}"

            iteration += 1

        return {
            "thoughts": [t.content for t in self.thoughts],
            "actions": [a.__dict__ for a in self.actions],
            "observations": self.observations,
            "final_answer": final_answer or self.thoughts[-1].content if self.thoughts else "No answer",
            "iterations": iteration
        }

    def _select_tool(self, thought: str, available_tools: List[str]) -> Optional[str]:
        for tool in available_tools:
            if tool.lower() in thought.lower():
                return tool
        return available_tools[0] if available_tools else None

    def _extract_params(self, thought: str) -> Dict[str, Any]:
        return {"query": thought}


class TreeOfThoughts:
    def __init__(self, branching_factor: int = 3, max_depth: int = 5):
        self.branching_factor = branching_factor
        self.max_depth = max_depth
        self.nodes: Dict[str, Thought] = {}
        self.root_id: Optional[str] = None

    def build_tree(self, problem: str, generate_thoughts_fn: Callable[[str, int], List[str]],
                   evaluate_fn: Callable[[str], float]) -> str:
        root = Thought(content=problem, thought_type="root", depth=0)
        self.root_id = root.id
        self.nodes[root.id] = root

        self._expand_node(root, generate_thoughts_fn, evaluate_fn)
        return self._find_best_path()

    def _expand_node(self, node: Thought, generate_thoughts_fn: Callable, evaluate_fn: Callable):
        if node.depth >= self.max_depth:
            return

        candidates = generate_thoughts_fn(node.content, self.branching_factor)

        for candidate in candidates:
            score = evaluate_fn(candidate)
            child = Thought(
                content=candidate,
                thought_type="candidate",
                parent_id=node.id,
                depth=node.depth + 1,
                score=score
            )
            self.nodes[child.id] = child
            node.children.append(child.id)

            if score < 0.8:
                self._expand_node(child, generate_thoughts_fn, evaluate_fn)

    def _find_best_path(self) -> str:
        if not self.root_id:
            return ""

        best_path = []
        current_id = self.root_id

        while current_id:
            node = self.nodes[current_id]
            best_path.append(node.content)

            if not node.children:
                break

            best_child = max(
                [self.nodes[cid] for cid in node.children],
                key=lambda x: x.score
            )
            current_id = best_child.id

        return " -> ".join(best_path)

    def backtrack(self, node_id: str) -> List[str]:
        path = []
        current_id = node_id

        while current_id:
            node = self.nodes.get(current_id)
            if not node:
                break
            path.append(node.content)
            current_id = node.parent_id

        return list(reversed(path))

    def get_all_paths(self) -> List[List[str]]:
        paths = []

        def traverse(node_id: str, current_path: List[str]):
            node = self.nodes.get(node_id)
            if not node:
                return

            current_path = current_path + [node.content]

            if not node.children:
                paths.append(current_path)
                return

            for child_id in node.children:
                traverse(child_id, current_path)

        if self.root_id:
            traverse(self.root_id, [])

        return paths


class GraphOfThoughts:
    def __init__(self):
        self.nodes: Dict[str, Thought] = {}
        self.edges: Dict[str, List[str]] = defaultdict(list)
        self.edge_weights: Dict[tuple, float] = {}

    def add_node(self, content: str, thought_type: str = "thought") -> str:
        node = Thought(content=content, thought_type=thought_type)
        self.nodes[node.id] = node
        self.edges[node.id] = []
        return node.id

    def add_edge(self, from_id: str, to_id: str, weight: float = 1.0):
        if from_id in self.nodes and to_id in self.nodes:
            self.edges[from_id].append(to_id)
            self.edge_weights[(from_id, to_id)] = weight

    def aggregate(self, node_ids: List[str], aggregation_type: str = "concat") -> str:
        contents = [self.nodes[nid].content for nid in node_ids if nid in self.nodes]

        if aggregation_type == "concat":
            return " ".join(contents)
        elif aggregation_type == "sum":
            return f"Combined: {', '.join(contents)}"
        elif aggregation_type == "vote":
            return self._voting_mechanism(contents)
        else:
            return " ".join(contents)

    def _voting_mechanism(self, contents: List[str]) -> str:
        if not contents:
            return ""
        counts = defaultdict(int)
        for c in contents:
            counts[c] += 1
        return max(counts.items(), key=lambda x: x[1])[0]

    def find_path(self, start_id: str, end_id: str) -> Optional[List[str]]:
        visited = set()
        queue = [(start_id, [start_id])]

        while queue:
            current, path = queue.pop(0)

            if current == end_id:
                return path

            if current in visited:
                continue

            visited.add(current)

            for neighbor in self.edges.get(current, []):
                if neighbor not in visited:
                    queue.append((neighbor, path + [neighbor]))

        return None

    def get_neighbors(self, node_id: str) -> List[str]:
        return self.edges.get(node_id, [])

    def get_strongly_connected(self) -> List[List[str]]:
        visited = set()
        components = []

        def dfs(node_id: str, component: List[str]):
            visited.add(node_id)
            component.append(node_id)
            for neighbor in self.edges.get(node_id, []):
                if neighbor not in visited:
                    dfs(neighbor, component)

        for node_id in self.nodes:
            if node_id not in visited:
                component = []
                dfs(node_id, component)
                if component:
                    components.append(component)

        return components

    def to_dict(self) -> Dict[str, Any]:
        return {
            "nodes": {k: {
                "content": v.content,
                "type": v.thought_type,
                "score": v.score
            } for k, v in self.nodes.items()},
            "edges": dict(self.edges),
            "weights": {f"{k[0]}->{k[1]}": v for k, v in self.edge_weights.items()}
        }


class SelfConsistencyChecker:
    def __init__(self, num_samples: int = 5, threshold: float = 0.6):
        self.num_samples = num_samples
        self.threshold = threshold

    def check(self, reasoning_fn: Callable[[], str]) -> Dict[str, Any]:
        samples = []
        for _ in range(self.num_samples):
            result = reasoning_fn()
            samples.append(result)

        consistency_score = self._calculate_consistency(samples)
        most_common = self._get_most_common(samples)

        return {
            "samples": samples,
            "consistency_score": consistency_score,
            "most_common_answer": most_common,
            "is_consistent": consistency_score >= self.threshold,
            "confidence": self._calculate_confidence(samples, most_common)
        }

    def _calculate_consistency(self, samples: List[str]) -> float:
        if not samples:
            return 0.0

        matches = 0
        total = len(samples) * (len(samples) - 1) // 2

        for i in range(len(samples)):
            for j in range(i + 1, len(samples)):
                if self._similarity(samples[i], samples[j]) > 0.8:
                    matches += 1

        return matches / total if total > 0 else 0.0

    def _similarity(self, a: str, b: str) -> float:
        a_words = set(a.lower().split())
        b_words = set(b.lower().split())

        if not a_words or not b_words:
            return 0.0

        intersection = len(a_words & b_words)
        union = len(a_words | b_words)

        return intersection / union if union > 0 else 0.0

    def _get_most_common(self, samples: List[str]) -> str:
        counts = defaultdict(int)
        for s in samples:
            counts[s] += 1
        return max(counts.items(), key=lambda x: x[1])[0]

    def _calculate_confidence(self, samples: List[str], answer: str) -> float:
        matches = sum(1 for s in samples if self._similarity(s, answer) > 0.8)
        return matches / len(samples) if samples else 0.0


class ReasoningEngine:
    def __init__(self):
        self.react = ReActPattern()
        self.tot = TreeOfThoughts()
        self.got = GraphOfThoughts()
        self.consistency = SelfConsistencyChecker()

    def solve_with_react(self, problem: str, tools: List[str],
                          tool_executor: Callable) -> Dict[str, Any]:
        return self.react.run(problem, "", tools, tool_executor)

    def solve_with_tot(self, problem: str, thought_generator: Callable,
                       evaluator: Callable) -> str:
        return self.tot.build_tree(problem, thought_generator, evaluator)

    def solve_with_got(self, thoughts: List[str], aggregations: List[str]) -> Dict[str, str]:
        node_ids = [self.got.add_node(t) for t in thoughts]

        for i in range(len(node_ids) - 1):
            self.got.add_edge(node_ids[i], node_ids[i + 1])

        results = {}
        for agg_type in aggregations:
            results[agg_type] = self.got.aggregate(node_ids, agg_type)

        return results

    def verify_consistency(self, reasoning_fn: Callable) -> Dict[str, Any]:
        return self.consistency.check(reasoning_fn)

    def hybrid_solve(self, problem: str, tools: List[str],
                     tool_executor: Callable) -> Dict[str, Any]:
        react_result = self.solve_with_react(problem, tools, tool_executor)

        def reasoning_fn():
            return react_result.get("final_answer", "")

        consistency = self.verify_consistency(reasoning_fn)

        return {
            "react_result": react_result,
            "consistency_check": consistency,
            "final_answer": consistency["most_common_answer"],
            "confidence": consistency["confidence"]
        }
