FROM node:21.7.1-alpine AS frontend

WORKDIR /app

COPY frontend/package*.json ./
RUN npm install

COPY frontend/ ./
RUN npm run build

FROM nginx:1.22.1

COPY --from=frontend /app/build /staticfiles
COPY docs /usr/share/nginx/html/api/docs
COPY nginx/nginx.conf /etc/nginx/templates/default.conf.template
