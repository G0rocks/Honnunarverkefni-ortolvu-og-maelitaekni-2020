cd 'C:\Users\Rúnar U\Documents\Skóli\Tölvunarfræði\Örtölvu- og mælitækni\Hópverkefni - Hönnun\H-nnunarverkefni-rt-lvu-og-m-lit-kni-2020\KodaVinnsla\Maelingar\control_test_files'



set term pdf

unset key

set xlabel 'Tími (s)'
set ylabel 'Hitastig (°C)'

set ytics nomirror
set y2tics

set output 'control_test.pdf'
plot 'control_test.csv' u 1:2,\
	'control_test.csv' u 1:6 with lines,\
	'control_test.csv' u 1:9 with lines axis x1y2,\
	'control_test.csv' u 1:4 with lines axis x1y2

unset output



