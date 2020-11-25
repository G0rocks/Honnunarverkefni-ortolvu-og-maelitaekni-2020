cd 'C:\Users\Rúnar U\Documents\Skóli\Tölvunarfræði\Örtölvu- og mælitækni\Hópverkefni - Hönnun\H-nnunarverkefni-rt-lvu-og-m-lit-kni-2020\KodaVinnsla\Maelingar\csv_files'

do for [j=1:12] {

	set term pdf
	inFile = sprintf('results_%i.csv', j)
	outFile = sprintf('results_%i.pdf', j)
	
	unset key
	
	set xlabel 'Tími (s)'
	set ylabel 'Hitastig (°C)
	
	set output outFile
	plot inFile u 1:2
	
	unset output



}