FROM python:3.7.3 AS builder

WORKDIR /src/
COPY ./pyproject.toml ./poetry.lock /src/
RUN pip install poetry==0.12.11 && \
	poetry install

COPY . /src/
RUN poetry run black --check bitly && \
      poetry run pylint bitly
RUN poetry build
RUN pip install .

FROM python:3.7.3

COPY --from=builder /usr/local/bin/entrypoint /usr/local/bin/
COPY --from=builder /usr/local/lib /usr/local/lib
ENTRYPOINT ["entrypoint"]
