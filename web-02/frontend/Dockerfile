FROM node:20-alpine AS build
WORKDIR /src
COPY web-02/frontend/package.json web-02/frontend/package-lock.json ./
RUN npm ci
COPY web-02/frontend ./
RUN npm run build

FROM nginx:1.27-alpine
COPY web-02/frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /src/dist /usr/share/nginx/html
EXPOSE 80
