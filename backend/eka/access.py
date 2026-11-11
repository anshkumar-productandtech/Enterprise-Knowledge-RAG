"""Who can read what.

A page belongs to exactly one access group, decided by its path. A role maps to
the set of groups it may read. Retrieval filters on the group inside the SQL
query, so a restricted chunk never reaches the reranker or the model. Filtering
in the prompt ("don't mention finance docs") is not access control.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml

from .settings import BACKEND_DIR

CORPUS_CONFIG = BACKEND_DIR / "config" / "corpus.yaml"

# Group and role names end up inside a SQL filter built by the vector store
# (string-interpolated, not parameterised), so they are restricted to a safe
# alphabet here and are never taken from user input.
_SAFE_NAME = re.compile(r"^[a-z][a-z0-9_]{0,31}$")


class UnknownRole(ValueError):
    pass


@dataclass(frozen=True)
class Role:
    name: str
    label: str
    description: str
    groups: tuple[str, ...]


@dataclass(frozen=True)
class AccessPolicy:
    site_url: str
    include: tuple[str, ...]
    rules: tuple[tuple[str, str], ...]  # (prefix, group), longest prefix first
    default_group: str
    roles: dict[str, Role]

    def group_for_path(self, rel_path: str) -> str:
        """rel_path is relative to the content dir, e.g. handbook/finance/expenses/_index.md"""
        p = rel_path.strip("/")
        for prefix, group in self.rules:
            if p == prefix or p.startswith(prefix + "/") or p.startswith(prefix + "."):
                return group
        return self.default_group

    def groups_for_role(self, role: str) -> list[str]:
        if role not in self.roles:
            raise UnknownRole(role)
        return list(self.roles[role].groups)

    @property
    def all_groups(self) -> set[str]:
        return {g for _, g in self.rules} | {self.default_group}


def load_policy(path: Path = CORPUS_CONFIG) -> AccessPolicy:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))

    rules = sorted(
        ((r["prefix"].strip("/"), r["group"]) for r in raw["access_rules"]),
        key=lambda r: len(r[0]),
        reverse=True,
    )
    roles = {
        name: Role(name, spec["label"], spec.get("description", ""), tuple(spec["groups"]))
        for name, spec in raw["roles"].items()
    }
    policy = AccessPolicy(
        site_url=raw["site_url"].rstrip("/"),
        include=tuple(p.strip("/") for p in raw["include"]),
        rules=tuple(rules),
        default_group=raw["default_group"],
        roles=roles,
    )

    names = policy.all_groups | set(roles) | {g for r in roles.values() for g in r.groups}
    bad = sorted(n for n in names if not _SAFE_NAME.match(n))
    if bad:
        raise ValueError(f"Unsafe group/role names in {path.name}: {bad}")
    unknown = {g for r in roles.values() for g in r.groups} - policy.all_groups
    if unknown:
        raise ValueError(f"Roles reference groups with no access rule: {sorted(unknown)}")
    return policy


@lru_cache
def get_policy() -> AccessPolicy:
    # EKA_CORPUS_CONFIG lets the smoke test swap in the fictional fixture corpus.
    return load_policy(Path(os.environ.get("EKA_CORPUS_CONFIG", CORPUS_CONFIG)))
