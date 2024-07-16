FROM continuumio/miniconda3

ARG VERSION
ARG HOST

RUN apt update -y && apt upgrade -y && apt clean
RUN apt install -y git

RUN mkdir -p /app/FlaskShowImg
WORKDIR /app/FlaskShowImg
RUN git clone --branch ${VERSION} https://github.com/YetAnotherGeorge/FlaskShowImg.git ./
RUN conda create --name FlaskShowImg --file ./requirements.conda.txt -y

RUN sed -i ./consts.py -E "s/^\s*WS_HOST.+?=\s*\"[^\"]+\"$/WS_HOST: str = \"${HOST}\"/gm"

# CMD conda run --no-capture-output -n FlaskShowImg waitress-serve --port=8020 --call 'flaskr:create_app'
CMD sleep infinity