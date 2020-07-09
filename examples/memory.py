from dbug12 import Debugger
import tempfile, os, subprocess

asm = '''
	org $2000
	db $AA
	org $2010
	db $01,$02,$03
'''

# assemble the src code
# (optionally you can compile externally and 
# feed the .s19 content to the load method)
try:
	asm_file = open('tmp.asm','w')
	asm_file.write(asm)
	asm_file.close()
	try: 
		subprocess.check_call(['as12', 'tmp.asm', '-otmp.s19'])
	except:
		raise Exception('as12 command not found')	
	compiled = open('tmp.s19','r').read()
except Exception as e:
	raise Exception("Compilation error: %s"%e)
finally:
	for f in ['tmp.s19','tmp.asm']:
		if os.path.exists(f): os.remove(f)

debugger = Debugger()		# make sure there's a board connected (use 'port' optional argument if you're using a custom serial port )
debugger.load(compiled)		# upload the compiled code to the board
print('$2000:%X'%debugger.read_memory(0x2000))			# read the content of 0x2000
print('$2010:%s'%debugger.read_memory(0x2010,0x2012))	# read the array of 3 bytes starting at 0x2010