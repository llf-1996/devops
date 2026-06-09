ARG SENTRY_IMAGE
FROM ${SENTRY_IMAGE:-sentry:9.1.2}-onbuild

# Applied before Python/uWSGI start; worker container RSS ~130MB confirms this works
ENV MALLOC_ARENA_MAX=2
