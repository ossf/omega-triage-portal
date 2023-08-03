FROM nginx:1.24.0-alpine

ENV TRIAGE_PORTAL_HOST=localhost
RUN rm /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d
COPY templates/ /etc/nginx/templates/
EXPOSE 80
