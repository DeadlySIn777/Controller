`timescale 1ns/1ps
module vendor_lut_probe_tb;
reg [3:0] a=0; reg[2:0] three=0;reg[1:0] two=0;
wire [174:0] y;
EFX_LUT4 l0(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[0])); defparam l0.LUTMASK=16'h0001;
EFX_LUT4 l1(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[1])); defparam l1.LUTMASK=16'h0007;
EFX_LUT4 l2(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[2])); defparam l2.LUTMASK=16'h000b;
EFX_LUT4 l3(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[3])); defparam l3.LUTMASK=16'h000d;
EFX_LUT4 l4(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[4])); defparam l4.LUTMASK=16'h000e;
EFX_LUT4 l5(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[5])); defparam l5.LUTMASK=16'h004f;
EFX_LUT4 l6(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[6])); defparam l6.LUTMASK=16'h0071;
EFX_LUT4 l7(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[7])); defparam l7.LUTMASK=16'h007f;
EFX_LUT4 l8(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[8])); defparam l8.LUTMASK=16'h008f;
EFX_LUT4 l9(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[9])); defparam l9.LUTMASK=16'h00b2;
EFX_LUT4 l10(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[10])); defparam l10.LUTMASK=16'h00bf;
EFX_LUT4 l11(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[11])); defparam l11.LUTMASK=16'h00ef;
EFX_LUT4 l12(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[12])); defparam l12.LUTMASK=16'h00f1;
EFX_LUT4 l13(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[13])); defparam l13.LUTMASK=16'h00f4;
EFX_LUT4 l14(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[14])); defparam l14.LUTMASK=16'h00f8;
EFX_LUT4 l15(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[15])); defparam l15.LUTMASK=16'h0100;
EFX_LUT4 l16(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[16])); defparam l16.LUTMASK=16'h0101;
EFX_LUT4 l17(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[17])); defparam l17.LUTMASK=16'h017f;
EFX_LUT4 l18(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[18])); defparam l18.LUTMASK=16'h040b;
EFX_LUT4 l19(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[19])); defparam l19.LUTMASK=16'h0700;
EFX_LUT4 l20(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[20])); defparam l20.LUTMASK=16'h0707;
EFX_LUT4 l21(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[21])); defparam l21.LUTMASK=16'h0708;
EFX_LUT4 l22(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[22])); defparam l22.LUTMASK=16'h0777;
EFX_LUT4 l23(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[23])); defparam l23.LUTMASK=16'h0807;
EFX_LUT4 l24(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[24])); defparam l24.LUTMASK=16'h0990;
EFX_LUT4 l25(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[25])); defparam l25.LUTMASK=16'h0a03;
EFX_LUT4 l26(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[26])); defparam l26.LUTMASK=16'h0a0c;
EFX_LUT4 l27(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[27])); defparam l27.LUTMASK=16'h0b00;
EFX_LUT4 l28(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[28])); defparam l28.LUTMASK=16'h0b0b;
EFX_LUT4 l29(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[29])); defparam l29.LUTMASK=16'h0d00;
EFX_LUT4 l30(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[30])); defparam l30.LUTMASK=16'h0d0d;
EFX_LUT4 l31(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[31])); defparam l31.LUTMASK=16'h0e00;
EFX_LUT4 l32(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[32])); defparam l32.LUTMASK=16'h0e01;
EFX_LUT4 l33(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[33])); defparam l33.LUTMASK=16'h0e0e;
EFX_LUT4 l34(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[34])); defparam l34.LUTMASK=16'h0f77;
EFX_LUT4 l35(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[35])); defparam l35.LUTMASK=16'h1000;
EFX_LUT4 l36(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[36])); defparam l36.LUTMASK=16'h1001;
EFX_LUT4 l37(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[37])); defparam l37.LUTMASK=16'h1004;
EFX_LUT4 l38(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[38])); defparam l38.LUTMASK=16'h1010;
EFX_LUT4 l39(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[39])); defparam l39.LUTMASK=16'h1055;
EFX_LUT4 l40(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[40])); defparam l40.LUTMASK=16'h10ff;
EFX_LUT4 l41(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[41])); defparam l41.LUTMASK=16'h1111;
EFX_LUT4 l42(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[42])); defparam l42.LUTMASK=16'h1400;
EFX_LUT4 l43(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[43])); defparam l43.LUTMASK=16'h1411;
EFX_LUT4 l44(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[44])); defparam l44.LUTMASK=16'h1414;
EFX_LUT4 l45(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[45])); defparam l45.LUTMASK=16'h1700;
EFX_LUT4 l46(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[46])); defparam l46.LUTMASK=16'h1717;
EFX_LUT4 l47(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[47])); defparam l47.LUTMASK=16'h1c00;
EFX_LUT4 l48(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[48])); defparam l48.LUTMASK=16'h1e00;
EFX_LUT4 l49(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[49])); defparam l49.LUTMASK=16'h1f00;
EFX_LUT4 l50(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[50])); defparam l50.LUTMASK=16'h1fe0;
EFX_LUT4 l51(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[51])); defparam l51.LUTMASK=16'h2003;
EFX_LUT4 l52(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[52])); defparam l52.LUTMASK=16'h220a;
EFX_LUT4 l53(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[53])); defparam l53.LUTMASK=16'h2b2b;
EFX_LUT4 l54(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[54])); defparam l54.LUTMASK=16'h2bbb;
EFX_LUT4 l55(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[55])); defparam l55.LUTMASK=16'h2fff;
EFX_LUT4 l56(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[56])); defparam l56.LUTMASK=16'h32f3;
EFX_LUT4 l57(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[57])); defparam l57.LUTMASK=16'h3533;
EFX_LUT4 l58(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[58])); defparam l58.LUTMASK=16'h3535;
EFX_LUT4 l59(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[59])); defparam l59.LUTMASK=16'h3a3a;
EFX_LUT4 l60(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[60])); defparam l60.LUTMASK=16'h3c55;
EFX_LUT4 l61(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[61])); defparam l61.LUTMASK=16'h3caa;
EFX_LUT4 l62(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[62])); defparam l62.LUTMASK=16'h3f05;
EFX_LUT4 l63(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[63])); defparam l63.LUTMASK=16'h3f50;
EFX_LUT4 l64(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[64])); defparam l64.LUTMASK=16'h4000;
EFX_LUT4 l65(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[65])); defparam l65.LUTMASK=16'h4040;
EFX_LUT4 l66(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[66])); defparam l66.LUTMASK=16'h40bf;
EFX_LUT4 l67(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[67])); defparam l67.LUTMASK=16'h40fd;
EFX_LUT4 l68(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[68])); defparam l68.LUTMASK=16'h4100;
EFX_LUT4 l69(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[69])); defparam l69.LUTMASK=16'h4141;
EFX_LUT4 l70(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[70])); defparam l70.LUTMASK=16'h4444;
EFX_LUT4 l71(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[71])); defparam l71.LUTMASK=16'h4545;
EFX_LUT4 l72(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[72])); defparam l72.LUTMASK=16'h4555;
EFX_LUT4 l73(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[73])); defparam l73.LUTMASK=16'h4b00;
EFX_LUT4 l74(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[74])); defparam l74.LUTMASK=16'h4b4b;
EFX_LUT4 l75(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[75])); defparam l75.LUTMASK=16'h4d5f;
EFX_LUT4 l76(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[76])); defparam l76.LUTMASK=16'h4f00;
EFX_LUT4 l77(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[77])); defparam l77.LUTMASK=16'h4f4f;
EFX_LUT4 l78(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[78])); defparam l78.LUTMASK=16'h4fb0;
EFX_LUT4 l79(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[79])); defparam l79.LUTMASK=16'h503f;
EFX_LUT4 l80(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[80])); defparam l80.LUTMASK=16'h5300;
EFX_LUT4 l81(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[81])); defparam l81.LUTMASK=16'h5333;
EFX_LUT4 l82(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[82])); defparam l82.LUTMASK=16'h5353;
EFX_LUT4 l83(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[83])); defparam l83.LUTMASK=16'h53ac;
EFX_LUT4 l84(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[84])); defparam l84.LUTMASK=16'h54fd;
EFX_LUT4 l85(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[85])); defparam l85.LUTMASK=16'h5c00;
EFX_LUT4 l86(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[86])); defparam l86.LUTMASK=16'h5ca3;
EFX_LUT4 l87(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[87])); defparam l87.LUTMASK=16'h6000;
EFX_LUT4 l88(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[88])); defparam l88.LUTMASK=16'h6060;
EFX_LUT4 l89(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[89])); defparam l89.LUTMASK=16'h6666;
EFX_LUT4 l90(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[90])); defparam l90.LUTMASK=16'h6969;
EFX_LUT4 l91(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[91])); defparam l91.LUTMASK=16'h6bbc;
EFX_LUT4 l92(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[92])); defparam l92.LUTMASK=16'h7000;
EFX_LUT4 l93(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[93])); defparam l93.LUTMASK=16'h7070;
EFX_LUT4 l94(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[94])); defparam l94.LUTMASK=16'h7077;
EFX_LUT4 l95(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[95])); defparam l95.LUTMASK=16'h70ff;
EFX_LUT4 l96(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[96])); defparam l96.LUTMASK=16'h718e;
EFX_LUT4 l97(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[97])); defparam l97.LUTMASK=16'h75cf;
EFX_LUT4 l98(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[98])); defparam l98.LUTMASK=16'h7800;
EFX_LUT4 l99(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[99])); defparam l99.LUTMASK=16'h7878;
EFX_LUT4 l100(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[100])); defparam l100.LUTMASK=16'h7f00;
EFX_LUT4 l101(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[101])); defparam l101.LUTMASK=16'h7f80;
EFX_LUT4 l102(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[102])); defparam l102.LUTMASK=16'h7fa8;
EFX_LUT4 l103(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[103])); defparam l103.LUTMASK=16'h8000;
EFX_LUT4 l104(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[104])); defparam l104.LUTMASK=16'h807f;
EFX_LUT4 l105(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[105])); defparam l105.LUTMASK=16'h8080;
EFX_LUT4 l106(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[106])); defparam l106.LUTMASK=16'h8700;
EFX_LUT4 l107(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[107])); defparam l107.LUTMASK=16'h8787;
EFX_LUT4 l108(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[108])); defparam l108.LUTMASK=16'h8888;
EFX_LUT4 l109(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[109])); defparam l109.LUTMASK=16'h8aa0;
EFX_LUT4 l110(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[110])); defparam l110.LUTMASK=16'h8f00;
EFX_LUT4 l111(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[111])); defparam l111.LUTMASK=16'h8f88;
EFX_LUT4 l112(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[112])); defparam l112.LUTMASK=16'h8ff7;
EFX_LUT4 l113(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[113])); defparam l113.LUTMASK=16'h8fff;
EFX_LUT4 l114(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[114])); defparam l114.LUTMASK=16'h9000;
EFX_LUT4 l115(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[115])); defparam l115.LUTMASK=16'h9009;
EFX_LUT4 l116(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[116])); defparam l116.LUTMASK=16'h9090;
EFX_LUT4 l117(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[117])); defparam l117.LUTMASK=16'h9696;
EFX_LUT4 l118(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[118])); defparam l118.LUTMASK=16'h9999;
EFX_LUT4 l119(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[119])); defparam l119.LUTMASK=16'ha300;
EFX_LUT4 l120(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[120])); defparam l120.LUTMASK=16'ha333;
EFX_LUT4 l121(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[121])); defparam l121.LUTMASK=16'ha3a3;
EFX_LUT4 l122(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[122])); defparam l122.LUTMASK=16'hac00;
EFX_LUT4 l123(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[123])); defparam l123.LUTMASK=16'hac53;
EFX_LUT4 l124(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[124])); defparam l124.LUTMASK=16'hacac;
EFX_LUT4 l125(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[125])); defparam l125.LUTMASK=16'hb000;
EFX_LUT4 l126(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[126])); defparam l126.LUTMASK=16'hb00f;
EFX_LUT4 l127(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[127])); defparam l127.LUTMASK=16'hb04f;
EFX_LUT4 l128(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[128])); defparam l128.LUTMASK=16'hb0b0;
EFX_LUT4 l129(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[129])); defparam l129.LUTMASK=16'hb0bb;
EFX_LUT4 l130(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[130])); defparam l130.LUTMASK=16'hb2b2;
EFX_LUT4 l131(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[131])); defparam l131.LUTMASK=16'hb400;
EFX_LUT4 l132(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[132])); defparam l132.LUTMASK=16'hb4b4;
EFX_LUT4 l133(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[133])); defparam l133.LUTMASK=16'hbbb0;
EFX_LUT4 l134(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[134])); defparam l134.LUTMASK=16'hbbbb;
EFX_LUT4 l135(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[135])); defparam l135.LUTMASK=16'hbc00;
EFX_LUT4 l136(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[136])); defparam l136.LUTMASK=16'hbcbc;
EFX_LUT4 l137(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[137])); defparam l137.LUTMASK=16'hbf00;
EFX_LUT4 l138(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[138])); defparam l138.LUTMASK=16'hbf40;
EFX_LUT4 l139(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[139])); defparam l139.LUTMASK=16'hbfbf;
EFX_LUT4 l140(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[140])); defparam l140.LUTMASK=16'hbfff;
EFX_LUT4 l141(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[141])); defparam l141.LUTMASK=16'hc0ce;
EFX_LUT4 l142(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[142])); defparam l142.LUTMASK=16'hc100;
EFX_LUT4 l143(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[143])); defparam l143.LUTMASK=16'hc355;
EFX_LUT4 l144(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[144])); defparam l144.LUTMASK=16'hc500;
EFX_LUT4 l145(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[145])); defparam l145.LUTMASK=16'hc5c5;
EFX_LUT4 l146(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[146])); defparam l146.LUTMASK=16'hca00;
EFX_LUT4 l147(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[147])); defparam l147.LUTMASK=16'hd000;
EFX_LUT4 l148(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[148])); defparam l148.LUTMASK=16'hd0d0;
EFX_LUT4 l149(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[149])); defparam l149.LUTMASK=16'hd400;
EFX_LUT4 l150(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[150])); defparam l150.LUTMASK=16'he000;
EFX_LUT4 l151(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[151])); defparam l151.LUTMASK=16'he01f;
EFX_LUT4 l152(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[152])); defparam l152.LUTMASK=16'he0e0;
EFX_LUT4 l153(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[153])); defparam l153.LUTMASK=16'he1e1;
EFX_LUT4 l154(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[154])); defparam l154.LUTMASK=16'he3e3;
EFX_LUT4 l155(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[155])); defparam l155.LUTMASK=16'he7e7;
EFX_LUT4 l156(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[156])); defparam l156.LUTMASK=16'he830;
EFX_LUT4 l157(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[157])); defparam l157.LUTMASK=16'he97f;
EFX_LUT4 l158(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[158])); defparam l158.LUTMASK=16'hecfa;
EFX_LUT4 l159(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[159])); defparam l159.LUTMASK=16'hee0f;
EFX_LUT4 l160(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[160])); defparam l160.LUTMASK=16'heef0;
EFX_LUT4 l161(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[161])); defparam l161.LUTMASK=16'hef10;
EFX_LUT4 l162(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[162])); defparam l162.LUTMASK=16'hf0bb;
EFX_LUT4 l163(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[163])); defparam l163.LUTMASK=16'hf0ee;
EFX_LUT4 l164(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[164])); defparam l164.LUTMASK=16'hf100;
EFX_LUT4 l165(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[165])); defparam l165.LUTMASK=16'hf20d;
EFX_LUT4 l166(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[166])); defparam l166.LUTMASK=16'hf2ff;
EFX_LUT4 l167(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[167])); defparam l167.LUTMASK=16'hf305;
EFX_LUT4 l168(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[168])); defparam l168.LUTMASK=16'hf400;
EFX_LUT4 l169(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[169])); defparam l169.LUTMASK=16'hf800;
EFX_LUT4 l170(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[170])); defparam l170.LUTMASK=16'hf807;
EFX_LUT4 l171(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[171])); defparam l171.LUTMASK=16'hf8ff;
EFX_LUT4 l172(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[172])); defparam l172.LUTMASK=16'hfe00;
EFX_LUT4 l173(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[173])); defparam l173.LUTMASK=16'hfefe;
EFX_LUT4 l174(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[174])); defparam l174.LUTMASK=16'hfff8;
wire nor3,nor2; EFX_LUT4 u3(.I0(three[0]),.I1(three[1]),.I2(three[2]),.O(nor3));defparam u3.LUTMASK=16'h0101;
EFX_LUT4 u2(.I0(two[0]),.I1(two[1]),.O(nor2));defparam u2.LUTMASK=16'h1111;
integer n; integer failures=0;initial begin
#1;$display("INITIAL_ZERO a=%h y=%h nor3=%b nor2=%b",a,y,nor3,nor2);
if(y[0]!==1'b1) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=0001 actual=%b expected=1",y[0]);end
if(y[1]!==1'b1) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=0007 actual=%b expected=1",y[1]);end
if(y[2]!==1'b1) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=000b actual=%b expected=1",y[2]);end
if(y[3]!==1'b1) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=000d actual=%b expected=1",y[3]);end
if(y[4]!==1'b0) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=000e actual=%b expected=0",y[4]);end
if(y[5]!==1'b1) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=004f actual=%b expected=1",y[5]);end
if(y[6]!==1'b1) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=0071 actual=%b expected=1",y[6]);end
if(y[7]!==1'b1) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=007f actual=%b expected=1",y[7]);end
if(y[8]!==1'b1) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=008f actual=%b expected=1",y[8]);end
if(y[9]!==1'b0) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=00b2 actual=%b expected=0",y[9]);end
if(y[10]!==1'b1) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=00bf actual=%b expected=1",y[10]);end
if(y[11]!==1'b1) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=00ef actual=%b expected=1",y[11]);end
if(y[12]!==1'b1) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=00f1 actual=%b expected=1",y[12]);end
if(y[13]!==1'b0) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=00f4 actual=%b expected=0",y[13]);end
if(y[14]!==1'b0) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=00f8 actual=%b expected=0",y[14]);end
if(y[15]!==1'b0) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=0100 actual=%b expected=0",y[15]);end
if(y[16]!==1'b1) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=0101 actual=%b expected=1",y[16]);end
if(y[17]!==1'b1) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=017f actual=%b expected=1",y[17]);end
if(y[18]!==1'b1) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=040b actual=%b expected=1",y[18]);end
if(y[19]!==1'b0) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=0700 actual=%b expected=0",y[19]);end
if(y[20]!==1'b1) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=0707 actual=%b expected=1",y[20]);end
if(y[21]!==1'b0) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=0708 actual=%b expected=0",y[21]);end
if(y[22]!==1'b1) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=0777 actual=%b expected=1",y[22]);end
if(y[23]!==1'b1) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=0807 actual=%b expected=1",y[23]);end
if(y[24]!==1'b0) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=0990 actual=%b expected=0",y[24]);end
if(y[25]!==1'b1) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=0a03 actual=%b expected=1",y[25]);end
if(y[26]!==1'b0) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=0a0c actual=%b expected=0",y[26]);end
if(y[27]!==1'b0) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=0b00 actual=%b expected=0",y[27]);end
if(y[28]!==1'b1) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=0b0b actual=%b expected=1",y[28]);end
if(y[29]!==1'b0) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=0d00 actual=%b expected=0",y[29]);end
if(y[30]!==1'b1) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=0d0d actual=%b expected=1",y[30]);end
if(y[31]!==1'b0) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=0e00 actual=%b expected=0",y[31]);end
if(y[32]!==1'b1) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=0e01 actual=%b expected=1",y[32]);end
if(y[33]!==1'b0) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=0e0e actual=%b expected=0",y[33]);end
if(y[34]!==1'b1) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=0f77 actual=%b expected=1",y[34]);end
if(y[35]!==1'b0) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=1000 actual=%b expected=0",y[35]);end
if(y[36]!==1'b1) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=1001 actual=%b expected=1",y[36]);end
if(y[37]!==1'b0) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=1004 actual=%b expected=0",y[37]);end
if(y[38]!==1'b0) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=1010 actual=%b expected=0",y[38]);end
if(y[39]!==1'b1) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=1055 actual=%b expected=1",y[39]);end
if(y[40]!==1'b1) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=10ff actual=%b expected=1",y[40]);end
if(y[41]!==1'b1) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=1111 actual=%b expected=1",y[41]);end
if(y[42]!==1'b0) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=1400 actual=%b expected=0",y[42]);end
if(y[43]!==1'b1) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=1411 actual=%b expected=1",y[43]);end
if(y[44]!==1'b0) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=1414 actual=%b expected=0",y[44]);end
if(y[45]!==1'b0) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=1700 actual=%b expected=0",y[45]);end
if(y[46]!==1'b1) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=1717 actual=%b expected=1",y[46]);end
if(y[47]!==1'b0) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=1c00 actual=%b expected=0",y[47]);end
if(y[48]!==1'b0) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=1e00 actual=%b expected=0",y[48]);end
if(y[49]!==1'b0) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=1f00 actual=%b expected=0",y[49]);end
if(y[50]!==1'b0) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=1fe0 actual=%b expected=0",y[50]);end
if(y[51]!==1'b1) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=2003 actual=%b expected=1",y[51]);end
if(y[52]!==1'b0) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=220a actual=%b expected=0",y[52]);end
if(y[53]!==1'b1) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=2b2b actual=%b expected=1",y[53]);end
if(y[54]!==1'b1) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=2bbb actual=%b expected=1",y[54]);end
if(y[55]!==1'b1) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=2fff actual=%b expected=1",y[55]);end
if(y[56]!==1'b1) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=32f3 actual=%b expected=1",y[56]);end
if(y[57]!==1'b1) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=3533 actual=%b expected=1",y[57]);end
if(y[58]!==1'b1) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=3535 actual=%b expected=1",y[58]);end
if(y[59]!==1'b0) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=3a3a actual=%b expected=0",y[59]);end
if(y[60]!==1'b1) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=3c55 actual=%b expected=1",y[60]);end
if(y[61]!==1'b0) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=3caa actual=%b expected=0",y[61]);end
if(y[62]!==1'b1) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=3f05 actual=%b expected=1",y[62]);end
if(y[63]!==1'b0) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=3f50 actual=%b expected=0",y[63]);end
if(y[64]!==1'b0) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=4000 actual=%b expected=0",y[64]);end
if(y[65]!==1'b0) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=4040 actual=%b expected=0",y[65]);end
if(y[66]!==1'b1) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=40bf actual=%b expected=1",y[66]);end
if(y[67]!==1'b1) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=40fd actual=%b expected=1",y[67]);end
if(y[68]!==1'b0) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=4100 actual=%b expected=0",y[68]);end
if(y[69]!==1'b1) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=4141 actual=%b expected=1",y[69]);end
if(y[70]!==1'b0) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=4444 actual=%b expected=0",y[70]);end
if(y[71]!==1'b1) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=4545 actual=%b expected=1",y[71]);end
if(y[72]!==1'b1) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=4555 actual=%b expected=1",y[72]);end
if(y[73]!==1'b0) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=4b00 actual=%b expected=0",y[73]);end
if(y[74]!==1'b1) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=4b4b actual=%b expected=1",y[74]);end
if(y[75]!==1'b1) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=4d5f actual=%b expected=1",y[75]);end
if(y[76]!==1'b0) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=4f00 actual=%b expected=0",y[76]);end
if(y[77]!==1'b1) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=4f4f actual=%b expected=1",y[77]);end
if(y[78]!==1'b0) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=4fb0 actual=%b expected=0",y[78]);end
if(y[79]!==1'b1) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=503f actual=%b expected=1",y[79]);end
if(y[80]!==1'b0) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=5300 actual=%b expected=0",y[80]);end
if(y[81]!==1'b1) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=5333 actual=%b expected=1",y[81]);end
if(y[82]!==1'b1) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=5353 actual=%b expected=1",y[82]);end
if(y[83]!==1'b0) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=53ac actual=%b expected=0",y[83]);end
if(y[84]!==1'b1) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=54fd actual=%b expected=1",y[84]);end
if(y[85]!==1'b0) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=5c00 actual=%b expected=0",y[85]);end
if(y[86]!==1'b1) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=5ca3 actual=%b expected=1",y[86]);end
if(y[87]!==1'b0) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=6000 actual=%b expected=0",y[87]);end
if(y[88]!==1'b0) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=6060 actual=%b expected=0",y[88]);end
if(y[89]!==1'b0) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=6666 actual=%b expected=0",y[89]);end
if(y[90]!==1'b1) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=6969 actual=%b expected=1",y[90]);end
if(y[91]!==1'b0) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=6bbc actual=%b expected=0",y[91]);end
if(y[92]!==1'b0) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=7000 actual=%b expected=0",y[92]);end
if(y[93]!==1'b0) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=7070 actual=%b expected=0",y[93]);end
if(y[94]!==1'b1) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=7077 actual=%b expected=1",y[94]);end
if(y[95]!==1'b1) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=70ff actual=%b expected=1",y[95]);end
if(y[96]!==1'b0) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=718e actual=%b expected=0",y[96]);end
if(y[97]!==1'b1) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=75cf actual=%b expected=1",y[97]);end
if(y[98]!==1'b0) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=7800 actual=%b expected=0",y[98]);end
if(y[99]!==1'b0) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=7878 actual=%b expected=0",y[99]);end
if(y[100]!==1'b0) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=7f00 actual=%b expected=0",y[100]);end
if(y[101]!==1'b0) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=7f80 actual=%b expected=0",y[101]);end
if(y[102]!==1'b0) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=7fa8 actual=%b expected=0",y[102]);end
if(y[103]!==1'b0) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=8000 actual=%b expected=0",y[103]);end
if(y[104]!==1'b1) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=807f actual=%b expected=1",y[104]);end
if(y[105]!==1'b0) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=8080 actual=%b expected=0",y[105]);end
if(y[106]!==1'b0) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=8700 actual=%b expected=0",y[106]);end
if(y[107]!==1'b1) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=8787 actual=%b expected=1",y[107]);end
if(y[108]!==1'b0) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=8888 actual=%b expected=0",y[108]);end
if(y[109]!==1'b0) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=8aa0 actual=%b expected=0",y[109]);end
if(y[110]!==1'b0) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=8f00 actual=%b expected=0",y[110]);end
if(y[111]!==1'b0) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=8f88 actual=%b expected=0",y[111]);end
if(y[112]!==1'b1) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=8ff7 actual=%b expected=1",y[112]);end
if(y[113]!==1'b1) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=8fff actual=%b expected=1",y[113]);end
if(y[114]!==1'b0) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=9000 actual=%b expected=0",y[114]);end
if(y[115]!==1'b1) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=9009 actual=%b expected=1",y[115]);end
if(y[116]!==1'b0) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=9090 actual=%b expected=0",y[116]);end
if(y[117]!==1'b0) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=9696 actual=%b expected=0",y[117]);end
if(y[118]!==1'b1) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=9999 actual=%b expected=1",y[118]);end
if(y[119]!==1'b0) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=a300 actual=%b expected=0",y[119]);end
if(y[120]!==1'b1) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=a333 actual=%b expected=1",y[120]);end
if(y[121]!==1'b1) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=a3a3 actual=%b expected=1",y[121]);end
if(y[122]!==1'b0) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=ac00 actual=%b expected=0",y[122]);end
if(y[123]!==1'b1) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=ac53 actual=%b expected=1",y[123]);end
if(y[124]!==1'b0) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=acac actual=%b expected=0",y[124]);end
if(y[125]!==1'b0) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=b000 actual=%b expected=0",y[125]);end
if(y[126]!==1'b1) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=b00f actual=%b expected=1",y[126]);end
if(y[127]!==1'b1) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=b04f actual=%b expected=1",y[127]);end
if(y[128]!==1'b0) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=b0b0 actual=%b expected=0",y[128]);end
if(y[129]!==1'b1) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=b0bb actual=%b expected=1",y[129]);end
if(y[130]!==1'b0) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=b2b2 actual=%b expected=0",y[130]);end
if(y[131]!==1'b0) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=b400 actual=%b expected=0",y[131]);end
if(y[132]!==1'b0) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=b4b4 actual=%b expected=0",y[132]);end
if(y[133]!==1'b0) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=bbb0 actual=%b expected=0",y[133]);end
if(y[134]!==1'b1) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=bbbb actual=%b expected=1",y[134]);end
if(y[135]!==1'b0) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=bc00 actual=%b expected=0",y[135]);end
if(y[136]!==1'b0) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=bcbc actual=%b expected=0",y[136]);end
if(y[137]!==1'b0) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=bf00 actual=%b expected=0",y[137]);end
if(y[138]!==1'b0) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=bf40 actual=%b expected=0",y[138]);end
if(y[139]!==1'b1) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=bfbf actual=%b expected=1",y[139]);end
if(y[140]!==1'b1) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=bfff actual=%b expected=1",y[140]);end
if(y[141]!==1'b0) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=c0ce actual=%b expected=0",y[141]);end
if(y[142]!==1'b0) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=c100 actual=%b expected=0",y[142]);end
if(y[143]!==1'b1) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=c355 actual=%b expected=1",y[143]);end
if(y[144]!==1'b0) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=c500 actual=%b expected=0",y[144]);end
if(y[145]!==1'b1) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=c5c5 actual=%b expected=1",y[145]);end
if(y[146]!==1'b0) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=ca00 actual=%b expected=0",y[146]);end
if(y[147]!==1'b0) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=d000 actual=%b expected=0",y[147]);end
if(y[148]!==1'b0) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=d0d0 actual=%b expected=0",y[148]);end
if(y[149]!==1'b0) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=d400 actual=%b expected=0",y[149]);end
if(y[150]!==1'b0) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=e000 actual=%b expected=0",y[150]);end
if(y[151]!==1'b1) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=e01f actual=%b expected=1",y[151]);end
if(y[152]!==1'b0) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=e0e0 actual=%b expected=0",y[152]);end
if(y[153]!==1'b1) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=e1e1 actual=%b expected=1",y[153]);end
if(y[154]!==1'b1) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=e3e3 actual=%b expected=1",y[154]);end
if(y[155]!==1'b1) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=e7e7 actual=%b expected=1",y[155]);end
if(y[156]!==1'b0) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=e830 actual=%b expected=0",y[156]);end
if(y[157]!==1'b1) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=e97f actual=%b expected=1",y[157]);end
if(y[158]!==1'b0) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=ecfa actual=%b expected=0",y[158]);end
if(y[159]!==1'b1) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=ee0f actual=%b expected=1",y[159]);end
if(y[160]!==1'b0) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=eef0 actual=%b expected=0",y[160]);end
if(y[161]!==1'b0) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=ef10 actual=%b expected=0",y[161]);end
if(y[162]!==1'b1) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=f0bb actual=%b expected=1",y[162]);end
if(y[163]!==1'b0) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=f0ee actual=%b expected=0",y[163]);end
if(y[164]!==1'b0) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=f100 actual=%b expected=0",y[164]);end
if(y[165]!==1'b1) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=f20d actual=%b expected=1",y[165]);end
if(y[166]!==1'b1) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=f2ff actual=%b expected=1",y[166]);end
if(y[167]!==1'b1) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=f305 actual=%b expected=1",y[167]);end
if(y[168]!==1'b0) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=f400 actual=%b expected=0",y[168]);end
if(y[169]!==1'b0) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=f800 actual=%b expected=0",y[169]);end
if(y[170]!==1'b1) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=f807 actual=%b expected=1",y[170]);end
if(y[171]!==1'b1) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=f8ff actual=%b expected=1",y[171]);end
if(y[172]!==1'b0) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=fe00 actual=%b expected=0",y[172]);end
if(y[173]!==1'b0) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=fefe actual=%b expected=0",y[173]);end
if(y[174]!==1'b0) begin failures=failures+1;$display("INITIAL_MASK_FAIL mask=fff8 actual=%b expected=0",y[174]);end
a=4'bx;three=3'bx;two=2'bx;#1;a=0;three=0;two=0;#1;
$display("EXPLICIT_X_TO_ZERO a=%h y=%h nor3=%b nor2=%b",a,y,nor3,nor2);
for(n=0;n<16;n=n+1)begin a=n;#1;
if(y[0]!==((16'h0001>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=0001 input=%h actual=%b",a,y[0]);end
if(y[1]!==((16'h0007>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=0007 input=%h actual=%b",a,y[1]);end
if(y[2]!==((16'h000b>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=000b input=%h actual=%b",a,y[2]);end
if(y[3]!==((16'h000d>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=000d input=%h actual=%b",a,y[3]);end
if(y[4]!==((16'h000e>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=000e input=%h actual=%b",a,y[4]);end
if(y[5]!==((16'h004f>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=004f input=%h actual=%b",a,y[5]);end
if(y[6]!==((16'h0071>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=0071 input=%h actual=%b",a,y[6]);end
if(y[7]!==((16'h007f>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=007f input=%h actual=%b",a,y[7]);end
if(y[8]!==((16'h008f>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=008f input=%h actual=%b",a,y[8]);end
if(y[9]!==((16'h00b2>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=00b2 input=%h actual=%b",a,y[9]);end
if(y[10]!==((16'h00bf>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=00bf input=%h actual=%b",a,y[10]);end
if(y[11]!==((16'h00ef>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=00ef input=%h actual=%b",a,y[11]);end
if(y[12]!==((16'h00f1>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=00f1 input=%h actual=%b",a,y[12]);end
if(y[13]!==((16'h00f4>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=00f4 input=%h actual=%b",a,y[13]);end
if(y[14]!==((16'h00f8>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=00f8 input=%h actual=%b",a,y[14]);end
if(y[15]!==((16'h0100>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=0100 input=%h actual=%b",a,y[15]);end
if(y[16]!==((16'h0101>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=0101 input=%h actual=%b",a,y[16]);end
if(y[17]!==((16'h017f>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=017f input=%h actual=%b",a,y[17]);end
if(y[18]!==((16'h040b>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=040b input=%h actual=%b",a,y[18]);end
if(y[19]!==((16'h0700>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=0700 input=%h actual=%b",a,y[19]);end
if(y[20]!==((16'h0707>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=0707 input=%h actual=%b",a,y[20]);end
if(y[21]!==((16'h0708>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=0708 input=%h actual=%b",a,y[21]);end
if(y[22]!==((16'h0777>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=0777 input=%h actual=%b",a,y[22]);end
if(y[23]!==((16'h0807>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=0807 input=%h actual=%b",a,y[23]);end
if(y[24]!==((16'h0990>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=0990 input=%h actual=%b",a,y[24]);end
if(y[25]!==((16'h0a03>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=0a03 input=%h actual=%b",a,y[25]);end
if(y[26]!==((16'h0a0c>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=0a0c input=%h actual=%b",a,y[26]);end
if(y[27]!==((16'h0b00>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=0b00 input=%h actual=%b",a,y[27]);end
if(y[28]!==((16'h0b0b>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=0b0b input=%h actual=%b",a,y[28]);end
if(y[29]!==((16'h0d00>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=0d00 input=%h actual=%b",a,y[29]);end
if(y[30]!==((16'h0d0d>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=0d0d input=%h actual=%b",a,y[30]);end
if(y[31]!==((16'h0e00>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=0e00 input=%h actual=%b",a,y[31]);end
if(y[32]!==((16'h0e01>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=0e01 input=%h actual=%b",a,y[32]);end
if(y[33]!==((16'h0e0e>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=0e0e input=%h actual=%b",a,y[33]);end
if(y[34]!==((16'h0f77>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=0f77 input=%h actual=%b",a,y[34]);end
if(y[35]!==((16'h1000>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=1000 input=%h actual=%b",a,y[35]);end
if(y[36]!==((16'h1001>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=1001 input=%h actual=%b",a,y[36]);end
if(y[37]!==((16'h1004>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=1004 input=%h actual=%b",a,y[37]);end
if(y[38]!==((16'h1010>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=1010 input=%h actual=%b",a,y[38]);end
if(y[39]!==((16'h1055>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=1055 input=%h actual=%b",a,y[39]);end
if(y[40]!==((16'h10ff>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=10ff input=%h actual=%b",a,y[40]);end
if(y[41]!==((16'h1111>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=1111 input=%h actual=%b",a,y[41]);end
if(y[42]!==((16'h1400>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=1400 input=%h actual=%b",a,y[42]);end
if(y[43]!==((16'h1411>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=1411 input=%h actual=%b",a,y[43]);end
if(y[44]!==((16'h1414>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=1414 input=%h actual=%b",a,y[44]);end
if(y[45]!==((16'h1700>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=1700 input=%h actual=%b",a,y[45]);end
if(y[46]!==((16'h1717>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=1717 input=%h actual=%b",a,y[46]);end
if(y[47]!==((16'h1c00>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=1c00 input=%h actual=%b",a,y[47]);end
if(y[48]!==((16'h1e00>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=1e00 input=%h actual=%b",a,y[48]);end
if(y[49]!==((16'h1f00>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=1f00 input=%h actual=%b",a,y[49]);end
if(y[50]!==((16'h1fe0>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=1fe0 input=%h actual=%b",a,y[50]);end
if(y[51]!==((16'h2003>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=2003 input=%h actual=%b",a,y[51]);end
if(y[52]!==((16'h220a>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=220a input=%h actual=%b",a,y[52]);end
if(y[53]!==((16'h2b2b>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=2b2b input=%h actual=%b",a,y[53]);end
if(y[54]!==((16'h2bbb>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=2bbb input=%h actual=%b",a,y[54]);end
if(y[55]!==((16'h2fff>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=2fff input=%h actual=%b",a,y[55]);end
if(y[56]!==((16'h32f3>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=32f3 input=%h actual=%b",a,y[56]);end
if(y[57]!==((16'h3533>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=3533 input=%h actual=%b",a,y[57]);end
if(y[58]!==((16'h3535>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=3535 input=%h actual=%b",a,y[58]);end
if(y[59]!==((16'h3a3a>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=3a3a input=%h actual=%b",a,y[59]);end
if(y[60]!==((16'h3c55>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=3c55 input=%h actual=%b",a,y[60]);end
if(y[61]!==((16'h3caa>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=3caa input=%h actual=%b",a,y[61]);end
if(y[62]!==((16'h3f05>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=3f05 input=%h actual=%b",a,y[62]);end
if(y[63]!==((16'h3f50>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=3f50 input=%h actual=%b",a,y[63]);end
if(y[64]!==((16'h4000>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=4000 input=%h actual=%b",a,y[64]);end
if(y[65]!==((16'h4040>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=4040 input=%h actual=%b",a,y[65]);end
if(y[66]!==((16'h40bf>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=40bf input=%h actual=%b",a,y[66]);end
if(y[67]!==((16'h40fd>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=40fd input=%h actual=%b",a,y[67]);end
if(y[68]!==((16'h4100>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=4100 input=%h actual=%b",a,y[68]);end
if(y[69]!==((16'h4141>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=4141 input=%h actual=%b",a,y[69]);end
if(y[70]!==((16'h4444>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=4444 input=%h actual=%b",a,y[70]);end
if(y[71]!==((16'h4545>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=4545 input=%h actual=%b",a,y[71]);end
if(y[72]!==((16'h4555>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=4555 input=%h actual=%b",a,y[72]);end
if(y[73]!==((16'h4b00>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=4b00 input=%h actual=%b",a,y[73]);end
if(y[74]!==((16'h4b4b>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=4b4b input=%h actual=%b",a,y[74]);end
if(y[75]!==((16'h4d5f>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=4d5f input=%h actual=%b",a,y[75]);end
if(y[76]!==((16'h4f00>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=4f00 input=%h actual=%b",a,y[76]);end
if(y[77]!==((16'h4f4f>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=4f4f input=%h actual=%b",a,y[77]);end
if(y[78]!==((16'h4fb0>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=4fb0 input=%h actual=%b",a,y[78]);end
if(y[79]!==((16'h503f>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=503f input=%h actual=%b",a,y[79]);end
if(y[80]!==((16'h5300>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=5300 input=%h actual=%b",a,y[80]);end
if(y[81]!==((16'h5333>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=5333 input=%h actual=%b",a,y[81]);end
if(y[82]!==((16'h5353>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=5353 input=%h actual=%b",a,y[82]);end
if(y[83]!==((16'h53ac>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=53ac input=%h actual=%b",a,y[83]);end
if(y[84]!==((16'h54fd>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=54fd input=%h actual=%b",a,y[84]);end
if(y[85]!==((16'h5c00>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=5c00 input=%h actual=%b",a,y[85]);end
if(y[86]!==((16'h5ca3>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=5ca3 input=%h actual=%b",a,y[86]);end
if(y[87]!==((16'h6000>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=6000 input=%h actual=%b",a,y[87]);end
if(y[88]!==((16'h6060>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=6060 input=%h actual=%b",a,y[88]);end
if(y[89]!==((16'h6666>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=6666 input=%h actual=%b",a,y[89]);end
if(y[90]!==((16'h6969>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=6969 input=%h actual=%b",a,y[90]);end
if(y[91]!==((16'h6bbc>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=6bbc input=%h actual=%b",a,y[91]);end
if(y[92]!==((16'h7000>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=7000 input=%h actual=%b",a,y[92]);end
if(y[93]!==((16'h7070>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=7070 input=%h actual=%b",a,y[93]);end
if(y[94]!==((16'h7077>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=7077 input=%h actual=%b",a,y[94]);end
if(y[95]!==((16'h70ff>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=70ff input=%h actual=%b",a,y[95]);end
if(y[96]!==((16'h718e>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=718e input=%h actual=%b",a,y[96]);end
if(y[97]!==((16'h75cf>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=75cf input=%h actual=%b",a,y[97]);end
if(y[98]!==((16'h7800>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=7800 input=%h actual=%b",a,y[98]);end
if(y[99]!==((16'h7878>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=7878 input=%h actual=%b",a,y[99]);end
if(y[100]!==((16'h7f00>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=7f00 input=%h actual=%b",a,y[100]);end
if(y[101]!==((16'h7f80>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=7f80 input=%h actual=%b",a,y[101]);end
if(y[102]!==((16'h7fa8>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=7fa8 input=%h actual=%b",a,y[102]);end
if(y[103]!==((16'h8000>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=8000 input=%h actual=%b",a,y[103]);end
if(y[104]!==((16'h807f>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=807f input=%h actual=%b",a,y[104]);end
if(y[105]!==((16'h8080>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=8080 input=%h actual=%b",a,y[105]);end
if(y[106]!==((16'h8700>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=8700 input=%h actual=%b",a,y[106]);end
if(y[107]!==((16'h8787>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=8787 input=%h actual=%b",a,y[107]);end
if(y[108]!==((16'h8888>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=8888 input=%h actual=%b",a,y[108]);end
if(y[109]!==((16'h8aa0>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=8aa0 input=%h actual=%b",a,y[109]);end
if(y[110]!==((16'h8f00>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=8f00 input=%h actual=%b",a,y[110]);end
if(y[111]!==((16'h8f88>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=8f88 input=%h actual=%b",a,y[111]);end
if(y[112]!==((16'h8ff7>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=8ff7 input=%h actual=%b",a,y[112]);end
if(y[113]!==((16'h8fff>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=8fff input=%h actual=%b",a,y[113]);end
if(y[114]!==((16'h9000>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=9000 input=%h actual=%b",a,y[114]);end
if(y[115]!==((16'h9009>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=9009 input=%h actual=%b",a,y[115]);end
if(y[116]!==((16'h9090>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=9090 input=%h actual=%b",a,y[116]);end
if(y[117]!==((16'h9696>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=9696 input=%h actual=%b",a,y[117]);end
if(y[118]!==((16'h9999>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=9999 input=%h actual=%b",a,y[118]);end
if(y[119]!==((16'ha300>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=a300 input=%h actual=%b",a,y[119]);end
if(y[120]!==((16'ha333>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=a333 input=%h actual=%b",a,y[120]);end
if(y[121]!==((16'ha3a3>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=a3a3 input=%h actual=%b",a,y[121]);end
if(y[122]!==((16'hac00>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=ac00 input=%h actual=%b",a,y[122]);end
if(y[123]!==((16'hac53>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=ac53 input=%h actual=%b",a,y[123]);end
if(y[124]!==((16'hacac>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=acac input=%h actual=%b",a,y[124]);end
if(y[125]!==((16'hb000>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=b000 input=%h actual=%b",a,y[125]);end
if(y[126]!==((16'hb00f>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=b00f input=%h actual=%b",a,y[126]);end
if(y[127]!==((16'hb04f>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=b04f input=%h actual=%b",a,y[127]);end
if(y[128]!==((16'hb0b0>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=b0b0 input=%h actual=%b",a,y[128]);end
if(y[129]!==((16'hb0bb>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=b0bb input=%h actual=%b",a,y[129]);end
if(y[130]!==((16'hb2b2>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=b2b2 input=%h actual=%b",a,y[130]);end
if(y[131]!==((16'hb400>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=b400 input=%h actual=%b",a,y[131]);end
if(y[132]!==((16'hb4b4>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=b4b4 input=%h actual=%b",a,y[132]);end
if(y[133]!==((16'hbbb0>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=bbb0 input=%h actual=%b",a,y[133]);end
if(y[134]!==((16'hbbbb>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=bbbb input=%h actual=%b",a,y[134]);end
if(y[135]!==((16'hbc00>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=bc00 input=%h actual=%b",a,y[135]);end
if(y[136]!==((16'hbcbc>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=bcbc input=%h actual=%b",a,y[136]);end
if(y[137]!==((16'hbf00>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=bf00 input=%h actual=%b",a,y[137]);end
if(y[138]!==((16'hbf40>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=bf40 input=%h actual=%b",a,y[138]);end
if(y[139]!==((16'hbfbf>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=bfbf input=%h actual=%b",a,y[139]);end
if(y[140]!==((16'hbfff>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=bfff input=%h actual=%b",a,y[140]);end
if(y[141]!==((16'hc0ce>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=c0ce input=%h actual=%b",a,y[141]);end
if(y[142]!==((16'hc100>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=c100 input=%h actual=%b",a,y[142]);end
if(y[143]!==((16'hc355>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=c355 input=%h actual=%b",a,y[143]);end
if(y[144]!==((16'hc500>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=c500 input=%h actual=%b",a,y[144]);end
if(y[145]!==((16'hc5c5>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=c5c5 input=%h actual=%b",a,y[145]);end
if(y[146]!==((16'hca00>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=ca00 input=%h actual=%b",a,y[146]);end
if(y[147]!==((16'hd000>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=d000 input=%h actual=%b",a,y[147]);end
if(y[148]!==((16'hd0d0>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=d0d0 input=%h actual=%b",a,y[148]);end
if(y[149]!==((16'hd400>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=d400 input=%h actual=%b",a,y[149]);end
if(y[150]!==((16'he000>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=e000 input=%h actual=%b",a,y[150]);end
if(y[151]!==((16'he01f>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=e01f input=%h actual=%b",a,y[151]);end
if(y[152]!==((16'he0e0>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=e0e0 input=%h actual=%b",a,y[152]);end
if(y[153]!==((16'he1e1>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=e1e1 input=%h actual=%b",a,y[153]);end
if(y[154]!==((16'he3e3>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=e3e3 input=%h actual=%b",a,y[154]);end
if(y[155]!==((16'he7e7>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=e7e7 input=%h actual=%b",a,y[155]);end
if(y[156]!==((16'he830>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=e830 input=%h actual=%b",a,y[156]);end
if(y[157]!==((16'he97f>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=e97f input=%h actual=%b",a,y[157]);end
if(y[158]!==((16'hecfa>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=ecfa input=%h actual=%b",a,y[158]);end
if(y[159]!==((16'hee0f>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=ee0f input=%h actual=%b",a,y[159]);end
if(y[160]!==((16'heef0>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=eef0 input=%h actual=%b",a,y[160]);end
if(y[161]!==((16'hef10>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=ef10 input=%h actual=%b",a,y[161]);end
if(y[162]!==((16'hf0bb>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=f0bb input=%h actual=%b",a,y[162]);end
if(y[163]!==((16'hf0ee>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=f0ee input=%h actual=%b",a,y[163]);end
if(y[164]!==((16'hf100>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=f100 input=%h actual=%b",a,y[164]);end
if(y[165]!==((16'hf20d>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=f20d input=%h actual=%b",a,y[165]);end
if(y[166]!==((16'hf2ff>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=f2ff input=%h actual=%b",a,y[166]);end
if(y[167]!==((16'hf305>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=f305 input=%h actual=%b",a,y[167]);end
if(y[168]!==((16'hf400>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=f400 input=%h actual=%b",a,y[168]);end
if(y[169]!==((16'hf800>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=f800 input=%h actual=%b",a,y[169]);end
if(y[170]!==((16'hf807>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=f807 input=%h actual=%b",a,y[170]);end
if(y[171]!==((16'hf8ff>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=f8ff input=%h actual=%b",a,y[171]);end
if(y[172]!==((16'hfe00>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=fe00 input=%h actual=%b",a,y[172]);end
if(y[173]!==((16'hfefe>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=fefe input=%h actual=%b",a,y[173]);end
if(y[174]!==((16'hfff8>>n)&1'b1))begin failures=failures+1;$display("MASK_FAIL mask=fff8 input=%h actual=%b",a,y[174]);end
end
$display("VENDOR_LUT_TINY_RESULT masks=%0d failures=%0d",175,failures);$finish;end endmodule
