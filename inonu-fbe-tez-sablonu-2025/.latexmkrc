# Inonu FBE tez sablonu XeLaTeX ile derlenmelidir.
# latexmk kullaniliyorsa bu ayar PDF uretimini xelatex ile yapar.
$pdf_mode = 5;
$xelatex = 'xelatex -interaction=nonstopmode -synctex=1 %O %S';
