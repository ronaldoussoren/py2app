all:
	echo "stubs: Create sub executables"
	echo "clean: Remove stubs"

stubs:
	python -m py2app._apptemplate

clean:
	rm  src/py2app/_apptemplate/launcher-*-*


.PHONY: stubs clean
