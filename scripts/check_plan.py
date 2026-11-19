#!/usr/bin/env python3
"""Check a cinematic shot plan and optionally export its edit timelines."""

import argparse
import csv
import json
import re
import sys
from pathlib import Path


ID_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")
METHODS = ("live", "ai", "composite")


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def records(items, location, issues):
    if not isinstance(items, list):
        issues.append(f"{location}: expected an array")
        return {}
    result = {}
    for position, item in enumerate(items):
        entry = f"{location}[{position}]"
        identifier = item.get("id") if isinstance(item, dict) else None
        if not isinstance(identifier, str) or ID_PATTERN.fullmatch(identifier) is None:
            issues.append(f"{entry}: expected an object with a valid id")
        elif identifier in result:
            issues.append(f"{entry}: duplicate id {identifier}")
        else:
            result[identifier] = item
    return result


def check_source(source, location, edit_duration, issues):
    if not isinstance(source, dict):
        issues.append(f"{location}: expected an object")
        return "", "", ""
    take = source.get("take")
    if not isinstance(take, str) or ID_PATTERN.fullmatch(take) is None:
        issues.append(f"{location}.take: expected a valid take id")
    start, end = source.get("in_ms"), source.get("out_ms")
    if type(start) is not int or type(end) is not int or not 0 <= start < end:
        issues.append(f"{location}: expected integer time with 0 <= in_ms < out_ms")
        return "", "", ""

    if "available_ms" in source:
        available = source["available_ms"]
        if type(available) is not int or available < end:
            issues.append(f"{location}.available_ms: expected an integer at least as large as out_ms ({end})")
    retimed = source.get("retimed", False)
    if type(retimed) is not bool:
        issues.append(f"{location}.retimed: expected true or false")
    elif not retimed and end - start != edit_duration:
        issues.append(f"{location}: source length differs from edit length for a real-time cut")
    return take, start, end


def check_cut_sequence(sequence, name, shot_index, beat_index, required, issues):
    if not isinstance(sequence, dict):
        issues.append(f"{name}: expected an object")
        return []
    target = sequence.get("target_ms")
    if type(target) is not int or target <= 0:
        issues.append(f"{name}.target_ms: expected a positive integer")
    allowed_methods = sequence.get("allowed_methods", list(METHODS))
    if not isinstance(allowed_methods, list) or not allowed_methods or any(method not in METHODS for method in allowed_methods):
        issues.append(f"{name}.allowed_methods: expected a non-empty array of live, ai, or composite")
        allowed_methods = METHODS
    cuts = records(sequence.get("cuts"), f"{name}.cuts", issues)
    if not cuts:
        issues.append(f"{name}.cuts: expected at least one cut")

    expected_start = 0
    covered = set()
    exported = []
    for cut_id, cut in cuts.items():
        location = f"{name}.cuts.{cut_id}"
        shot_id = cut.get("shot")
        shot = shot_index.get(shot_id) if isinstance(shot_id, str) else None
        if shot is None:
            issues.append(f"{location}.shot: unknown shot {shot_id!r}")
        elif shot.get("method") not in allowed_methods:
            issues.append(f"{location}.shot: method {shot.get('method')!r} is not allowed in {name}")
        beat_ids = cut.get("covers")
        if not isinstance(beat_ids, list):
            issues.append(f"{location}.covers: expected an array of beat ids")
        else:
            for beat_id in beat_ids:
                if not isinstance(beat_id, str) or beat_id not in beat_index:
                    issues.append(f"{location}.covers: unknown beat {beat_id!r}")
                elif shot is not None:
                    covered.add(beat_id)

        start, end = cut.get("in_ms"), cut.get("out_ms")
        if type(start) is not int or type(end) is not int or not 0 <= start < end:
            issues.append(f"{location}: expected integer time with 0 <= in_ms < out_ms")
            continue
        if start != expected_start:
            fault = "gap" if start > expected_start else "overlap or out of order"
            issues.append(f"{location}: {fault}, starts at {start} ms, expected {expected_start} ms")
        expected_start = end
        source_fields = "", "", ""
        if "source" in cut:
            source_fields = check_source(cut["source"], f"{location}.source", end - start, issues)
        if shot is not None:
            exported.append((name, cut_id, shot_id, start, end, end - start,
                             shot.get("method"), shot.get("setup", ""), *source_fields))

    if type(target) is int and expected_start != target:
        issues.append(f"{name}: ends at {expected_start} ms, targets {target} ms")
    missing = sorted(required - covered)
    if missing:
        issues.append(f"{name}: missing required beats {', '.join(missing)}")
    return exported


def check_plan(plan):
    if not isinstance(plan, dict):
        return ["plan: expected a JSON object"], []
    issues = []
    version = plan.get("schema_version")
    if type(version) is not int or version != 1:
        issues.append("schema_version: expected 1")

    setups = records(plan.get("setups", []), "setups", issues)
    shots = records(plan.get("shots"), "shots", issues)
    beats = records(plan.get("beats"), "beats", issues)
    required_beats = set()
    for beat_id, beat in beats.items():
        required = beat.get("required", True)
        if type(required) is not bool:
            issues.append(f"beats.{beat_id}.required: expected true or false")
        elif required:
            required_beats.add(beat_id)

    for shot_id, shot in shots.items():
        method = shot.get("method")
        setup = shot.get("setup")
        if method not in METHODS:
            issues.append(f"shots.{shot_id}.method: expected live, ai, or composite")
        elif method in ("live", "composite"):
            if not isinstance(setup, str) or setup not in setups:
                issues.append(f"shots.{shot_id}.setup: unknown or missing live setup {setup!r}")
        elif setup is not None:
            issues.append(f"shots.{shot_id}.setup: AI-only shots have no live setup")

    rows = check_cut_sequence(plan.get("main"), "main", shots, beats, required_beats, issues)
    if "fallback" in plan:
        rows.extend(check_cut_sequence(plan["fallback"], "fallback", shots, beats, required_beats, issues))
    return issues, rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", type=Path, help="UTF-8 JSON shot plan")
    parser.add_argument("--csv", type=Path, help="export validated timelines to a new CSV file")
    args = parser.parse_args()

    try:
        with args.plan.open(encoding="utf-8-sig") as source:
            plan = json.load(source, object_pairs_hook=unique_object)
        issues, rows = check_plan(plan)
        if issues:
            for issue in issues:
                print(f"ERROR {issue}", file=sys.stderr)
            return 1
        if args.csv is not None:
            with args.csv.open("x", encoding="utf-8-sig", newline="") as output:
                writer = csv.writer(output)
                writer.writerow(("sequence", "cut", "shot", "in_ms", "out_ms", "duration_ms", "method", "setup",
                                 "take", "source_in_ms", "source_out_ms"))
                writer.writerows(rows)
    except (OSError, ValueError) as error:
        print(f"ERROR {error}", file=sys.stderr)
        return 1

    print(f"OK: {len(rows)} cuts checked across {1 + ('fallback' in plan)} sequence(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
