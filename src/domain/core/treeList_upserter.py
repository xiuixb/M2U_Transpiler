from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, MutableMapping, Optional


def _is_dict(x: Any) -> bool:
    return isinstance(x, dict)


def _is_list(x: Any) -> bool:
    return isinstance(x, list)


@dataclass
class TreeListUpserter:
    """
    目标：
    - items: [{"sys_type": "...", "value": {...}}]
    - tree: 多层级 dict，其中业务 bucket 为 list
    - 对 bucket 内根据 sys_name 做 upsert：
        * 同名覆盖
        * 不同名新增

    关键策略：
    - 扫描 tree 时“所有 list”并不等价于业务 bucket（避免标签爆炸）
    - 索引构建仅保留“唯一标签”（在 tree 中作为 list 节点 key 只出现一次的 key）

    特性：
    - 初始化时不传 tree
    - upsert 时传 tree
    - missing type：忽略
    - 支持 reindex(tree)
    """

    type_field: str = "sys_type"
    name_field: str = "sys_name"
    value_field: str = "value"

    _tree_id: Optional[int] = None
    _index: Optional[Dict[str, List[Dict[str, Any]]]] = None  # type_key -> bucket(list)

    # ---------- Tree scanning utilities ----------

    def _scan_list_key_counts(self, tree: MutableMapping[str, Any]) -> Dict[str, int]:
        """
        扫描 tree：统计所有 value 为 list 的 key 出现次数。
        """
        counts: Dict[str, int] = {}

        def dfs(node: Any) -> None:
            if not _is_dict(node):
                return
            for k, v in node.items():
                if _is_list(v):
                    counts[k] = counts.get(k, 0) + 1
                elif _is_dict(v):
                    dfs(v)

        dfs(tree)
        return counts

    def list_unique_tags(self, tree: MutableMapping[str, Any]) -> List[str]:
        """
        返回“唯一标签”：在 tree 中作为 list 节点 key 只出现一次的 key。
        该方法不依赖索引，不会触发 reindex。
        """
        counts = self._scan_list_key_counts(tree)
        return sorted([k for k, c in counts.items() if c == 1])

    def list_tags(self, tree: MutableMapping[str, Any]) -> List[str]:
        """
        返回 tree 中所有 list 节点的 key（去重，保持首次出现顺序）。
        该方法仅用于调试观察，不建议用于索引构建。
        """
        tags: List[str] = []
        seen: set[str] = set()

        def dfs(node: Any) -> None:
            if not _is_dict(node):
                return
            for k, v in node.items():
                if _is_list(v):
                    if k not in seen:
                        seen.add(k)
                        tags.append(k)
                elif _is_dict(v):
                    dfs(v)

        dfs(tree)
        return tags
    
    def list_unique_tags(self, tree: MutableMapping[str, Any]) -> List[str]:
        """
        返回 tree 中所有 list 节点的 key，但只保留“出现次数=1”的标签。
        即：任何重复出现的 key 都会被丢弃（不保留任何一个）。
        """
        counts: Dict[str, int] = {}

        def dfs_count(node: Any) -> None:
            if not _is_dict(node):
                return
            for k, v in node.items():
                if _is_list(v):
                    counts[k] = counts.get(k, 0) + 1
                elif _is_dict(v):
                    dfs_count(v)

        dfs_count(tree)

        tags: List[str] = []
        seen: set[str] = set()

        def dfs_collect(node: Any) -> None:
            if not _is_dict(node):
                return
            for k, v in node.items():
                if _is_list(v):
                    # 只保留唯一的（出现次数==1）
                    if counts.get(k, 0) == 1 and k not in seen:
                        seen.add(k)
                        tags.append(k)
                elif _is_dict(v):
                    dfs_collect(v)

        dfs_collect(tree)
        return tags


    # ---------- Index management ----------

    def reindex(self, tree: MutableMapping[str, Any]) -> None:
        """
        基于“唯一标签”构建索引：
            type_key -> bucket(list) 引用
        """
        unique_tags = set(self.list_unique_tags(tree))
        idx: Dict[str, List[Dict[str, Any]]] = {}

        def dfs(node: Any) -> None:
            if not _is_dict(node):
                return
            for k, v in node.items():
                if k in unique_tags and _is_list(v):
                    # 在“唯一标签”约束下，k 不会重复出现
                    if k in idx:
                        # 理论不应发生；若发生说明 tree 结构异常
                        raise ValueError(
                            f"Duplicate unique tag detected unexpectedly: '{k}'. "
                            f"Please check your tree structure."
                        )
                    idx[k] = v
                elif _is_dict(v):
                    dfs(v)

        dfs(tree)
        self._index = idx
        self._tree_id = id(tree)

    def _ensure_index(self, tree: MutableMapping[str, Any]) -> None:
        """
        若 tree 对象变化（id变化）或索引为空，则重建索引。
        """
        if self._index is None or self._tree_id != id(tree):
            self.reindex(tree)

    # ---------- Upsert operations ----------
    def upsert_one(self, tree: MutableMapping[str, Any], item: Dict[str, Any]) -> None:
            self._ensure_index(tree)

            type_key = item.get(self.type_field)
            value = item.get(self.value_field)

            if not isinstance(type_key, str) or not type_key:
                return
            if not _is_dict(value):
                raise TypeError(
                    f"item['{self.value_field}'] must be dict, got {type(value)} for type={type_key}"
                )

            bucket = self._index.get(type_key)
            if bucket is None:
                # missing type：忽略
                return

            name = value.get(self.name_field)

            # 没有 sys_name：默认新增（不做覆盖匹配）
            if not isinstance(name, str) or not name:
                bucket.append(value)
                return

            # 有 sys_name：在 bucket 内以 sys_name 为主键进行覆盖/新增
            for i, obj in enumerate(bucket):
                if not _is_dict(obj):
                    raise TypeError(f"Bucket '{type_key}' contains non-dict element: {type(obj)}")
                if obj.get(self.name_field) == name:
                    bucket[i] = value
                    return

            bucket.append(value)

    def upsert_many(self, tree: MutableMapping[str, Any], items: List[Dict[str, Any]]) -> MutableMapping[str, Any]:
        """
        批量 upsert
        """
        self._ensure_index(tree)
        for item in items:
            self.upsert_one(tree, item)
        return tree
