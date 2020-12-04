build:
	pip install -r requirements.txt
	python setup.py build

upload:
	python setup.py bdist_wheel --universal upload -r hobot-local

clean:
	@rm -rf build dist image_viewer.egg-info

lint:
	pylint image-viewer --reports=n

lintfull:
	pylint image-viewer

install:
	python setup.py install

uninstall:
	python setup.py install --record install.log
	cat install.log | xargs rm -rf 
	@rm install.log
