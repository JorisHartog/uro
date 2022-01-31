.PHONY: clean

%.s: src/%.uro
	python ./uro0/uro.py $^ > $@

%.o: %.s
	nasm -f elf64 $^ -i $@

%.bin: %.o
	ld -dynamic-linker /lib64/ld-linux-x86-64.so.2 -lc $^ -e main -o $@

clean:
	rm *.o *.s *.bin
