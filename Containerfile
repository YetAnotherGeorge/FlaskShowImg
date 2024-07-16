FROM conda/miniconda3
LABEL name="FlaskShowImg"
COPY . /FlaskShowImg
RUN conda --name FlaskShowImg python=${PYTHON_VERSION} --file /FlaskShowImg/requirements.conda.txt

WORKDIR /FlaskShowImg
CMD conda run --no-capture-output -n FlaskShowImg waitress-serve --port=8020 --call 'flaskr:create_app'