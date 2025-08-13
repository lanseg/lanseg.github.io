index.html: index.m4.html
	m4 index.m4.html > index.html

watch:
	while true; do \
		inotifywait -e close_write index.m4.html; \
		make index.html; \
	done

