from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping


FORBIDDEN_KEYS = {
    "condition_id",
    "episode_id",
    "factor",
    "fault_injected",
    "reference_label",
    "deployed_output",
}


class ObservationFirewall:
    def __init__(self, layers: Mapping[str, list[str]]):
        self.layers = {name: tuple(fields) for name, fields in layers.items()}
        if set(self.layers) != {"R", "P", "H", "X"}:
            raise ValueError("layers must be exactly R, P, H, and X")
        previous: set[str] = set()
        for name in ("R", "P", "H", "X"):
            current = set(self.layers[name])
            if not previous <= current:
                raise ValueError("observation layers must be monotone")
            previous = current

    def view(self, layer: str, record: Mapping[str, Any]) -> dict[str, Any]:
        if layer not in self.layers:
            raise ValueError(f"unknown observation layer: {layer}")
        hidden = FORBIDDEN_KEYS.intersection(record)
        if hidden:
            raise ValueError(f"forbidden observation key: {sorted(hidden)[0]}")
        allowed = self.layers[layer]
        return {key: deepcopy(record[key]) for key in allowed if key in record}


def apply_ablation(view: Mapping[str, Any], groups: Mapping[str, list[str]]) -> dict[str, Any]:
    out = deepcopy(dict(view))
    for section, fields in groups.items():
        if section not in out or not isinstance(out[section], dict):
            continue
        for field in fields:
            out[section].pop(field, None)
    return out


NA = {"NOT_APPLICABLE"}


def _first(value: Any, default: Any = None) -> Any:
    if isinstance(value, list) and value:
        return value[0]
    return default


def _changed(view: Mapping[str, Any], field: str) -> bool | None:
    pre, post = view.get("pre_public"), view.get("post_public")
    if not isinstance(pre, dict) or not isinstance(post, dict) or field not in pre or field not in post:
        return None
    return pre[field] != post[field]


def infer_semantics(implementation: str, layer: str, view: Mapping[str, Any]) -> dict[str, set[str]]:
    """Apply the frozen, set-valued rules without experimental identifiers."""
    ret = view.get("return", [])
    pre = view.get("pre_public", {}) if isinstance(view.get("pre_public"), dict) else {}
    post = view.get("post_public", {}) if isinstance(view.get("post_public"), dict) else {}

    if implementation == "VESTA":
        out = {
            "input_acceptance": {"ACCEPTED", "REJECTED"},
            "return_source": {"CURRENT_INPUT", "RETAINED_CACHE"},
            "updated_stage": {"CACHE", "STATUS_AND_CACHE"},
            "state_transition": {"NONE", "HEALTHY_TO_UNTRUSTED"},
            "timestamp_meaning": NA.copy(),
        }
        if layer in {"H", "X"} and pre and post:
            pre_status, post_status = _first(pre.get("status")), _first(post.get("status"))
            cache_changed = _changed(view, "lastGoodPrice")
            if pre_status == "0" and post_status == "1":
                out.update(input_acceptance={"REJECTED"}, return_source={"RETAINED_CACHE"}, updated_stage={"STATUS_AND_CACHE"}, state_transition={"HEALTHY_TO_UNTRUSTED"})
            elif cache_changed:
                out.update(input_acceptance={"ACCEPTED"}, return_source={"CURRENT_INPUT"}, updated_stage={"CACHE"}, state_transition={"NONE"})
        return out

    if implementation == "AURIGAMI":
        out = {
            "input_acceptance": {"NOT_EVALUATED"}, "return_source": {"MAIN_AGGREGATE", "BACKUP_FEED"},
            "updated_stage": {"NONE"}, "state_transition": {"NONE"},
            "timestamp_meaning": {"MAIN_AGGREGATION_TIME", "BACKUP_PUBLICATION_TIME"},
        }
        flag = post.get("rawUnderlying")
        if isinstance(flag, list) and len(flag) >= 3:
            if flag[2] is True:
                out["return_source"] = {"MAIN_AGGREGATE"}; out["timestamp_meaning"] = {"MAIN_AGGREGATION_TIME"}
            elif flag[2] is False:
                out["return_source"] = {"BACKUP_FEED"}; out["timestamp_meaning"] = {"BACKUP_PUBLICATION_TIME"}
        return out

    if implementation == "FATHOM":
        success = ret[1] if isinstance(ret, list) and len(ret) > 1 else None
        acceptance = {"ACCEPTED"} if success is True else ({"REJECTED"} if success is False else {"NOT_EVALUATED"})
        out = {
            "input_acceptance": acceptance, "return_source": {"DELAYED_RECORD"},
            "updated_stage": {"NONE", "DELAYED_AND_LATEST"} if success is True else {"NONE"},
            "state_transition": {"NONE", "INVALID_TO_VALID", "VALID_TO_INVALID"},
            "timestamp_meaning": {"DELAYED_SOURCE_WINDOW_END"} if "post_public" in view else {"DELAYED_SOURCE_WINDOW_END", "OTHER_EVENT_TIME"},
        }
        if layer in {"H", "X"} and pre and post:
            delayed_changed = _changed(view, "delayedPrice")
            latest_changed = _changed(view, "latestPrice")
            out["updated_stage"] = {"DELAYED_AND_LATEST"} if delayed_changed or latest_changed else {"NONE"}
            before_ok, after_ok = _first(pre.get("isPriceOk")), _first(post.get("isPriceOk"))
            if before_ok is False and after_ok is True: out["state_transition"] = {"INVALID_TO_VALID"}
            elif before_ok is True and after_ok is False: out["state_transition"] = {"VALID_TO_INVALID"}
            else: out["state_transition"] = {"NONE"}
        return out

    if implementation == "MENTO":
        out = {
            "input_acceptance": {"ACCEPTED"}, "return_source": {"REPORT_ACK"},
            "updated_stage": {"REPORTER_RECORD"}, "state_transition": {"VALID_REFRESH", "EXPIRED_TO_VALID"},
            "timestamp_meaning": {"REPORT_SUBMISSION_TIME"},
        }
        return out

    if implementation == "FELIX":
        failure = ret[1] if isinstance(ret, list) and len(ret) > 1 else None
        if failure is True:
            return {
                "input_acceptance": {"REJECTED"}, "return_source": {"RETAINED_CACHE"},
                "updated_stage": {"DISABLE_FLAG"}, "state_transition": {"ENABLED_TO_DISABLED"},
                "timestamp_meaning": NA.copy(),
            }
        out = {
            "input_acceptance": {"ACCEPTED", "NOT_EVALUATED"},
            "return_source": {"CURRENT_ORACLE", "RETAINED_CACHE"},
            "updated_stage": {"CACHE", "NONE"}, "state_transition": {"NONE"},
            "timestamp_meaning": NA.copy(),
        }
        sstores = view.get("non_abi_storage", {}).get("sstores", []) if isinstance(view.get("non_abi_storage"), dict) else []
        if layer == "X" and sstores:
            out.update(input_acceptance={"ACCEPTED"}, return_source={"CURRENT_ORACLE"}, updated_stage={"CACHE"})
        elif layer == "X" and "non_abi_storage" in view:
            out.update(input_acceptance={"NOT_EVALUATED"}, return_source={"RETAINED_CACHE"}, updated_stage={"NONE"})
        return out

    raise ValueError(f"unknown implementation: {implementation}")
