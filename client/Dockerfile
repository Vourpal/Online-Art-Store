FROM node:18-alpine

WORKDIR /./client

COPY . .
EXPOSE 3000

RUN npm install 

CMD ["npm", "run", "dev"]