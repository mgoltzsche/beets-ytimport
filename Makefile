PYPI_REPO=https://upload.pypi.org/legacy/
define DOCKERFILE
FROM python:3.9-alpine
RUN python -m pip install twine==4.0.2
endef
export DOCKERFILE
BEETS_IMG=beets-ytimport
BUILD_IMG=ytimport-build
DOCKER_OPTS=--rm -u `id -u`:`id -g` \
                -v "`pwd`:/work" -w /work \
                --entrypoint sh $(BUILD_IMG) -c

.PHONY: egg
egg: clean python-container
	docker run $(DOCKER_OPTS) 'python3 setup.py bdist_wheel'

.PHONY: beets-sh
beets-sh: beets-container
	mkdir -p data
	docker run -ti --rm -u `id -u`:`id -g` \
		-v "`pwd`/data:/data" \
		--entrypoint sh $(BEETS_IMG)

.PHONY: beets-container
beets-container: egg
	docker build --rm -t $(BEETS_IMG) .

.PHONY: release
release: clean egg
	docker run -e PYPI_USER -e PYPI_PASS -e PYPI_REPO=$(PYPI_REPO) \
		$(DOCKER_OPTS) \
		'python3 -m twine upload --repository-url "$$PYPI_REPO" -u "$$PYPI_USER" -p "$$PYPI_PASS" dist/*'

.PHONY: clean
clean:
	rm -rf build dist *.egg-info

.PHONY: clean-data
clean-data: clean
	rm -rf data

.PHONY: python-container
python-container:
	echo "$$DOCKERFILE" | docker build --rm -f - -t $(BUILD_IMG) .

