FROM python:3.6
EXPOSE 5000
WORKDIR /python
RUN python -m pip install --upgrade pip
RUN pip install Flask
RUN echo "from flask import Flask \n\
app = Flask(__name__)             \n\
                                  \n\
@app.route('/')                   \n\
def hello():                      \n\
  name = \"Hello World\"          \n\
  return name                     \n\
                                  \n\
if __name__ == \"__main__\":      \n\
  app.run(debug=False, host='0.0.0.0', port=80) \n\
" >> server.py
ENTRYPOINT python server.py
