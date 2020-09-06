import serial, re, os
import time
from collections import namedtuple

EXECUTION_TIMEOUT = 10
READ_TIMEOUT = 0.1
COMMAND_WAIT = 0.1
PORT = '/dev/ttyUSB0' if os.name == 'posix' else 'COM7'

class Debugger(object):

	def __init__(self, port=PORT, read_timeout=READ_TIMEOUT):
		try:
			self._serial_interface = serial.Serial(port, 9600, timeout=read_timeout, write_timeout=EXECUTION_TIMEOUT)
		except serial.SerialException:
			raise Exception("No board found. Please make sure it's connected and that you have permissions to read and write at '%s'"%port )
		self.memory = {}

	def __getattribute__(self, item):
		if item[:1] != '_' and callable(object.__getattribute__(self, item)):
			if not self.writtable:
				raise Exception("Serial port is blocked since the cpu is still executing instructions. Either wait for it to finish, or restart the board if it's on a loop")

		return super(Debugger, self).__getattribute__(item)

	@property
	def writtable(self):
		self._serial_interface.write(b' ')
		return self._read_batch() != ''

	def _read_batch(self):
		line = True
		batch = ""
		while line:
			line = self._serial_interface.readline()
			if line:
				batch += "%s"%line
		return batch

	def _write(self,msg):
		self._serial_interface.write(b'\r\n')
		time.sleep(COMMAND_WAIT)
		self._serial_interface.write(msg.encode())
		time.sleep(COMMAND_WAIT)


	def load(self, program):
		if program[:3] != 'S01':
			raise Exception('Invalid program binary')
		self._write('load\r\n')
		self._write(program)
		output = self._read_batch()
		if 'invalid' in output:
			raise Exception('Invalid program binary')

	def run(self, start=None):
		self._write('g %x\r\n'%start if start else 'g \r\n')
		raw = self._read_batch()
		serial_output = re.split(r"g .*\n",raw)
		if(len(serial_output)>1):
			serial_output = re.split(r"User Bkpt|Trap Instruction|User Program|.*Exception",serial_output[-1])[0]
		else:
			serial_output = ''
		try:
			return self._parse_registers(raw), serial_output
		except:
			return None, serial_output

	def read_memory(self, start, end=None):
		if end and start > end:
			start,end = end,start
		command =  ' md %x %x\r\n'%(start,end) if end else ' md %x\r\n'%start
		self._write(command)
		raw = self._read_batch()
		try: # parsing the command result
			results = [ obj.groupdict() for obj in re.compile(r"(?P<addr>[0-9A-F]{4})\s+(?P<vals>([0-9A-F]{2}(\s|-)+)*)").finditer(raw) if obj.groupdict()['vals']!='']
			addr = int(results[0]['addr'],16)
			for line in results:
				vals = re.split(r"\s*-\s*|\s+",line['vals'])
				for val in [v for v in vals if not '-' in v and v != '']:
					self.memory[addr] = int(val,16); addr += 1
		except:
			raise Exception("Wrong command response")

		return [self.memory[i] for i in range(start,end+1)] if end else self.memory[start]

	def fill_memory(self, start, end=None, value=0):
		if end and start > end:
			start,end = end,start
		command =  ' bf %x %x %x\r\n'%(start,end,value) if end else ' bf %x %x %x\r\n'%(start,start,value)
		self._write(command)
		raw = self._read_batch().lower()
		if 'data' in raw:
			raise Exception('Value out of range (max 1 byte size)')

	def get_registers(self):
		self._write('rd \r\n')
		raw = self._read_batch()
		return self._parse_registers(raw)

	def do_command(self, command):
		self._write('%s \r\n'%command)
		raw = self._read_batch()
		serial_output = re.split(r"%s .*\n"%command,raw)
		if(len(serial_output)>1):
			serial_output = re.split(r"User Bkpt|Trap Instruction|User Program|.*Exception",serial_output[-1])[0]
		else:
			serial_output = ''
		response = None
		try:
			response = self._parse_registers(raw)
		except Exception:
			pass
		return response, serial_output

	def _parse_registers(self, msg):
		try: # parsing the command result
			regs = next(re.compile(r"(?P<PP>[0-9A-F]{2})\s+(?P<PC>[0-9A-F]{4})\s+(?P<SP>[0-9A-F]{4})\s+(?P<X>[0-9A-F]{4})\s+(?P<Y>[0-9A-F]{4})\s+(?P<A>[0-9A-F]{2})\:(?P<B>[0-9A-F]{2})\s+(?P<CCR>(?P<S>\d)(?P<XI>\d)(?P<H>\d)(?P<I>\d)\s+(?P<N>\d)(?P<Z>\d)(?P<V>\d)(?P<C>\d))").finditer(msg)).groupdict()
			next_instruction = next(re.compile(r"xx\:(?P<address>[0-9A-F]{4})\s+(?P<assembled>[0-9A-F]+)\s+(?P<instruction>.*)").finditer(msg)).groupdict()
			for k,v in regs.items():
				if k == 'CCR':
					regs[k] = int(v.replace(' ',''),2)
				else:
					regs[k] = int(v,16)
			next_instruction = {
				'assembled':int(next_instruction['assembled'],16),
				'address':int(next_instruction['address'],16),
				'instruction':next_instruction['instruction'].strip()
			}
			Conditions = namedtuple('Conditions', 's x h i n z v c')
			Registers = namedtuple('Registers', 'pp pc sp x y a b ccr ccr_bits next')
			Next = namedtuple('Next', sorted(next_instruction))
			regs = Registers(
				pp=regs['PP'],
				pc=regs['PC'],
				sp=regs['SP'],
				x=regs['X'],
				y=regs['Y'],
				a=regs['A'],
				b=regs['B'],
				ccr=regs['CCR'],
				ccr_bits=Conditions(
					s=regs['S'],
					x=regs['XI'],
					h=regs['H'],
					i=regs['I'],
					n=regs['N'],
					z=regs['Z'],
					v=regs['V'],
					c=regs['C']),
				next=Next(**next_instruction)
			)
			return regs
		except:
			raise Exception("Wrong command response")

