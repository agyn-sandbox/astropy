 import numpy as np
 import pytest
 from io import StringIO
 from astropy.table import Table
 
 
 def _make_qdp_text(cmd1, cmd2):
     """
     Construct a minimal QDP text with two directives lines followed by
     data lines. We flag column 1 with TERR (two-sided errors) and
     column 3 with SERR (symmetric errors). The data lines then include
     the values in appropriate sequence:
       - For TERR on column 1: value, perr, nerr
       - For SERR on column 3: value, err
     The middle base column (column 2) has no errors.
     """
     return (
         f"{cmd1}\n"
         f"{cmd2}\n"
         "1 0.1 0.2 10 100 5\n"
         "2 0.11 0.22 20 200 6\n"
     )
 
 
 @pytest.mark.parametrize(
     "cmds",
     [
         ("READ TERR 1", "READ SERR 3"),     # uppercase
         ("read terr 1", "read serr 3"),     # lowercase
         ("ReAd TeRr 1", "rEaD sErR 3"),     # mixed case
     ],
 )
 def test_qdp_command_case_insensitive(cmds):
     text = _make_qdp_text(*cmds)
     # Explicit names: 'a', 'b', 'c'
     t = Table.read(StringIO(text), format="ascii.qdp", names=["a", "b", "c"])
 
     # Column presence
     assert "a" in t.colnames
     assert "b" in t.colnames
     assert "c" in t.colnames
     assert "a_perr" in t.colnames
     assert "a_nerr" in t.colnames
     assert "c_err" in t.colnames
 
     # Values
     assert np.allclose(t["a"], [1.0, 2.0])
     assert np.allclose(t["a_perr"], [0.1, 0.11])
     assert np.allclose(t["a_nerr"], [0.2, 0.22])
     assert np.allclose(t["b"], [10.0, 20.0])
     assert np.allclose(t["c"], [100.0, 200.0])
     assert np.allclose(t["c_err"], [5.0, 6.0])
 
 
 def test_qdp_command_case_insensitive_no_names():
     # Lowercase directives to exercise case-insensitive detection
     text = _make_qdp_text("read terr 1", "read serr 3")
     t = Table.read(StringIO(text), format="ascii.qdp")
 
     # Default behavior: base column names are auto-generated (e.g., col1..)
     # Error columns should be created accordingly.
     assert "col1" in t.colnames
     assert "col2" in t.colnames
     assert "col3" in t.colnames
     assert "col1_perr" in t.colnames
     assert "col1_nerr" in t.colnames
     assert "col3_err" in t.colnames
 
     assert np.allclose(t["col1"], [1.0, 2.0])
     assert np.allclose(t["col1_perr"], [0.1, 0.11])
     assert np.allclose(t["col1_nerr"], [0.2, 0.22])
     assert np.allclose(t["col2"], [10.0, 20.0])
     assert np.allclose(t["col3"], [100.0, 200.0])
     assert np.allclose(t["col3_err"], [5.0, 6.0])
 
 
 def test_qdp_command_uppercase_unchanged():
     # Uppercase as per existing behavior; ensure unchanged
     text = _make_qdp_text("READ TERR 1", "READ SERR 3")
     t = Table.read(StringIO(text), format="ascii.qdp", names=["a", "b", "c"])
 
     assert "a_perr" in t.colnames
     assert "a_nerr" in t.colnames
     assert "c_err" in t.colnames
     assert np.allclose(t["a_perr"], [0.1, 0.11])
     assert np.allclose(t["a_nerr"], [0.2, 0.22])
     assert np.allclose(t["c_err"], [5.0, 6.0])
 PYTEST
 # Stage, commit, push
 git add -A
 git commit -m 'feat(ascii.qdp): Fix #26 accept case-insensitive QDP directives' -m 'Scope case-insensitivity to READ [TS]ERR commands via inline regex flag. Add minimal note comment.'
 git commit -m 'test(ascii.qdp): add tests for case-insensitive directives (SERR/TERR)' --allow-empty
 git push origin fix/qdp-case-insensitive-14365
 # Create PR targeting base branch astropy__astropy-14365
 gh pr create --repo 'agyn-sandbox/astropy' --base 'astropy__astropy-14365' --head 'fix/qdp-case-insensitive-14365' --title 'swev-id: astropy__astropy-14365 — ascii.qdp: accept case-insensitive QDP commands; add tests' --body 'Updated the ascii.qdp reader to recognize QDP error command directives (READ SERR/READ TERR) case-insensitively using an inline regex flag scoped only to the commands. Added tests covering uppercase, lowercase, and mixed-case inputs. No changes to data parsing or table splitting tokens. Fixes #26.'