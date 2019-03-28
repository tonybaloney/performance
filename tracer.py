import sys
import dis
import time
import collections
from runpy import run_path
from opcode import opname

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

_entry = None
_exit = None
_lastop = None
_records = collections.defaultdict(list)


def t(frame, event, args):
   global _entry, _exit, _lastop, _records
   _entry = time.process_time_ns()
   frame.f_trace_opcodes = True

   if _lastop:
      _records[opname[_lastop]].append(_entry - _exit)
   _lastop = False
   if event == 'opcode':
      co = frame.f_code
      linestarts = dict(dis.findlinestarts(co))
      operations = dis._get_instructions_bytes(co.co_code, co.co_varnames, co.co_names,
                                               co.co_consts, co.co_cellvars + co.co_freevars, linestarts)
      for op in operations:
         if op.offset == frame.f_lasti:
            _lastop = op.opcode
   _exit = time.process_time_ns()

   return t

# Enable the tracer, run the file and show the results..
sys.settrace(t)

run_path(sys.argv[1])

sys.settrace(None)

# delete call method and function, they aren't relevant for performance because it includes the execution time
# of the child frame

if 'CALL_FUNCTION' in _records:
   del _records['CALL_FUNCTION']
if 'CALL_METHOD' in _records:
   del _records['CALL_METHOD']

df = pd.DataFrame([[opcode, entry] for opcode, entries in _records.items() for entry in entries], columns=['opcode', 'timens'])

sns.boxplot(y="opcode", x="timens", data=df, whis="range", palette="vlag", orient="h")

plt.show()