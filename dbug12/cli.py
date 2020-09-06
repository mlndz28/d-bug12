#!/usr/bin/env python

from dbug12 import Debugger
import argparse, sys, os, serial.tools.miniterm

def main():
	commands = {
		'load':{
			'description':'Load a compiled program into memory',
			'args':[
				{'name':'file', 'meta':'<file>','type':argparse.FileType('r'),'description':'Assembled file to be loaded in memory','nargs':1}
			]},
		'run': {
			'description':'Start execution from a specific point of memory',
			'args':[
				{'name':'addr', 'meta':'<address>','description':'Execution start address (hexadecimal). Default value: registers.pc','nargs':'?'}
			]},
		'next-instruction': {
			'description':'Run a single instruction (from current PC)',
			},
		'get-memory': {
			'description':'Display a section of memory',
			'args':[
				{'name':'start', 'meta':'<start>','description':'Address (in hexadecimal representation) at which to start the read','nargs':1},
				{'name':'end', 'meta':'<end>','description':'Address (in hexadecimal representation) at which to end the read. Optional parameter, leaving this empty will return only one byte from memory','nargs':'?'}
			]},
		'erase-memory': {
			'description':'Erase a section of memory',
			'args':[
				{'name':'start', 'meta':'<start>','description':'Address (in hexadecimal representation) at which to start erasing values','nargs':1},
				{'name':'end', 'meta':'<end>','description':'Address (in hexadecimal representation) at which to end erasing values. Optional parameter, leaving this empty will erase only one byte from memory','nargs':'?'},
				{'name':'--value', 'meta':None,'description':'Value written in all specified address. Default: 00','nargs':None,'default':'00'}
			]},
		'get-registers': {
			'description':'Display CPU registers',
			},
		'monitor': {
			'description':'Spawns a terminal that directly communicates with the board',
			}
	}

	port = '/dev/ttyUSB0' if os.name == 'posix' else 'COM7'
	
	parent = argparse.ArgumentParser(description='CLI for D-Bug12 compatible boards',add_help=False)
	parent.add_argument('-p','--port', help='serial communication port accessed by the board. Default: "%s"'%port,default=port)
	parser = argparse.ArgumentParser(parents=[parent])
	subparsers = parser.add_subparsers(dest='command',metavar='<command>', help='%s <command> -h will show further usage and arguments, if any. Available commands are:\n'%os.path.basename(sys.argv[0]))
	for k in commands:
		commands[k]['parser'] = subparsers.add_parser(k, description=commands[k]['description'],parents=[parent],help=commands[k]['description'])
		if 'args' in commands[k]:
			for a in commands[k]['args']:
				commands[k]['parser'].add_argument(a['name'], metavar=a['meta'], type=a.get('type'), help=a['description'], nargs=a['nargs'], default=a.get('default'))

	if(len(sys.argv)==1): 
		sys.stdout.write(parser.format_help())
		sys.stdout.flush()
		exit() 
	
	args = parser.parse_args()
	sys.argv.remove(args.command)
	subargs = commands[args.command]['parser'].parse_args()

	
	if args.command == 'get-registers':
		print_regs(Debugger(args.port).get_registers())
		
	elif args.command == 'load':
		Debugger(args.port).load(subargs.file[0].read())
	
	elif args.command == 'run':
		deb = Debugger(args.port)
		if subargs.addr:
			start = int(subargs.addr,16)
		else:
			start = deb.get_registers().pc
		print('Executing at 0x%x'%start)
		regs,serial_output = deb.run(start)
		if serial_output: 
			print("Output:\n\n%s"%serial_output)
		if regs:
			print("Execution stopped")
			print_regs(regs)

	elif args.command == 'next-instruction':
		deb = Debugger(args.port)
		regs,_ = deb.do_command('t')
		if regs:
			print("Execution stopped")
			print_regs(regs)

	elif args.command == 'monitor':
		print('\n\tEnter HELP for a command summary\n')
		sys.argv[1:] = ['--eol','cr']
		serial.tools.miniterm.main(default_port=port)
	
	elif args.command == 'get-memory':
		if subargs.end:
			mem = Debugger(args.port).read_memory(int(subargs.start[0],16),int(subargs.end,16))
		else:
			mem = [Debugger(port).read_memory(int(subargs.start[0],16))]
		for i in range(len(mem)):
			print("\t0x%04X:\t0x%02X"%(int(subargs.start[0],16)+i,mem[i]))
	
	elif args.command == 'erase-memory':
		Debugger(port).fill_memory(int(subargs.start[0],16),end=int(subargs.end,16) if subargs.end else None,value=int(args.value,16))
	

def print_regs(regs):
	print('')
	for name, value in regs._asdict().items():
		if(name=='ccr_bits'):
			print("\t\t"+repr(value).replace('Conditions(','').replace(')','').upper())
		elif(name=='next'):
			print("\n\tNext instruction: @0x%04X | %s (0x%X)\n"%(value.address,value.instruction,value.assembled))
		elif(['a','b','ccr','pp'].count(name)):
			print("\t%s:\t0x%02X"%(name.upper(),value))
		else:
			print("\t%s:\t0x%04X"%(name.upper(),value))

if __name__ == '__main__':
	main()
