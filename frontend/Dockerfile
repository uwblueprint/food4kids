FROM node:24.13.0

WORKDIR /app

COPY package.json yarn.lock ./
RUN npm install

COPY . ./

EXPOSE 3000
ENTRYPOINT ["npm", "dev"]