cd 'C:\Users\R�nar U\Documents\Sk�li\T�lvunarfr��i\�rt�lvu- og m�lit�kni\H�pverkefni - H�nnun\H-nnunarverkefni-rt-lvu-og-m-lit-kni-2020\KodaVinnsla\Maelingar\csv_files'



set term pdfcairo

unset key

set xlabel 'T�mi (s)'
set ylabel 'Hitastig (�C)

set output 'results_combined.pdf'
plot for [j=2:11] sprintf('results_%i.csv', j) u 1:2 with dots pc j

unset output



