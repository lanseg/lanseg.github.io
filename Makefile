index.html: index.m4.html
	m4 index.m4.html > index.html

watch:
	while true; do \
		inotifywait -e close_write *; \
		rm -f index.html; \
		make index.html; \
	done

