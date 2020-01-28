#!/bin/python

import json
import cvf
from jtaghex import DataSerializer

def get_pin_pos(bsd_data, pin_name, cell_function):
	for cell in bsd_data["boundary_scan_register_description"]["fixed_boundary_stmts"]["boundary_register"]:
		if cell["cell_info"]["cell_spec"]["port_id"] == pin_name and cell["cell_info"]["cell_spec"]["function"] == cell_function:
			return int(cell["cell_number"])

def fill_instructions(bsd_data):
	instructions = {}

	for i in bsd_data["instruction_register_description"]["instruction_opcodes"]:
		instructions[i["instruction_name"]] = int(i["opcode_list"][0],2)

	return instructions

def main():
	bsdlfile = "5M160ZE64.json"
	bsd_data = json.loads(open(bsdlfile, "r").read())

	dr_scan_len = int(bsd_data["boundary_scan_register_description"]["fixed_boundary_stmts"]["boundary_length"])
	ir_scan_len = int(bsd_data["instruction_register_description"]["instruction_length"])

	instructions = fill_instructions(bsd_data)

	print("DR_LEN",dr_scan_len)
	print("IR_LEN",ir_scan_len)
	print(instructions)

	led_a_pin = "IO64"
	led_b_pin = "IO48"
	pos_out_led_green = get_pin_pos(bsd_data, led_a_pin, "OUTPUT3")
	pos_out_led_yellow = get_pin_pos(bsd_data, led_b_pin, "OUTPUT3")

	sample = DataSerializer()
	sample.add_data_block(ir_scan_len, instructions["SAMPLE"])
	sample.add_data_block(ir_scan_len, instructions["SAMPLE"])

	extest = DataSerializer()
	extest.add_data_block(ir_scan_len, instructions["EXTEST"])
	extest.add_data_block(ir_scan_len, instructions["EXTEST"])

	led_on = DataSerializer()
	led_on.add_data_block(dr_scan_len, 1 << pos_out_led_yellow)
	led_on.add_data_block(dr_scan_len, 1 << pos_out_led_green)

	led_off = DataSerializer()
	led_off.add_data_block(dr_scan_len, 0)
	led_off.add_data_block(dr_scan_len, 0)

	cvf_writer = cvf.CVFWriter()
	cvf_writer.rst_state()
	cvf_writer.frequency("change_me_later")
	cvf_writer.send_instruction(extest.get_len(), extest.get_hex_str())
	cvf_writer.send_data(led_on.get_len(), led_on.get_hex_str())
	cvf_writer.add_delay(1000)
	cvf_writer.send_data(led_off.get_len(), led_off.get_hex_str())
	cvf_writer.add_delay(1000)
	cvf_writer.send_data(led_on.get_len(), led_on.get_hex_str())
	cvf_writer.add_delay(1000)
	cvf_writer.send_data(led_off.get_len(), led_off.get_hex_str())
	cvf_writer.add_delay(1000)
	cvf_writer.send_instruction(sample.get_len(), sample.get_hex_str())

	cvf_writer.write_to_file("test.cvf")


if __name__ == "__main__":
	main()
