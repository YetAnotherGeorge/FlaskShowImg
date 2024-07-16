FROM continuumio/miniconda3

RUN apt update -y && apt upgrade -y && apt clean
RUN apt install -y git

RUN mkdir -p /app/FlaskShowImg
WORKDIR /app/FlaskShowImg
RUN git clone --branch ${VERSION} https://github.com/YetAnotherGeorge/FlaskShowImg.git ./
RUN conda create --name FlaskShowImg --file ./requirements.conda.txt -y

CMD conda run --no-capture-output -n FlaskShowImg waitress-serve --port=8020 --call 'flaskr:create_app'