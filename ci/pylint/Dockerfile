FROM python:3.7.3

WORKDIR /src/
COPY ./pyproject.toml ./poetry.lock /src/
RUN pip install poetry==0.12.11 && \
	poetry install

COPY ./ci/pylint/entrypoint.sh /
ENTRYPOINT ["/entrypoint.sh"]
