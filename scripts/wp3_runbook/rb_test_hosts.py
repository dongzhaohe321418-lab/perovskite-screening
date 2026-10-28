# RUNBOOK step 3c: the --test-hosts list of the m 1e command (m30 m32 + every item-1' host with at least one
# converged output with a force block). Reads only convergence status, no value (item 7: not analysed before step 6).
#   python rb_test_hosts.py [<dft root>]       (default results/objective2/dopant_shell)
import glob, importlib.util, os, sys
s = importlib.util.spec_from_file_location("a32", "scripts/32_dft_validation_analysis.py")
a32 = importlib.util.module_from_spec(s); s.loader.exec_module(a32)
root = sys.argv[1] if len(sys.argv) > 1 else "results/objective2/dopant_shell"
ok = set()
for f in glob.glob(os.path.join(root, "wp3", "test_extra", "raw", "*.out.gz")):
    q = a32.parse_qe(f)
    if q is not None and q["converged"] and q["forces"] is not None:
        ok.add(os.path.basename(f).split("_")[0])
print(" ".join(["m30", "m32"] + [h for h in ("m04", "m10", "m14", "m18", "m27") if h in ok]))
