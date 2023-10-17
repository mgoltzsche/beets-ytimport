PYPI_REPO=https://upload.pypi.org/legacy/
DOCKER_OPTS=--rm -u `id -u`:`id -g` \
		-v "`pwd`:/work" -w /work \
		--entrypoint sh $(PYTHON_IMG) -c

define DOCKERFILE
FROM python:3.9-alpine
RUN python -m pip install twine==4.0.2
endef
export DOCKERFILE
BUILDIMG=ytimport-build

DOCKER_OPTS=--rm -u `id -u`:`id -g` \
                -v "`pwd`:/work" -w /work \
                --entrypoint sh $(BUILDIMG) -c


egg: buildcontainer
	docker run $(DOCKER_OPTS) 'python3 setup.py bdist_wheel'

release: egg
	docker run -e PYPI_USER -e PYPI_PASS -e PYPI_REPO=$(PYPI_REPO) \
		$(DOCKER_OPTS) \
		'python3 -m twine upload --repository-url "$$PYPI_REPO" -u "$$PYPI_USER" -p "$$PYPI_PASS" dist/*'

clean:
	rm -rf build dist *.egg-info

buildcontainer:
	echo "$$DOCKERFILE" | docker build --force-rm -f - -t $(BUILDIMG) .
