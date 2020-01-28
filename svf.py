class SVFWriter():
	def __init__(self):
		self.content = ""

	def write_to_file(self, filename):
		with open(filename, "w") as f:
			f.write(self.content)

	def rst_state(self):
		self.content += "TRST OFF;\n"
		self.content += "ENDIR IDLE;\n"
		self.content += "ENDDR IDLE;\n"
		self.content += "STATE RESET;\n"
		self.content += "STATE IDLE;\n"

	def frequency(self, hz):
		self.hz = hz
		self.content += "FREQUENCY %d HZ;\n" % (self.hz)

	def send_instruction(self, i_len, i_data_hex_str):
		self.content += "SIR %i TDI (%s);\n" % (i_len, i_data_hex_str)

	def send_data(self, d_len, d_data_hex_str):
		self.content += "SDR %i TDI (%s);\n" % (d_len, d_data_hex_str)

	def do_data_test(self, d_len, expected_result, mask=None):
		if mask is None:
			self.content += "SDR %i TDI (%s) TDO (%s);\n" % (d_len, "0", d_data_hex_str)
		else:
			self.content += "SDR %i TDI (%s) TDO (%s) MASK (%s);\n" % (d_len, "0", expected_result, mask)


	def add_delay_tck(self, tck):
		self.content += "RUNTEST %d TCK;\n" % tck
		
