FROM python:3.13-slim-bookworm
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates
ADD https://astral.sh/uv/install.sh /uv-installer.sh
RUN sh /uv-installer.sh && rm /uv-installer.sh

ENV PATH="/root/.local/bin/:$PATH"

ADD . /app
WORKDIR /app

RUN uv sync --frozen
VOLUME /app/data
ENTRYPOINT ["uv", "run", "mail2cospend"]
CMD ["run"]

