from dbug12 import Debugger
import time

formatStr="%8s %8s %8s %8s %8s %12s %8s %s"

def printRegs(r):
  print(formatStr % (hex(r.pp), hex(r.pc), hex(r.sp), hex(r.x), hex(r.y), bin(r.ccr), hex(r.next.address), r.next.instruction))

compiled=open("archivo.s19", "r").read()
debugger = Debugger(port='COM3')
debugger.load(compiled)
debugger.do_command('pc 2000')

print(formatStr % ('pp', 'pc', 'sp', 'x', 'y', 'SXHINZVC', 'next', 'instruction'))
while True:
	try:
		regs = debugger.get_registers()
		printRegs(regs)
		time.sleep(1)
		debugger.do_command('t')
	except Exception:
		continue
