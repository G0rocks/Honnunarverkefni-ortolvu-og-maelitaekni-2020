cd 'C:\Users\R�nar U\Documents\Sk�li\T�lvunarfr��i\�rt�lvu- og m�lit�kni\H�pverkefni - H�nnun\H-nnunarverkefni-rt-lvu-og-m-lit-kni-2020\KodaVinnsla\Maelingar\csv_files'

do for [j=1:12] {

	set term pdf
	inFile = sprintf('results_%i.csv', j)
	outFile = sprintf('results_%i.pdf', j)
	
	unset key
	
	set xlabel 'T�mi (s)'
	set ylabel 'Hitastig (�C)
	
	set output outFile
	plot inFile u 1:2
	
	unset output



}