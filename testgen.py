from jtaghex import DataSerializer
import bsdl
import svf

class BsdlSemantics:
    def map_string(self, ast):
        parser = bsdl.bsdlParser()
        ast = parser.parse(''.join(ast), "port_map")
        return ast

    def grouped_port_identification(self, ast):
        parser = bsdl.bsdlParser()
        ast = parser.parse(''.join(ast), "group_table")
        return ast

class TestGenerator:

	def __init__(self, bsdlfile, pins):
		parser = bsdl.bsdlParser()
		self.bsd_data = parser.parse(open(bsdlfile).read(), "bsdl_description", semantics=BsdlSemantics(), parseinfo=False)
		self.dr_scan_len = int(self.bsd_data["boundary_scan_register_description"]["fixed_boundary_stmts"]["boundary_length"])
		self.ir_scan_len = int(self.bsd_data["instruction_register_description"]["instruction_length"])

		led_a_pin = "IO64"
		led_b_pin = "IO48"
		pos_out_led_green = self.get_pin_pos(led_a_pin, "OUTPUT3")
		pos_out_led_yellow = self.get_pin_pos(led_b_pin, "OUTPUT3")

		self.fill_instructions()
		print(self.instructions)

		self.testpins = pins

		self.sample = DataSerializer()
		self.sample.add_data_block(self.ir_scan_len, self.instructions["SAMPLE"])
		self.sample.add_data_block(self.ir_scan_len, self.instructions["SAMPLE"])

		self.extest = DataSerializer()
		self.extest.add_data_block(self.ir_scan_len, self.instructions["EXTEST"])
		self.extest.add_data_block(self.ir_scan_len, self.instructions["EXTEST"])

		self.testdata = DataSerializer()

		self.result_mask = DataSerializer()

		self.expected_result = DataSerializer()

		self.testcon = DataSerializer()
		self.testcon.add_data_block(self.ir_scan_len, self.instructions["SAMPLE"])
		self.testcon.add_data_block(self.ir_scan_len, self.instructions["EXTEST"])

		self.led_green_on = DataSerializer()
		self.led_green_on.add_data_block(self.dr_scan_len, 0)
		self.led_green_on.add_data_block(self.dr_scan_len, 1 << pos_out_led_green)

	def simple_bridge_test(self):
		self.testdata.clear()
		#second device will measure -> no data
		self.testdata.add_data_block(self.dr_scan_len, 0)
		#first device sets outputs
		self.testdata.add_data_block(self.dr_scan_len, 1 << self.get_pin_pos("IO56", "OUTPUT3"))

		self.result_mask.clear()
		self.result_mask.add_data_block(self.dr_scan_len, 1 << self.get_pin_pos("IO49", "INPUT") | 1 << self.get_pin_pos("IO50", "INPUT"))
		self.result_mask.add_data_block(self.dr_scan_len, 0)

		self.expected_result.clear()
		self.expected_result.add_data_block(self.dr_scan_len, 1 << self.get_pin_pos("IO49", "INPUT"))
		self.expected_result.add_data_block(self.dr_scan_len, 0)

		svf_writer = svf.SVFWriter()
		svf_writer.rst_state()
		svf_writer.frequency(10000000)
		#set test data
		svf_writer.send_instruction(self.sample.get_len(), self.sample.get_hex_str())
		svf_writer.send_data(self.testdata.get_len(), self.testdata.get_hex_str())
		svf_writer.send_instruction(self.testcon.get_len(), self.testcon.get_hex_str())
		svf_writer.do_data_test(self.expected_result.get_len(), self.expected_result.get_hex_str(), self.result_mask.get_hex_str())

		#if we get here the test did not fail
		svf_writer.send_data(self.led_green_on.get_len(), self.led_green_on.get_hex_str())
		svf_writer.send_instruction(self.extest.get_len(), self.extest.get_hex_str())

		svf_writer.write_to_file("simple_bridge_test.svf")

	def pull_up_test_all(self):
		svf_writer = svf.SVFWriter()
		svf_writer.rst_state()
		svf_writer.frequency(10000000)

		self.testdata.clear()
		self.result_mask.clear()
		self.expected_result.clear()

		#no weird gates -> so no fancy testing required -> all in parallel possible
		#pull up test checks if a high is recieved while all data is zero
		self.testdata.add_data_block(self.dr_scan_len, 0)
		self.testdata.add_data_block(self.dr_scan_len, 0)
		#expecting all zero answer
		self.expected_result.add_data_block(self.dr_scan_len, 0)
		self.expected_result.add_data_block(self.dr_scan_len, 0)

		#mask all input cells of recieving chip
		mask = 0
		for i in range(len(self.testpins)):
			mask = mask | (1 << self.get_pin_pos(self.testpins[i], "INPUT"))

		self.result_mask.add_data_block(self.dr_scan_len, mask)
		self.result_mask.add_data_block(self.dr_scan_len, 0)

		#write test sequence
		svf_writer.send_instruction(self.sample.get_len(), self.sample.get_hex_str())
		svf_writer.send_data(self.testdata.get_len(), self.testdata.get_hex_str())
		svf_writer.send_instruction(self.testcon.get_len(), self.testcon.get_hex_str())
		svf_writer.do_data_test(self.expected_result.get_len(), self.expected_result.get_hex_str(), self.result_mask.get_hex_str())

		#if we get here the test did not fail
		svf_writer.send_data(self.led_green_on.get_len(), self.led_green_on.get_hex_str())
		svf_writer.send_instruction(self.extest.get_len(), self.extest.get_hex_str())
		svf_writer.write_to_file("pull_up_test_all.svf")

	def pull_down_test_all(self):
		svf_writer = svf.SVFWriter()
		svf_writer.rst_state()
		svf_writer.frequency(10000000)

		self.testdata.clear()
		self.result_mask.clear()
		self.expected_result.clear()


		#mask all input cells of recieving chip
		mask = 0
		result = 0
		testpattern = 0
		for i in range(len(self.testpins)):
			mask = mask | (1 << self.get_pin_pos(self.testpins[i], "INPUT"))
			result = result | (1 << self.get_pin_pos(self.testpins[i], "INPUT"))
			testpattern = testpattern | (1 << self.get_pin_pos(self.testpins[i], "OUTPUT3"))

		#no weird gates -> so no fancy testing required -> all in parallel possible
		#pull up test checks if a high is recieved while all data is zero
		self.testdata.add_data_block(self.dr_scan_len, 0)
		#first chips pulls pins high
		self.testdata.add_data_block(self.dr_scan_len, testpattern)

		#expecting all zero answer
		self.expected_result.add_data_block(self.dr_scan_len, result)
		self.expected_result.add_data_block(self.dr_scan_len, 0)

		self.result_mask.add_data_block(self.dr_scan_len, mask)
		self.result_mask.add_data_block(self.dr_scan_len, 0)

		#write test sequence
		svf_writer.send_instruction(self.sample.get_len(), self.sample.get_hex_str())
		svf_writer.send_data(self.testdata.get_len(), self.testdata.get_hex_str())
		svf_writer.send_instruction(self.testcon.get_len(), self.testcon.get_hex_str())
		svf_writer.do_data_test(self.expected_result.get_len(), self.expected_result.get_hex_str(), self.result_mask.get_hex_str())

		#if we get here the test did not fail
		svf_writer.send_data(self.led_green_on.get_len(), self.led_green_on.get_hex_str())
		svf_writer.send_instruction(self.extest.get_len(), self.extest.get_hex_str())
		svf_writer.write_to_file("pull_down_test_all.svf")

	def short_test_all(self):
		svf_writer = svf.SVFWriter()
		svf_writer.rst_state()
		svf_writer.frequency(10000000)

		#mask all input cells of recieving chip
		for i in range(len(self.testpins)):
			print(self.testpins[i], self.testpins[len(self.testpins)-i-1])
			self.testdata.clear()
			self.result_mask.clear()
			self.expected_result.clear()

			mask = 0
			result = 0
			testpattern = 0

			#test if highs are found at neighboring pins
			if i == 0:
				mask = mask | (1 << self.get_pin_pos(self.testpins[len(self.testpins)-1], "INPUT")) | (1 << self.get_pin_pos(self.testpins[len(self.testpins)-2], "INPUT"))
			elif i == len(self.testpins)-1:
				mask = mask | (1 << self.get_pin_pos(self.testpins[0], "INPUT")) | (1 << self.get_pin_pos(self.testpins[1], "INPUT"))
			else:
				for j in [-1, 0, 1]:
					mask = mask | (1 << self.get_pin_pos(self.testpins[len(self.testpins)-(i+j)-1], "INPUT"))

			#expecting high at only the expected recieving pin
			result = result | (1 << self.get_pin_pos(self.testpins[len(self.testpins)-i-1], "INPUT"))

			#test for shorts one pin at a time
			testpattern = testpattern | (1 << self.get_pin_pos(self.testpins[i], "OUTPUT3"))

			self.expected_result.add_data_block(self.dr_scan_len, result)
			self.expected_result.add_data_block(self.dr_scan_len, 0)

			self.testdata.add_data_block(self.dr_scan_len, 0)
			#first chips pulls one pin high
			self.testdata.add_data_block(self.dr_scan_len, testpattern)

			self.result_mask.add_data_block(self.dr_scan_len, mask)
			self.result_mask.add_data_block(self.dr_scan_len, 0)

			#write test sequence
			svf_writer.send_instruction(self.sample.get_len(), self.sample.get_hex_str())
			svf_writer.send_data(self.testdata.get_len(), self.testdata.get_hex_str())
			svf_writer.send_instruction(self.testcon.get_len(), self.testcon.get_hex_str())
			svf_writer.do_data_test(self.expected_result.get_len(), self.expected_result.get_hex_str(), self.result_mask.get_hex_str())

		#if we get here the test did not fail
		svf_writer.send_data(self.led_green_on.get_len(), self.led_green_on.get_hex_str())
		svf_writer.send_instruction(self.extest.get_len(), self.extest.get_hex_str())
		svf_writer.write_to_file("short_test_all.svf")


	def get_pin_pos(self, pin_name, cell_function):
		for cell in self.bsd_data["boundary_scan_register_description"]["fixed_boundary_stmts"]["boundary_register"]:
			if cell["cell_info"]["cell_spec"]["port_id"] == pin_name and cell["cell_info"]["cell_spec"]["function"] == cell_function:
				return int(cell["cell_number"])

	def fill_instructions(self):
		self.instructions = {}

		for i in self.bsd_data["instruction_register_description"]["instruction_opcodes"]:
			self.instructions[i["instruction_name"]] = int(i["opcode_list"][0],2)





if __name__ == "__main__":
	testpins = ["IO49", "IO50", "IO51", "IO52", "IO53", "IO54", "IO55", "IO56" ]
	gen = TestGenerator("bsdlfiles/5M160ZE64.bsd", testpins)

	gen.simple_bridge_test()
	gen.pull_up_test_all()
	gen.pull_down_test_all()
	gen.short_test_all()


