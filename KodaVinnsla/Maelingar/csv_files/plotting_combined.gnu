cd 'C:\Users\Rúnar U\Documents\Skóli\Tölvunarfræði\Örtölvu- og mælitækni\Hópverkefni - Hönnun\H-nnunarverkefni-rt-lvu-og-m-lit-kni-2020\KodaVinnsla\Maelingar\csv_files'



set term pdfcairo

unset key

set xlabel 'Tími (s)'
set ylabel 'Hitastig (°C)

set output 'results_combined.pdf'
plot for [j=2:11] sprintf('results_%i.csv', j) u 1:2 with dots pc j

unset output



