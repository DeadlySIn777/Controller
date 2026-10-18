"""Wider exact same-layer search, preserving R91's bounded-window failure."""
from pathlib import Path
p=Path(__file__).resolve().parent
s=(p/'construct_u19008_reference_power_tree_r91.py').read_text()
s=s.replace("s=s.replace(\"OUT=HERE/'u19008-outside-reservation-power-tree-r88'\",\"OUT=HERE/'u19008-reference-covered-power-tree-r91'\")", "s=s.replace(\"OUT=HERE/'u19008-outside-reservation-power-tree-r88'\",\"OUT=HERE/'u19008-wide-reference-power-tree-r92'\")")
s=s.replace("s=s.replace(\"controller-u19008-r88/\", \"controller-u19008-r91/\")", "s=s.replace(\"controller-u19008-r88/\", \"controller-u19008-r92/\")")
s=s.replace("exec(compile(s,", "s=s.replace('win=box(57,105,70,116)', 'win=box(52,100,85,123)')\ns=s.replace(\"min(t['a'][0],t['b'][0])-t['w']/2<70.9 and max(t['a'][0],t['b'][0])+t['w']/2>56.1 and min(t['a'][1],t['b'][1])-t['w']/2<116.9 and max(t['a'][1],t['b'][1])+t['w']/2>104.1\", \"min(t['a'][0],t['b'][0])-t['w']/2<85.9 and max(t['a'][0],t['b'][0])+t['w']/2>51.1 and min(t['a'][1],t['b'][1])-t['w']/2<123.9 and max(t['a'][1],t['b'][1])+t['w']/2>99.1\")\ns=s.replace(\"56.1<v['x']<70.9 and 104.1<v['y']<116.9\", \"51.1<v['x']<85.9 and 99.1<v['y']<123.9\")\nexec(compile(s,")
exec(compile(s,str(p/'construct_u19008_reference_power_tree_r91.py'),'exec'))
