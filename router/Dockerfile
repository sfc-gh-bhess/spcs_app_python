FROM nginx:alpine
 
RUN apk update && apk add bash

EXPOSE 80

WORKDIR /app

COPY src/. .

RUN chmod +x ./entrypoint.sh

ENTRYPOINT [ "./entrypoint.sh" ]