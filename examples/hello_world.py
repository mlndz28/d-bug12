from dbug12 import Debugger
import tempfile, os, subprocess

asm = '''
	org $1FF0
	fcc "Hello World!"
	dc.b $00
	org $2000
	ldd #$1FF0
	ldx #$0
	jsr [#$EE88,X]
	swi
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
reg, output = debugger.run(0x2000)		# run starting from $2000
print(output)