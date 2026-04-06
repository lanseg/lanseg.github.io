index.html: index.m4.html
	m4 index.m4.html > index.html

diary.html: diary.m4.html
	m4 diary.m4.html > diary.html

watch:
	while true; do \
		inotifywait -e close_write *; \
		rm -fv index.html; rm -rf diary.html;\
		make index.html; make diary.html; \
	done
