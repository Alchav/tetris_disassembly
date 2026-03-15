rgbasm -o main.o main.asm
rgblink -o tetris.gb main.o -n tetris.sym
python3 extractor.py