#functions to create and read hex data strings
#to be used with cvf files

class DataSerializer():
	def __init__(self):
		self.datalen = 0
		self.data = 0

		self.datablocks = []

	def add_data_block(self, block_len, block_data):
		self.datablocks.append((block_len, block_data))

		self.data += (block_data << self.datalen)
		self.datalen += block_len

	def get_len(self):
		return self.datalen

	def get_hex(self):
		return hex(self.data)

	def get_hex_str(self):
		back = str(hex(self.data))[2:]
		while len(back) * 4 < self.datalen:
			back = "0" + back
		return back

	def clear(self):
		self.datalen = 0
		self.data = 0

		self.datablocks = []


