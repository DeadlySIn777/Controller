"""Repeat exact independent actual COM check for the R19 native clone."""
from pathlib import Path
HERE=Path(__file__).resolve().parent
s=(HERE/'audit_ao1_native_com_reference_r2.py').read_text()
def change(a,b):
 global s
 assert a in s,a;s=s.replace(a,b)
change('reference-independent-r2','reference-independent-r4')
change('ao1-native-diagnostic-r1','ao1-native-diagnostic-r2')
change('5405473a4b6f55dda52f03f2328cfa282bc57784d18530d010bb135d2dcde15c','9c193d4e0e3b8d552a03eca2f91fcbcf6bc1a44c9b4a7bc4ee18b240292df18c')
change('eb9bbc9f6a29e8179704b425cb9826093be97e9af7cae23ecd1f536e8372e82d','fab7420ade17a7c742efbba1bc5acfd3b91e6607fc222fb7aec5ddd805aac1dd')
change('ao1-reference-coupled-r18.json','ao1-reference-coupled-r19.json')
change('dec4321581a1d9e3cdab41f556804e45469ff3a82850f772a5e22a98362e206f','203f9f36ec4979ba2715139a16058a38f40f4d9fdcb4ec9f95fad07c4c6526b7')
change('ao1-reference-coupled-r18-independent-mon-r4.json','ao1-reference-coupled-r19-independent-native-bound-r19.json')
change('e06e6692d3c03be118a741205fe691fe929ae91c5ee4c8e467fba48660d120f9','f664d851a31e2ce65a2f0bd979a8d851bd67c3efd3d20099c4cb3f210a7bb3bd')
change("'whole_board_no_loss_DRC_SI_analog_PDN_thermal_final_power':'OPEN'","'whole_board_no_loss_DRC_SI_analog_PDN_thermal_final_power':'OPEN','all85_original_native_2nm_contour_boundary_slivers_remain_explicitly_OPEN':True,'R19_native_repeat_no_reuse_of_old_transition_gap_credit':True")
q=HERE/'audit_ao1_native_com_reference_r4.py';assert not q.exists();q.write_text(s)
