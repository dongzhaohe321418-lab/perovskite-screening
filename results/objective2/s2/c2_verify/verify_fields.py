"""Field-by-field reading of 'scripts/49_s2_gates.py verify' (C2 operating decision D-C2-6; operator tool, private).

For every node gate file of a campaign (gates/*.json and the applied copies gates_applied/*.gate.json) the gate is
recomputed from the archive exactly as verify() does. The script prints, per gate, only whether decision, result
and inputs digest are equal. For a result that differs it prints the differing key paths. For a digest that
differs it prints the names of the opened files whose content hash differs. It never prints a value.

    cd <repo> && <python> <this file> --archive results/objective2/s2 --campaign c2
"""
import argparse, glob, importlib.util, json, os, sys


def load49(repo):
    sys.path.insert(0, os.path.join(repo, "scripts"))
    s = importlib.util.spec_from_file_location("g49", os.path.join(repo, "scripts", "49_s2_gates.py"))
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
    return m


def diff_paths(a, b, path=""):
    """Key paths where two JSON-like values differ (no values returned)."""
    if isinstance(a, dict) and isinstance(b, dict):
        out = []
        for k in sorted(set(a) | set(b)):
            if k not in a or k not in b:
                out.append(f"{path}/{k} (only one side)")
            else:
                out += diff_paths(a[k], b[k], f"{path}/{k}")
        return out
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            return [f"{path} (length {len(a)} vs {len(b)})"]
        return [p for i, (x, y) in enumerate(zip(a, b)) for p in diff_paths(x, y, f"{path}[{i}]")]
    return [] if json.dumps(a, sort_keys=True, default=str) == json.dumps(b, sort_keys=True, default=str) else [path or "/"]


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--archive", required=True); ap.add_argument("--campaign", required=True)
    a = ap.parse_args()
    g = load49(os.getcwd())
    layout = g.dep("c46").Layout(kind="archive", root=a.archive)
    cdir = layout.campaign_dir(a.campaign)
    st_path = os.path.join(cdir, "state_end.json")
    state = json.load(open(st_path)) if os.path.exists(st_path) else {}
    files = sorted(glob.glob(os.path.join(cdir, "gates", "*.json"))) + \
        sorted(glob.glob(os.path.join(cdir, "gates_applied", "*.gate.json")))
    for fn in files:
        node = json.load(open(fn))
        again = g.evaluate_gate(node["gate"], layout, a.campaign, node.get("state_in", state), attempt=node.get("attempt", 1),
                                inputs=node.get("inputs_in"), c1=node.get("c1_in"))
        rel = os.path.relpath(fn, cdir)
        dec = "equal" if not diff_paths(node.get("decision"), again.get("decision")) else "DIFFER"
        rp = diff_paths(node.get("result"), again.get("result"))
        dg = "equal" if node.get("inputs_digest") == again.get("inputs_digest") else "DIFFER"
        print(f"{rel}: gate {node['gate']} attempt {node.get('attempt', 1)}: decision {dec}; result "
              f"{'equal' if not rp else 'DIFFER at ' + ', '.join(rp[:12]) + (' ...' if len(rp) > 12 else '')}; digest {dg}")
        if dg == "DIFFER":
            na = {(o["label"], o["file"], o["mode"]): o["sha256"] for o in node.get("opened", [])}
            nb = {(o["label"], o["file"], o["mode"]): o["sha256"] for o in again.get("opened", [])}
            changed = sorted(f"{k[1]} ({k[2]})" for k in set(na) & set(nb) if na[k] != nb[k])
            only = sorted(f"{k[1]} ({k[2]}; {'node' if k in na else 'archive'} only)" for k in set(na) ^ set(nb))
            print(f"    opened files with another content hash: {changed or 'none'}; opened on one side only: {only or 'none'}")


if __name__ == "__main__":
    main()
