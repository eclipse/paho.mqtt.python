DIRS=lib
DOCDIRS=
DISTDIRS=

.PHONY : all docs clean reallyclean test

all : docs
	for d in ${DIRS}; do $(MAKE) -C $${d}; done

docs :
	for d in ${DOCDIRS}; do $(MAKE) -C $${d}; done

clean :
	for d in ${DIRS}; do $(MAKE) -C $${d} clean; done
	for d in ${DOCDIRS}; do $(MAKE) -C $${d} clean; done
	$(MAKE) -C test clean

reallyclean : 
	for d in ${DIRS}; do $(MAKE) -C $${d} reallyclean; done
	for d in ${DOCDIRS}; do $(MAKE) -C $${d} reallyclean; done
	$(MAKE) -C test reallyclean
	-rm -f *.orig

test :
	$(MAKE) -C test test

