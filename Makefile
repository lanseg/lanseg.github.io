html: index.m4.html featured.m4.html about.m4.html
	m4 index.m4.html > index.html
	m4 featured.m4.html > featured.html
	m4 about.m4.html > about.html

clean:
	rm -fv index.html featured.html about.html

watch:
	while true; do \
		inotifywait -r -e close_write *; \
		make clean; \
		make html; \
	done
