SKILL := skills/pr-explainer-video

.PHONY: help test package example clean

help:
	@echo "make test      the layout check catches planted problems and passes the example (Docker, a few minutes)"
	@echo "make package   dist/pr-explainer-video.skill: the skill folder as one zip file"
	@echo "make example   render the worked example to build/example.mp4 (1080p60, about 20 minutes)"
	@echo "make clean     remove build/ and dist/"

test:
	tests/test_layout.sh

package:
	find $(SKILL) -name __pycache__ -prune -exec rm -rf {} +
	mkdir -p dist
	rm -f dist/pr-explainer-video.skill
	cd skills && python3 -m zipfile -c ../dist/pr-explainer-video.skill pr-explainer-video
	@echo "dist/pr-explainer-video.skill"

example:
	mkdir -p build
	cp $(SKILL)/scripts/* $(SKILL)/references/example.py build/
	cd build && ./pv.sh high example.py

clean:
	rm -rf build dist
