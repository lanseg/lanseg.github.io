html: index.m4.html projects.m4.html about.m4.html
	m4 index.m4.html > index.html
	m4 projects.m4.html > projects.html
	m4 about.m4.html > about.html

clean:
	rm -fv index.html projects.html about.html

watch:
	while true; do \
		inotifywait -e close_write *; \
		make clean; \
		make html; \
	done
