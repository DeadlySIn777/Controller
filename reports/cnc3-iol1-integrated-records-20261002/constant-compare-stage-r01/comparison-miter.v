module comparison_miter(input[1407:0]frame,input cs_fb,input[8:0]frame_bytes,input crc_good,embedded_crc_good,output mismatch,output[7:0]reference_result,logic_result);
cnc3_command_validate_reference old(frame,cs_fb,frame_bytes,crc_good,embedded_crc_good,reference_result);
cnc3_command_validate_logic new_impl(frame,cs_fb,frame_bytes,crc_good,embedded_crc_good,logic_result);
assign mismatch=reference_result!=logic_result;
endmodule
